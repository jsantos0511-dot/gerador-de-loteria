import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd
import requests
from supabase import create_client, Client

# --- CONFIGURAÇÕES DO BANCO DE DADOS (SUPABASE) ---
# Substitua pelos dados do seu projeto no Supabase
SUPABASE_URL = "SUA_URL_AQUI"
SUPABASE_KEY = "SUA_KEY_ANON_AQUI"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0, "api": "megasena", "garantias": ["Quadra", "Quina"]},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0, "api": "lotofacil", "garantias": ["11 Pontos", "12 Pontos"]},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5, "api": "quina", "garantias": ["Terno", "Quadra"]},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0, "api": "lotomania", "garantias": ["16 Pontos", "17 Pontos"]},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5, "api": "duplasena", "garantias": ["Quadra", "Quina"]}
}

# --- FUNÇÕES AUXILIARES ---
def buscar_resultado_api(loteria_slug):
    try:
        response = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{loteria_slug}/latest", timeout=10)
        return response.json() if response.status_code == 200 else None
    except: return None

def aplicar_filtros(combos, f_seq, f_fin, f_par, max_p, dez_jogo, limite, tudo):
    res = []
    for c in combos:
        j = list(c)
        if f_seq and any(j[i+1] == j[i]+1 for i in range(len(j)-1)): continue
        if f_fin and any([n % 10 for n in j].count(f) > 4 for f in [n % 10 for n in j]): continue
        if f_par:
            p = len([n for n in j if n % 2 == 0])
            if p > max_p or (dez_jogo - p) > max_p: continue
        res.append(j)
        if not tudo and len(res) >= limite: break
    return res

# --- ESTILIZAÇÃO CSS ---
params = st.query_params
st.session_state.pagina = params.get("escolha", "Início")
p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    .card-container {{
        border: 2px solid var(--cor-loteria); border-radius: 12px; padding: 12px 8px;
        text-align: center; background-color: #161b22; transition: all 0.2s;
        cursor: pointer; text-decoration: none !important; display: block; margin-bottom: 12px;
    }}
    .card-container:hover {{ transform: scale(1.02); box-shadow: 0 0 15px var(--cor-loteria); }}
    .card-title {{ font-size: 17px; font-weight: bold; color: var(--cor-loteria); }}
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{ display: grid !important; grid-template-columns: repeat({cols_v}, 1fr) !important; gap: 3px !important; }}
    [data-testid="stSidebar"] {{ display: none; }}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- TELAS ---
def home():
    st.markdown('<h2 style="text-align:center; margin-bottom:25px;">🍀 Portal Loterias Pro</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        card_html = f'<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados["cor"]};"><div style="font-size:22px;">🍀</div><div class="card-title">{nome}</div></a>'
        alvo.markdown(card_html, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📂 Meus Jogos Salvos (Nuvem)")
    if supabase:
        try:
            res_db = supabase.table("meus_jogos").select("*").order("created_at", desc=True).limit(5).execute()
            for item in res_db.data:
                with st.expander(f"📌 {item['loteria']} - {item['created_at'][:10]}"):
                    st.write(f"Ref: {item['concurso']}")
                    st.dataframe(pd.DataFrame(item['dezenas']), use_container_width=True)
        except: st.info("Conecte o Supabase para ver seus jogos aqui.")

def gerador_loteria(nome, config):
    c_v, c_t = st.columns([1, 4])
    with c_v:
        if st.button("⬅️ Sair"):
            st.query_params.clear()
            st.session_state.pagina = "Início"
            st.rerun()
    with c_t: st.markdown(f'<h3 style="color:{config["cor"]}; margin:0;">🍀 {nome}</h3>', unsafe_allow_html=True)

    aba_gerar, aba_fechamento, aba_estatisticas, aba_conferir = st.tabs(["🚀 Gerador", "🛡️ Fechamentos", "📊 Estatísticas", "🎯 Conferidor"])

    with aba_gerar:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎲 Surpresinha", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
        with c2:
            if st.button("❌ Limpar", use_container_width=True):
                st.session_state[f"sel_{nome}"] = []
                st.rerun()

        selecionados = st.segmented_control("V", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a: dez_por_jogo = st.number_input("Dezenas", config['min_sel'], config['total'], config['min_sel'])
        with col_b: valor_unit = st.number_input("Preço R$", 0.0, 5000.0, config['preco'])
        with col_c: 
            gerar_tudo = st.checkbox("Gerar Todos")
            qtd_max = st.number_input("Limite", 1, 1000000, 100, disabled=gerar_tudo)

        with st.expander("🛠️ Filtros Inteligentes", expanded=False):
            f_s = st.checkbox("🚫 Sem sequências")
            f_f = st.checkbox("🚫 Limitar finais iguais (máx 4)")
            f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
            m_p = st.slider("Máx. Pares", 0, dez_por_jogo, dez_por_jogo // 2) if f_p else dez_por_jogo

        if st.button(f"🚀 GERAR JOGOS", type="primary", use_container_width=True):
            if len(selecionados) < dez_por_jogo: st.error(f"Selecione no mínimo {dez_por_jogo} números!")
            else:
                lista_n = sorted([int(x) for x in selecionados])
                res = aplicar_filtros(combinations(lista_n, dez_por_jogo), f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                st.session_state[f"ultimos_jogos_{nome}"] = res 
                if res:
                    st.success(f"{len(res)} jogos!")
                    st.dataframe(pd.DataFrame(res, columns=[f"B{i+1}" for i in range(dez_por_jogo)]), use_container_width=True)
                    
                    if supabase:
                        if st.button("💾 Salvar esta lista na Nuvem"):
                            supabase.table("meus_jogos").insert({"loteria": nome, "concurso": "Gerado Manual", "dezenas": res}).execute()
                            st.toast("Salvo na Nuvem!")

    with aba_fechamento:
        st.subheader("🛡️ Fechamentos")
        if len(selecionados) >= config['min_sel'] + 2:
            tipo_f = st.selectbox("Garantia:", config['garantias'])
            if st.button("🚀 Gerar Fechamento", use_container_width=True):
                combos = list(combinations(sorted([int(x) for x in selecionados]), config['min_sel']))
                res_f = combos[::4]
                st.session_state[f"ultimos_jogos_{nome}"] = res_f
                st.success(f"Fechamento: {len(res_f)} jogos.")
                st.dataframe(pd.DataFrame(res_f), use_container_width=True)
        else: st.warning("Selecione mais números.")

    with aba_estatisticas:
        if selecionados:
            st.subheader("📊 Estatísticas da Seleção")
            nums_int = [int(n) for n in selecionados]
            st.bar_chart(pd.Series([n % 10 for n in nums_int]).value_counts().sort_index(), color=config['cor'])

    with aba_conferir:
        st.subheader("🎯 Conferidor Oficial")
        if st.button("🔄 Buscar Último Sorteio Real", use_container_width=True):
            dados = buscar_resultado_api(config['api'])
            if dados:
                st.session_state[f"res_oficial_{nome}"] = dados['dezenas']
                st.info(f"Concurso {dados['concurso']} ({dados['data']})")
        
        res_oficial = st.session_state.get(f"res_oficial_{nome}", [])
        txt_res = st.text_input("Dezenas para conferência", value=", ".join(res_oficial))
        
        if txt_res and f"ultimos_jogos_{nome}" in st.session_state:
            sorteados = [int(n) for n in txt_res.replace(',', ' ').split() if n.strip().isdigit()]
            jogos = st.session_state[f"ultimos_jogos_{nome}"]
            res_conf = [list(j) + [len(set(j).intersection(set(sorteados)))] for j in jogos]
            df_conf = pd.DataFrame(res_conf, columns=[f"D{i+1}" for i in range(len(jogos[0]))] + ["✅ Acertos"])
            st.dataframe(df_conf.sort_values("✅ Acertos", ascending=False), use_container_width=True)

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
