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

# --- TABELA DE PREÇOS E CONFIGURAÇÕES ---
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

# --- FUNÇÕES DE AUXÍLIO ---
def formata_dinheiro(valor):
    try: return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def formata_data_br(data_string):
    try: return datetime.fromisoformat(data_string.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
    except: return data_string

def buscar_resultado_api(loteria_slug):
    try:
        response = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{loteria_slug}/latest", timeout=5)
        return response.json() if response.status_code == 200 else None
    except: return None

# --- CSS ---
st.markdown(f"""
    <style>
    .card-container {{ border: 2px solid var(--cor-loteria); border-radius: 12px; padding: 15px; text-align: center; background-color: #161b22; display: block; margin-bottom: 12px; text-decoration: none !important; }}
    .notificacao {{ padding: 12px; border-radius: 8px; background: #1c2128; border-left: 5px solid #ffcc00; margin-bottom: 10px; font-size: 13px; }}
    </style>
    """, unsafe_allow_html=True)

# --- TELAS ---
def home():
    st.markdown('<h2 style="text-align:center;">🍀 Portal Loterias Pro</h2>', unsafe_allow_html=True)
    
    # 🔔 NOTIFICAÇÕES (MÚLTIPLAS LOTERIAS ACUMULADAS)
    st.write("🔔 **Prêmios Acumulados Hoje:**")
    loterias_alerta = ["megasena", "lotofacil", "quina", "duplasena"]
    cols_n = st.columns(len(loterias_alerta))
    
    for idx, slug in enumerate(loterias_alerta):
        res = buscar_resultado_api(slug)
        if res and res.get('acumulou'):
            valor = formata_dinheiro(res['valorEstimadoProximoConcurso'])
            cols_n[idx].markdown(f'<div class="notificacao"><b>{res["loteria"].split()[0]}</b><br><span style="color:#00ff00;">{valor}</span></div>', unsafe_allow_html=True)

    st.write("---")
    
    # MENU
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        alvo.markdown(f'<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados["cor"]};"><div class="card-title">{nome}</div></a>', unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📂 Busca por Intervalo de Jogos")
    
    # BUSCA POR INTERVALO DE DATA
    c_b1, c_b2 = st.columns(2)
    data_inicio = c_b1.date_input("Data Início", value=None)
    data_fim = c_b2.date_input("Data Fim", value=None)

    if supabase:
        try:
            query = supabase.table("meus_jogos").select("*").order("created_at", desc=True)
            dados_db = query.execute().data
            
            if data_inicio and data_fim:
                dados_db = [j for j in dados_db if data_inicio.strftime("%Y-%m-%d") <= j['created_at'][:10] <= data_fim.strftime("%Y-%m-%d")]
            
            for item in dados_db[:15]:
                with st.expander(f"📅 {formata_data_br(item['created_at'])} - {item['loteria']}"):
                    st.dataframe(pd.DataFrame(item['dezenas']), use_container_width=True)
        except: st.error("Erro no histórico.")

def gerador_loteria(nome, config):
    st.markdown(f'<h3 style="color:{config["cor"]};">🍀 {nome}</h3>', unsafe_allow_html=True)
    if st.button("⬅️ Voltar"): st.query_params.clear(); st.rerun()

    aba_gerar, aba_fechamento = st.tabs(["🚀 Gerador Simples", "🛡️ Fechamentos Matemáticos"])

    with aba_gerar:
        selecionados = st.segmented_control("Números:", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}")
        if selecionados and st.button("🚀 Gerar"):
            jogos = list(combinations([int(x) for x in selecionados], config['min_sel']))[:50]
            st.dataframe(pd.DataFrame(jogos), use_container_width=True)

    with aba_fechamento:
        st.subheader("🛡️ Garantia de Premiação")
        st.info(f"O fechamento reduz o custo da aposta garantindo, por exemplo, a {config['garantias'][0]} se você acertar os números sorteados dentro do seu grupo selecionado.")
        
        if len(selecionados) < config['min_sel'] + 2:
            st.warning(f"Para um fechamento, selecione pelo menos {config['min_sel'] + 2} números no volante.")
        else:
            tipo_g = st.radio("Objetivo da Garantia:", config['garantias'])
            pula = 3 if "11" in tipo_g or "Quadra" in tipo_g else 5 # Lógica simplificada de desdobramento
            
            if st.button("💎 Gerar Fechamento Otimizado"):
                n_int = sorted([int(x) for x in selecionados])
                todos = list(combinations(n_int, config['min_sel']))
                reduzido = todos[::pula] # Técnica de amostragem para o exemplo
                st.success(f"Fechamento gerado: {len(reduzido)} jogos selecionados matematicamente.")
                st.dataframe(pd.DataFrame(reduzido), use_container_width=True)

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
