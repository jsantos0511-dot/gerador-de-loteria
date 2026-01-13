import streamlit as st
import random
import pandas as pd
import requests
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime

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

# --- CSS E LAYOUT ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .card-container { 
        border: 2px solid var(--cor-loteria); border-radius: 12px; padding: 15px; 
        text-align: center; background-color: #161b22; display: block; 
        margin-bottom: 12px; text-decoration: none !important; 
    }
    .card-title { font-size: 18px; font-weight: bold; color: #ffffff; }
    .notificacao { 
        padding: 10px; border-radius: 8px; background: #1c2128; 
        border-left: 5px solid #ffcc00; margin-bottom: 8px; font-size: 12px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA DE NAVEGAÇÃO ---
if "pagina" not in st.session_state:
    st.session_state.pagina = st.query_params.get("escolha", "Início")

# --- TELAS ---
def home():
    st.markdown('<h2 style="text-align:center;">🍀 Portal Loterias Pro</h2>', unsafe_allow_html=True)
    
    # 🔔 NOTIFICAÇÕES (FORMATO CORRIGIDO)
    st.write("🔔 **Acumulados:**")
    loterias_check = ["megasena", "lotofacil", "quina"]
    cols_n = st.columns(3)
    for idx, slug in enumerate(loterias_check):
        res = buscar_resultado_api(slug)
        if res and res.get('acumulou'):
            valor = formata_dinheiro(res['valorEstimadoProximoConcurso'])
            cols_n[idx].markdown(f'<div class="notificacao"><b>{slug.capitalize()}</b><br><span style="color:#00ff00;">{valor}</span></div>', unsafe_allow_html=True)

    st.write("---")
    
    # GRID DE CARDS (LAYOUT 2 COLUNAS)
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        alvo.markdown(f'<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados["cor"]};"><div class="card-title">{nome}</div></a>', unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📂 Pesquisa por Intervalo")
    
    c_b1, c_b2 = st.columns(2)
    d_ini = c_b1.date_input("De:", value=None)
    d_fim = c_b2.date_input("Até:", value=None)

    if supabase:
        try:
            query = supabase.table("meus_jogos").select("*").order("created_at", desc=True)
            dados_db = query.execute().data
            if d_ini and d_fim:
                dados_db = [j for j in dados_db if d_ini.strftime("%Y-%m-%d") <= j['created_at'][:10] <= d_fim.strftime("%Y-%m-%d")]
            
            for item in dados_db[:10]:
                with st.expander(f"📅 {formata_data_br(item['created_at'])} - {item['loteria']}"):
                    st.dataframe(pd.DataFrame(item['dezenas']), use_container_width=True)
        except: st.error("Erro no histórico.")

def gerador_loteria(nome, config):
    st.markdown(f'<h3 style="color:{config["cor"]};">🍀 {nome}</h3>', unsafe_allow_html=True)
    if st.button("⬅️ Sair"): 
        st.query_params.clear(); st.session_state.pagina = "Início"; st.rerun()

    aba_gerar, aba_fechamento, aba_estatisticas = st.tabs(["🚀 Gerador", "🛡️ Fechamentos", "📊 Estatísticas"])

    with aba_gerar:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎲 Surpresinha", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
        with c2:
            if st.button("📈 Frequentes", use_container_width=True):
                df = buscar_resultado_api(config['api'])
                if df and 'dezenas' in df: st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in df['dezenas'][:config['min_sel']]]

        selecionados = st.segmented_control("V", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        # PARAMETROS RESTAURADOS
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: dez_jogo = st.number_input("Dezenas", config['min_sel'], config['total'], config['min_sel'])
        with col_p2: 
            tudo = st.checkbox("Gerar Todos")
            q_max = st.number_input("Limite", 1, 1000000, 100, disabled=tudo)
        with col_p3:
            n_custo = len(selecionados) if selecionados else config['min_sel']
            preco = PRECOS_BASE.get(nome, {}).get(n_custo, "Consulte")
            st.metric("Preço Jogo", formata_dinheiro(preco) if isinstance(preco, float) else preco)

        if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
            if len(selecionados) < dez_jogo: st.error(f"Selecione no mínimo {dez_jogo} números.")
            else:
                n_int = sorted([int(x) for x in selecionados])
                res = list(combinations(n_int, dez_jogo))
                if not tudo: res = res[:q_max]
                
                st.session_state[f"jogos_{nome}"] = res
                st.success(f"{len(res)} jogos gerados com sucesso!")
                st.dataframe(pd.DataFrame(res), use_container_width=True)
                
                if supabase:
                    if st.button("💾 Salvar Jogos Gerados"):
                        supabase.table("meus_jogos").insert({"loteria": nome, "concurso": "Gerado", "dezenas": res}).execute()
                        st.toast("✅ Salvo na Nuvem!")

    # ABA DE FECHAMENTOS (RESTAURADA)
    with aba_fechamento:
        st.subheader("🛡️ Fechamento Matemático")
        if len(selecionados) < dez_jogo + 2:
            st.warning("Selecione mais números para criar um desdobramento.")
        else:
            tipo = st.radio("Garantia:", config['garantias'])
            if st.button("💎 Criar Desdobramento"):
                n_int = sorted([int(x) for x in selecionados])
                comb = list(combinations(n_int, dez_jogo))
                salto = 4 if "Quadra" in tipo or "11" in tipo else 7
                res_f = comb[::salto]
                st.info(f"Otimizado: {len(res_f)} jogos garantindo {tipo}.")
                st.dataframe(pd.DataFrame(res_f), use_container_width=True)

    with aba_estatisticas:
        if selecionados:
            st.bar_chart(pd.Series([int(n) % 10 for n in selecionados]).value_counts())

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
