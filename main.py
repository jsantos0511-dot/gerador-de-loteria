import streamlit as st
import random
import pandas as pd
import requests
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DO BANCO DE DADOS ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = get_supabase()

# --- TABELAS E CONFIGURAÇÕES ---
PRECOS_BASE = {
    "Mega-Sena": {6: 6.0, 7: 42.0, 8: 168.0, 9: 504.0, 10: 1260.0},
    "Lotofácil": {15: 3.5, 16: 56.0, 17: 476.0, 18: 2856.0, 19: 13566.0, 20: 54264.0},
    "Quina": {5: 3.0, 6: 18.0, 7: 63.0, 8: 168.0, 9: 378.0, 10: 756.0},
    "Lotomania": {50: 3.0},
    "Dupla Sena": {6: 3.0, 7: 21.0, 8: 84.0, 9: 252.0, 10: 630.0}
}

TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "api": "megasena", "garantias": ["Quadra", "Quina"]},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "api": "lotofacil", "garantias": ["11 Pontos", "12 Pontos"]},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "api": "quina", "garantias": ["Terno", "Quadra"]},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "api": "lotomania", "garantias": ["16 Pontos", "17 Pontos"]},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "api": "duplasena", "garantias": ["Quadra", "Quina"]}
}

# --- FUNÇÕES DE APOIO ---
def formata_dinheiro(valor):
    try: return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def formata_data_br(data_string):
    try: return datetime.fromisoformat(data_string.split('.')[0].replace('Z', '')).strftime("%d/%m/%Y %H:%M")
    except: return data_string

def buscar_resultado_api(loteria_slug):
    try:
        response = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{loteria_slug}/latest", timeout=5)
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

# --- ESTILIZAÇÃO CSS (NEON + AJUSTES) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Título aumentado em 15% */
    .main-title { 
        text-align: center; 
        font-size: 1.75rem; 
        font-weight: bold; 
        margin-bottom: 1.5rem;
        color: #ffffff;
    }
    
    .card-link { text-decoration: none !important; color: white !important; }
    
    /* Menus com altura +15% e Efeito Neon */
    .card-container { 
        border: 2px solid var(--cor-loteria); 
        border-radius: 10px; 
        padding: 25px; 
        text-align: center; 
        background-color: #161b22; 
        margin-bottom: 15px; 
        cursor: pointer; 
        display: block;
        transition: 0.4s ease;
    }
    
    .card-container:hover { 
        background-color: #1c2128;
        box-shadow: 0 0 15px var(--cor-loteria), 0 0 5px var(--cor-loteria) inset;
        transform: scale(1.02);
    }
    
    .notificacao { 
        padding: 8px; 
        border-radius: 6px; 
        background: #1c2128; 
        border-left: 4px solid #ffcc00; 
        margin-bottom: 5px; 
        font-size: 0.75rem; 
    }
    
    .resultado-bola {
        display: inline-block; width: 32px; height: 32px; line-height: 32px;
        background-color: #209869; color: white; border-radius: 50%;
        text-align: center; margin: 2px; font-weight: bold; font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
params = st.query_params
st.session_state.pagina = params.get("escolha", "Início")

# --- TELAS ---
def home():
    st.markdown('<div class="main-title">🍀 Gerador de Jogos</div>', unsafe_allow_html=True)
    
    st.write("🔔 **Acumulados:**")
    loterias_check = ["megasena", "lotofacil", "quina", "duplasena"]
    cols_n = st.columns(len(loterias_check))
    for idx, slug in enumerate(loterias_check):
        res = buscar_resultado_api(slug)
        if res and res.get('acumulou'):
            valor = formata_dinheiro(res['valorEstimadoProximoConcurso'])
            cols_n[idx].markdown(f'<div class="notificacao"><b>{slug.capitalize()}</b><br><span style="color:#00ff00;">{valor}</span></div>', unsafe_allow_html=True)

    st.write("---")
    
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        alvo.markdown(f'<a href="/?escolha={nome}" target="_self" class="card-link"><div class="card-container" style="--cor-loteria: {dados["cor"]};"><b style="font-size:18px;">{nome}</b></div></a>', unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📂 Histórico de Jogos (Últimos 15 dias)")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Filtrar de:", value=None)
    d_fim = c2.date_input("Filtrar até:", value=None)

    if supabase:
        try:
            query = supabase.table("meus_jogos").select("*").order("created_at", desc=True)
            dados_db = query.execute().data
            
            # Lógica de exibição: Se houver filtro manual usa ele, senão usa últimos 15 dias
            if d_ini and d_fim:
                dados_db = [j for j in dados_db if d_ini.strftime("%Y-%m-%d") <= j['created_at'][:10] <= d_fim.strftime("%Y-%m-%d")]
            else:
                limite_15_dias = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
                dados_db = [j for j in dados_db if j['created_at'][:10] >= limite_15_dias]

            if not dados_db:
                st.info("Nenhum jogo encontrado no período.")
            else:
                for item in dados_db:
                    with st.expander(f"📅 {formata_data_br(item['created_at'])} - {item['loteria']}"):
                        st.dataframe(pd.DataFrame(item['dezenas']), use_container_width=True)
        except: st.error("Erro ao carregar banco de dados.")

def gerador_loteria(nome, config):
    st.markdown(f'<h3 style="color:{config["cor"]}; text-align:center;">🍀 {nome}</h3>', unsafe_allow_html=True)
    if st.button("⬅️ Sair"): st.query_params.clear(); st.rerun()

    aba_gerar, aba_fechamento, aba_conferir = st.tabs(["🚀 Gerador", "🛡️ Fechamentos", "✅ Conferir"])

    with aba_gerar:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🎲 Surpresa", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
        with c2:
            if st.button("📈 Frequentes", use_container_width=True):
                df = buscar_resultado_api(config['api'])
                if df and 'dezenas' in df: st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in df['dezenas'][:config['min_sel']]]
        with c3:
            if st.button("🗑️ Limpar", use_container_width=True):
                st.session_state[f"sel_{nome}"] = []; st.rerun()

        selecionados = st.segmented_control("Números:", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: dez_jogo = st.number_input("Dezenas", config['min_sel'], config['total'], config['min_sel'])
        with col_p2: 
            tudo = st.checkbox("Gerar Todas")
            q_max = st.number_input("Limite", 1, 1000000, 100, disabled=tudo)
        with col_p3:
            n_atual = len(selecionados) if selecionados else config['min_sel']
            preco = PRECOS_BASE.get(nome, {}).get(n_atual, "Consulte")
            st.metric("Custo", formata_dinheiro(preco) if isinstance(preco, float) else preco)

        with st.expander("🛠️ Filtros Inteligentes"):
            f_s = st.checkbox("Sem sequências")
            f_f = st.checkbox("Limitar finais")
            f_p = st.checkbox("Par/Ímpar")
            m_p = st.slider("Máx Pares", 0, dez_jogo, dez_jogo // 2) if f_p else dez_jogo

        if st.button("🚀 GERAR E SALVAR", type="primary", use_container_width=True):
            if len(selecionados) < dez_jogo: st.error("Selecione mais números.")
            else:
                res = aplicar_filtros(combinations(sorted([int(x) for x in selecionados]), dez_jogo), f_s, f_f, f_p, m_p, dez_jogo, q_max, tudo)
                st.success(f"{len(res)} jogos gerados!")
                st.dataframe(pd.DataFrame(res), use_container_width=True)
                if supabase and len(res) > 0:
                    supabase.table("meus_jogos").insert({"loteria": nome, "concurso": "Manual", "dezenas": res}).execute()
                    st.toast("✅ Salvo no histórico!")

    with aba_fechamento:
        st.subheader("🛡️ Fechamento Matemático")
        tipo = st.radio("Objetivo:", config['garantias'])
        if st.button("💎 Gerar"):
            comb = list(combinations(sorted([int(x) for x in selecionados]), dez_jogo))
            res_f = comb[::5]
            st.dataframe(pd.DataFrame(res_f), use_container_width=True)

    with aba_conferir:
        st.subheader("✅ Conferência Inteligente (7 dias)")
        res_oficial = buscar_resultado_api(config['api'])
        if res_oficial:
            dt_sorteio = datetime.strptime(res_oficial['data'], "%d/%m/%Y").date()
            st.info(f"Último Concurso: **{res_oficial['concurso']}** ({res_oficial['data']})")
            
            html_bolas = "".join([f'<div class="resultado-bola" style="background-color:{config["cor"]}">{n:02d}</div>' for n in [int(n) for n in res_oficial['dezenas']]])
            st.markdown(html_bolas, unsafe_allow_html=True)

            if supabase:
                dt_limite_inf = (dt_sorteio - timedelta(days=7)).strftime("%Y-%m-%d")
                dt_limite_sup = dt_sorteio.strftime("%Y-%m-%d")
                
                jogos_db = supabase.table("meus_jogos").select("*").eq("loteria", nome).execute().data
                jogos_validos = [j for j in jogos_db if dt_limite_inf <= j['created_at'][:10] <= dt_limite_sup]

                if jogos_validos:
                    oficiais = [int(n) for n in res_oficial['dezenas']]
                    for bloco in jogos_validos:
                        with st.expander(f"Jogos salvos em: {formata_data_br(bloco['created_at'])}"):
                            results = []
                            for j in bloco['dezenas']:
                                acertos = len(set(j) & set(oficiais))
                                results.append({"Jogo": j, "Acertos": acertos})
                            st.dataframe(pd.DataFrame(results).sort_values("Acertos", ascending=False), use_container_width=True)
                else:
                    st.warning("Sem jogos salvos próximos a esta data.")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
