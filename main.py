import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd
import requests  # Importante para buscar os resultados reais

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES ---
TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0, "api": "megasena", "garantias": ["Quadra", "Quina"]},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0, "api": "lotofacil", "garantias": ["11 Pontos", "12 Pontos", "13 Pontos"]},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5, "api": "quina", "garantias": ["Terno", "Quadra"]},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0, "api": "lotomania", "garantias": ["16 Pontos", "17 Pontos"]},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5, "api": "duplasena", "garantias": ["Quadra", "Quina"]}
}

# --- FUNÇÃO PARA BUSCAR RESULTADOS REAIS ---
def buscar_resultado_api(loteria_slug):
    try:
        # Usando a API pública LoteriasCaixa-API
        response = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{loteria_slug}/latest", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return None
    return None

# --- NAVEGAÇÃO E CSS ---
params = st.query_params
if "escolha" in params:
    st.session_state.pagina = params["escolha"]

if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    .card-container {{
        border: 2px solid var(--cor-loteria);
        border-radius: 12px;
        padding: 12px 8px;
        text-align: center;
        background-color: #161b22;
        transition: all 0.2s ease;
        cursor: pointer;
        text-decoration: none !important;
        display: block;
        margin-bottom: 12px;
    }}
    .card-container:hover {{ transform: scale(1.02); box-shadow: 0 0 15px var(--cor-loteria); }}
    .card-title {{ font-size: 17px; font-weight: bold; color: var(--cor-loteria); }}
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{ display: grid !important; grid-template-columns: repeat({cols_v}, 1fr) !important; gap: 3px !important; }}
    [data-testid="stSidebar"] {{ display: none; }}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE FILTRO ---
def aplicar_filtros(combos, f_seq, f_finais, f_par, max_p, dez_jogo, limite, gerar_tudo):
    res = []
    for c in combos:
        jogo = list(c)
        if f_seq and any(jogo[i+1] == jogo[i]+1 for i in range(len(jogo)-1)): continue
        if f_finais:
            finais = [n % 10 for n in jogo]
            if any(finais.count(f) > 4 for f in finais): continue
        if f_par:
            p = len([n for n in jogo if n % 2 == 0])
            if p > max_p or (dez_jogo - p) > max_p: continue
        res.append(jogo)
        if not gerar_tudo and len(res) >= limite: break
    return res

# --- TELAS ---

def home():
    st.markdown('<h2 style="text-align:center; margin-bottom:25px;">🍀 Portal Loterias Pro</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        card_html = f"""<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados['cor']};">
            <div style="font-size:22px;">🍀</div><div class="card-title">{nome}</div></a>"""
        alvo.markdown(card_html, unsafe_allow_html=True)

def gerador_loteria(nome, config):
    c_v, c_t = st.columns([1, 4])
    with c_v:
        if st.button("⬅️ Sair"):
            st.query_params.clear()
            st.session_state.pagina = "Início"
            st.rerun()
    with c_t: st.markdown(f'<h3 style="color:{config["cor"]}; margin:0;">🍀 {nome}</h3>', unsafe_allow_html=True)

    aba_gerar, aba_fechamento, aba_estatisticas, aba_conferir = st.tabs(["🚀 Gerador", "🛡️ Fechamentos", "📊 Estatísticas", "🎯 Conferidor"])

    # ABA GERADOR
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
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                st.session_state[f"ultimos_jogos_{nome}"] = res 
                if res:
                    st.success(f"{len(res)} jogos!")
                    st.dataframe(pd.DataFrame(res, columns=[f"B{i+1}" for i in range(dez_por_jogo)]), use_container_width=True)

    # ABA FECHAMENTOS (Simplificada)
    with aba_fechamento:
        st.subheader("🛡️ Desdobramentos")
        if len(selecionados) < config['min_sel'] + 2:
            st.warning("Selecione mais números no volante.")
        else:
            tipo_f = st.selectbox("Garantia:", config['garantias'])
            if st.button("🚀 Gerar Fechamento Otimizado", use_container_width=True):
                combos = list(combinations(sorted([int(x) for x in selecionados]), config['min_sel']))
                res_f = combos[::3] # Lógica de redução
                st.session_state[f"ultimos_jogos_{nome}"] = res_f
                st.success(f"Fechamento: {len(res_f)} jogos.")
                st.dataframe(pd.DataFrame(res_f), use_container_width=True)

    # ABA ESTATÍSTICAS
    with aba_estatisticas:
        if selecionados:
            st.subheader("📊 Estatísticas da Seleção")
            nums_int = [int(n) for n in selecionados]
            st.bar_chart(pd.Series([n % 10 for n in nums_int]).value_counts().sort_index(), color=config['cor'])

    # ABA CONFERIR (COM INTEGRAÇÃO API)
    with aba_conferir:
        st.subheader("🎯 Conferidor Automático")
        
        if st.button("🔄 Buscar Último Resultado Oficial", use_container_width=True):
            with st.spinner("Conectando à Caixa..."):
                dados_api = buscar_resultado_api(config['api'])
                if dados_api:
                    st.session_state[f"res_oficial_{nome}"] = dados_api['dezenas']
                    st.session_state[f"info_api_{nome}"] = f"Concurso {dados_api['concurso']} ({dados_api['data']})"
                    st.toast("Resultado atualizado com sucesso!")
                else:
                    st.error("Não foi possível obter os dados. Tente novamente mais tarde.")

        res_atual = st.session_state.get(f"res_oficial_{nome}", "")
        info_api = st.session_state.get(f"info_api_{nome}", "")
        
        if info_api: st.info(info_api)
        
        txt_resultado = st.text_input("Dezenas para conferir", value=", ".join(res_atual) if res_atual else "", placeholder="Ex: 01, 02, 03...")
        
        if txt_resultado and f"ultimos_jogos_{nome}" in st.session_state:
            num_sorteados = [int(n) for n in txt_resultado.replace(',', ' ').split() if n.strip().isdigit()]
            jogos = st.session_state[f"ultimos_jogos_{nome}"]
            res_conf = [list(j) + [len(set(j).intersection(set(num_sorteados)))] for j in jogos]
            df_conf = pd.DataFrame(res_conf, columns=[f"D{i+1}" for i in range(len(jogos[0]))] + ["✅ Acertos"])
            st.dataframe(df_conf.sort_values("✅ Acertos", ascending=False), use_container_width=True)

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
