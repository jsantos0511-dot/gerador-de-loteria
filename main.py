import streamlit as st
import random
import pandas as pd
import requests
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime

# --- CONFIGURAÇÕES DO BANCO DE DADOS (SUPABASE) ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

# --- TABELA DE PREÇOS ATUALIZADA (2025) ---
# Dicionário com multiplicadores de aposta para cálculo automático
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

# --- FUNÇÕES DE API ---
def buscar_resultado_api(loteria_slug):
    try:
        response = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{loteria_slug}/latest", timeout=10)
        return response.json() if response.status_code == 200 else None
    except: return None

# --- ESTILIZAÇÃO ---
params = st.query_params
st.session_state.pagina = params.get("escolha", "Início")
p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    .card-container {{
        border: 2px solid var(--cor-loteria); border-radius: 12px; padding: 15px 10px;
        text-align: center; background-color: #161b22; transition: all 0.2s;
        text-decoration: none !important; display: block; margin-bottom: 15px;
    }}
    .card-container:hover {{ transform: scale(1.03); box-shadow: 0 0 15px var(--cor-loteria); }}
    .card-title {{ font-size: 18px; font-weight: bold; color: #ffffff; margin-top: 5px; }}
    .notificacao {{
        padding: 10px; border-radius: 8px; background: #1e2329; border-left: 5px solid #ffcc00;
        margin-bottom: 10px; font-size: 14px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- TELA INICIAL ---
def home():
    st.markdown('<h2 style="text-align:center;">🍀 Portal Loterias Pro</h2>', unsafe_allow_html=True)
    
    # 🔔 SEÇÃO DE NOTIFICAÇÕES (Destaques de Prêmios)
    with st.container():
        st.write("🔔 **Destaques de Hoje:**")
        cols_notif = st.columns(3)
        for i, lot_name in enumerate(["Mega-Sena", "Lotofácil", "Quina"]):
            res = buscar_resultado_api(TEMAS[lot_name]['api'])
            if res and res.get('acumulou'):
                cols_notif[i].markdown(f"""<div class="notificacao"><b>{lot_name}</b><br>💰 Acumulada!<br>Est: {res['valorEstimadoProximoConcurso']}</div>""", unsafe_allow_html=True)

    st.write("---")
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        card_html = f"""<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados['cor']};">
            <div style="font-size:24px;">🍀</div><div class="card-title">{nome}</div></a>"""
        alvo.markdown(card_html, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📂 Meus Jogos Salvos")
    
    # 🔍 BUSCA POR DATA E NOME
    c_busca1, c_busca2 = st.columns([2, 1])
    data_filtro = c_busca1.date_input("Filtrar por data", value=None)
    lot_filtro = c_busca2.selectbox("Loteria", ["Todas"] + list(TEMAS.keys()))

    if supabase:
        try:
            query = supabase.table("meus_jogos").select("*").order("created_at", desc=True)
            if lot_filtro != "Todas": query = query.eq("loteria", lot_filtro)
            res_db = query.execute()
            
            jogos = res_db.data
            if data_filtro:
                jogos = [j for j in jogos if j['created_at'].startswith(str(data_filtro))]

            for item in jogos[:10]: # Mostra os 10 mais recentes da busca
                with st.expander(f"📌 {item['loteria']} - {item['created_at'][:10]}"):
                    st.caption(f"Ref: {item['concurso']}")
                    st.table(item['dezenas'])
        except: st.info("Conecte ao banco de dados para ver seu histórico completo.")

# --- TELA DO GERADOR ---
def gerador_loteria(nome, config):
    st.markdown(f'<h3 style="color:{config["cor"]};">🍀 {nome}</h3>', unsafe_allow_html=True)
    if st.button("⬅️ Voltar"): st.query_params.clear(); st.rerun()

    aba_gerar, aba_conferir = st.tabs(["🚀 Gerador & Filtros", "🎯 Conferidor"])

    with aba_gerar:
        # 📊 FILTRO DE NÚMEROS FREQUENTES
        if st.button("📈 Selecionar os Mais Frequentes (Último Sorteio)", use_container_width=True):
            dados_freq = buscar_resultado_api(config['api'])
            if dados_freq:
                st.session_state[f"sel_{nome}"] = [f"{n:02d}" for n in dados_freq['dezenas']]
                st.toast("Números do último sorteio selecionados!")

        selecionados = st.segmented_control("Selecione seus números:", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}")
        
        # 💰 CÁLCULO AUTOMÁTICO DE PREÇO
        num_escolhidos = len(selecionados) if selecionados else config['min_sel']
        preco_calc = PRECOS_BASE.get(nome, {}).get(num_escolhidos, "Sob consulta")
        
        col_a, col_b = st.columns(2)
        col_a.metric("Números Selecionados", num_escolhidos)
        col_b.metric("Preço da Aposta (R$)", f"{preco_calc}" if isinstance(preco_calc, float) else preco_calc)

        if st.button(f"🚀 GERAR JOGOS", type="primary", use_container_width=True):
            if len(selecionados) < config['min_sel']: st.error(f"Selecione no mínimo {config['min_sel']} números!")
            else:
                lista_n = sorted([int(x) for x in selecionados])
                res = list(combinations(lista_n, config['min_sel']))[:100] # Limite para não travar
                st.session_state[f"ultimos_jogos_{nome}"] = res 
                st.success(f"Gerado: {len(res)} jogos.")
                st.dataframe(pd.DataFrame(res), use_container_width=True)
                
                if supabase and st.button("💾 Salvar na Nuvem"):
                    supabase.table("meus_jogos").insert({"loteria": nome, "concurso": "Gerado Manual", "dezenas": res}).execute()
                    st.success("Salvo com sucesso!")

    with aba_conferir:
        if st.button("🔄 Buscar Resultado Oficial"):
            dados = buscar_resultado_api(config['api'])
            if dados: st.session_state[f"res_oficial_{nome}"] = dados['dezenas']; st.info(f"Concurso {dados['concurso']}")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
