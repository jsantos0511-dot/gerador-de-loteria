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
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase = get_supabase()

# --- TABELA DE PREÇOS (2026) ---
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

# --- FUNÇÕES DE FORMATAÇÃO ---
def formata_dinheiro(valor):
    try:
        f_val = float(valor)
        return f"R$ {f_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def formata_data_br(data_string):
    try:
        # Tenta formatar string vinda do Supabase (ISO) para BR
        dt = datetime.fromisoformat(data_string.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return data_string

# --- FUNÇÕES DE API ---
def buscar_resultado_api(loteria_slug):
    try:
        response = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{loteria_slug}/latest", timeout=5)
        return response.json() if response.status_code == 200 else None
    except: return None

# --- ESTILIZAÇÃO CSS ---
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
        text-decoration: none !important; display: block; margin-bottom: 12px;
    }}
    .card-container:hover {{ transform: scale(1.03); box-shadow: 0 0 15px var(--cor-loteria); }}
    .card-title {{ font-size: 18px; font-weight: bold; color: #ffffff; margin-top: 5px; }}
    .notificacao {{
        padding: 12px; border-radius: 8px; background: #1c2128; border-left: 5px solid #ffcc00;
        margin-bottom: 10px; font-size: 13px; color: #eeeeee;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- TELAS ---
def home():
    st.markdown('<h2 style="text-align:center;">🍀 Portal Loterias Pro</h2>', unsafe_allow_html=True)
    
    # 🔔 NOTIFICAÇÕES FORMATADAS
    st.write("🔔 **Destaques Acumulados:**")
    res_mega = buscar_resultado_api("megasena")
    res_loto = buscar_resultado_api("lotofacil")
    
    col_n1, col_n2 = st.columns(2)
    for col, res, nome in zip([col_n1, col_n2], [res_mega, res_loto], ["Mega-Sena", "Lotofácil"]):
        if res and res.get('acumulou'):
            valor = formata_dinheiro(res['valorEstimadoProximoConcurso'])
            col.markdown(f'<div class="notificacao"><b>{nome}</b><br><span style="color:#00ff00;">{valor}</span></div>', unsafe_allow_html=True)

    st.write("---")
    
    # MENU INICIAL
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        card_html = f"""<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados['cor']};">
            <div style="font-size:24px;">🍀</div><div class="card-title">{nome}</div></a><div style="margin-bottom:10px;"></div>"""
        alvo.markdown(card_html, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📂 Busca Histórica")
    
    c_b1, c_b2 = st.columns([2, 1])
    data_sel = c_b1.date_input("Filtrar por data", value=None)
    lot_sel = c_b2.selectbox("Loteria", ["Todas"] + list(TEMAS.keys()))

    if supabase:
        try:
            query = supabase.table("meus_jogos").select("*").order("created_at", desc=True)
            if lot_sel != "Todas": query = query.eq("loteria", lot_sel)
            dados_db = query.execute().data
            
            if data_sel:
                data_str = data_sel.strftime("%Y-%m-%d")
                dados_db = [j for j in dados_db if j['created_at'].startswith(data_str)]
            
            if not dados_db:
                st.info("Nenhum jogo encontrado para este filtro.")
            else:
                for item in dados_db[:10]:
                    dt_br = formata_data_br(item['created_at'])
                    with st.expander(f"📅 {dt_br} - {item['loteria']}"):
                        st.write(f"Concurso: {item['concurso']}")
                        st.dataframe(pd.DataFrame(item['dezenas']), use_container_width=True)
        except: st.error("Erro ao conectar com a nuvem.")

def gerador_loteria(nome, config):
    c_v, c_t = st.columns([1, 4])
    with c_v:
        if st.button("⬅️ Sair"): st.query_params.clear(); st.rerun()
    with c_t: st.markdown(f'<h3 style="color:{config["cor"]}; margin:0;">🍀 {nome}</h3>', unsafe_allow_html=True)

    aba_gerar, aba_conf = st.tabs(["🚀 Gerador", "🎯 Conferidor"])

    with aba_gerar:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎲 Surpresinha", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
        with c2:
            if st.button("📈 Mais Frequentes", use_container_width=True):
                dfreq = buscar_resultado_api(config['api'])
                # CORREÇÃO DO ERRO DA IMAGEM 2: Verificar se dezenas existem
                if dfreq and 'dezenas' in dfreq:
                    st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in dfreq['dezenas'][:config['min_sel']]]
                else:
                    st.warning("Não foi possível obter dados frequentes agora.")

        sel = st.segmented_control("V", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        n_at = len(sel) if sel else config['min_sel']
        preco = PRECOS_BASE.get(nome, {}).get(n_at, "Sob consulta")
        
        st.metric("Custo Estimado", formata_dinheiro(preco) if isinstance(preco, float) else preco)

        if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
            if len(sel) < config['min_sel']: st.error("Selecione mais números!")
            else:
                lista_n = sorted([int(x) for x in sel])
                jogos = list(combinations(lista_n, config['min_sel']))[:100]
                st.session_state[f"ult_{nome}"] = jogos
                st.dataframe(pd.DataFrame(jogos), use_container_width=True)
                
                if supabase:
                    if st.button("💾 Confirmar e Salvar"):
                        supabase.table("meus_jogos").insert({"loteria": nome, "concurso": "Manual", "dezenas": jogos}).execute()
                        st.toast("✅ Salvo!")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
