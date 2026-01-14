import streamlit as st
import random
import pandas as pd
import requests
import numpy as np
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime, timedelta

# Importação protegida para evitar erros de deploy
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- INICIALIZAÇÃO DE ESTADO ---
if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"

# Sincronização com Parâmetros de URL
if "escolha" in st.query_params:
    st.session_state.pagina = st.query_params["escolha"]

# --- CONEXÃO BANCO DE DADOS ---
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
    "Mega-Sena": {"cor": "#209869", "total": 60, "min_sel": 6, "api": "megasena"},
    "Lotofácil": {"cor": "#930089", "total": 25, "min_sel": 15, "api": "lotofacil"},
    "Quina": {"cor": "#260085", "total": 80, "min_sel": 5, "api": "quina"},
    "Lotomania": {"cor": "#f7941d", "total": 100, "min_sel": 50, "api": "lotomania"},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "min_sel": 6, "api": "duplasena"}
}

# --- FUNÇÕES AUXILIARES ---
def formata_dinheiro(valor):
    try: return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def formata_data_br(ds):
    try: return datetime.fromisoformat(ds.split('.')[0].replace('Z', '')).strftime("%d/%m/%Y %H:%M")
    except: return ds

@st.cache_data(ttl=3600)
def buscar_resultado_api(slug):
    try:
        r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest", timeout=5)
        return r.json() if r.status_code == 200 else None
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
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; font-size: 1.8rem; font-weight: bold; margin-bottom: 1rem; }
    .card-loteria { 
        border: 2px solid var(--c); border-radius: 10px; padding: 20px; 
        text-align: center; background: #161b22; cursor: pointer; margin-bottom: 10px;
    }
    .resultado-bola {
        display: inline-block; width: 32px; height: 32px; line-height: 32px;
        background-color: #209869; color: white; border-radius: 50%;
        text-align: center; margin: 3px; font-weight: bold;
    }
    .contador-status {
        background: #1c2128; padding: 10px; border-radius: 8px;
        border: 1px solid #58a6ff; color: #58a6ff; font-weight: bold;
        text-align: center; margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TELAS ---

def home():
    st.markdown('<div class="main-title">🍀 Gerador Profissional & Analytics</div>', unsafe_allow_html=True)
    
    # Alertas de Acumulados
    loterias_alerta = ["megasena", "lotofacil", "quina"]
    cols = st.columns(len(loterias_alerta))
    for i, slug in enumerate(loterias_alerta):
        res = buscar_resultado_api(slug)
        if res:
            estimada = res.get('valorEstimadoProximoConcurso', 0)
            cols[i].metric(slug.upper(), formata_dinheiro(estimada))

    st.write("---")
    col1, col2 = st.columns(2)
    for i, (nome, d) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        if alvo.button(f"➔ {nome}", use_container_width=True):
            st.query_params.escolha = nome
            st.session_state.pagina = nome
            st.rerun()

    st.write("---")
    t1, t2 = st.tabs(["📂 Histórico", "📊 Analytics"])
    with t1:
        if supabase:
            try:
                dados = supabase.table("meus_jogos").select("*").order("created_at", desc=True).limit(10).execute().data
                for j in dados:
                    with st.expander(f"📅 {formata_data_br(j['created_at'])} - {j['loteria']}"):
                        st.write(j['dezenas'])
            except: st.info("Histórico indisponível.")

def gerador_loteria(nome, config):
    # HEADER COM BOTÃO VOLTAR À ESQUERDA
    c_v, c_t = st.columns([1, 4])
    with c_v:
        if st.button("⬅️ Voltar"):
            st.query_params.clear()
            st.session_state.pagina = "Início"
            st.rerun()
    with c_t:
        st.markdown(f'<h2 style="color:{config["cor"]}; margin:0;">{nome}</h2>', unsafe_allow_html=True)

    tab_g, tab_c, tab_b = st.tabs(["🚀 Gerador", "✅ Conferir", "👥 Bolão"])

    with tab_g:
        res_oficial = buscar_resultado_api(config['api'])
        
        # BOTÕES DE AÇÃO CENTRALIZADOS
        st.write("")
        _, centro, _ = st.columns([1, 6, 1])
        with centro:
            ca, cb, cc = st.columns(3)
            with ca:
                if st.button("🎲 Surpresa", use_container_width=True):
                    st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total']+1), config['min_sel'])]
            with cb:
                if st.button("🔥 Quentes", use_container_width=True) and res_oficial:
                    st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in res_oficial['dezenas']]
            with cc:
                if st.button("🗑️ Limpar", use_container_width=True):
                    st.session_state[f"sel_{nome}"] = []; st.rerun()

        # CONTADOR DE DEZENAS
        selecionados = st.session_state.get(f"sel_{nome}", [])
        qtd_atual = len(selecionados)
        cor_badge = "#00ff00" if qtd_atual >= config['min_sel'] else "#58a6ff"
        st.markdown(f'<div class="contador-status" style="color:{cor_badge}; border-color:{cor_badge}">Números Selecionados: {qtd_atual} (Mínimo: {config["min_sel"]})</div>', unsafe_allow_html=True)

        sel = st.segmented_control("V", options=[f"{i:02d}" for i in range(1, config['total']+1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        c1, c2, c3 = st.columns(3)
        with c1: dz = st.number_input("Dezenas/Jogo", config['min_sel'], config['total'], config['min_sel'])
        with c2: 
            tudo = st.checkbox("Gerar Tudo", help="Gera todas as combinações possíveis")
            lim = st.number_input("Limite Máx.", 1, 10000, 100, disabled=tudo)
        with c3:
            p_qtd = len(sel) if (sel and len(sel) >= config['min_sel']) else config['min_sel']
            st.metric("Custo Base", formata_dinheiro(PRECOS_BASE.get(nome, {}).get(p_qtd, 0)))

        with st.expander("🛠️ Filtros Inteligentes"):
            f_s = st.checkbox("Sem sequências")
            f_f = st.checkbox("Limitar finais repetidos")
            f_p = st.checkbox("Equilibrar Par/Ímpar")
            m_p = st.slider("Máx Pares", 0, dz, dz//2) if f_p else dz

        if st.button("🚀 GERAR E SALVAR", type="primary", use_container_width=True):
            if not sel or len(sel) < dz:
                st.error(f"Selecione ao menos {dz} dezenas.")
            else:
                jogos = aplicar_filtros(combinations(sorted([int(x) for x in sel]), dz), f_s, f_f, f_p, m_p, dz, lim, tudo)
                if jogos:
                    st.success(f"{len(jogos)} jogos gerados!")
                    st.dataframe(pd.DataFrame(jogos), use_container_width=True)
                    if supabase:
                        try: supabase.table("meus_jogos").insert({"loteria": nome, "dezenas": jogos}).execute()
                        except: pass
                else: st.warning("Nenhum jogo atendeu aos filtros.")

    with tab_c:
        if res_oficial:
            st.info(f"Último Concurso: {res_oficial['concurso']} ({res_oficial['data']})")
            bolas = "".join([f'<div class="resultado-bola" style="background:{config["cor"]}">{n:02d}</div>' for n in [int(x) for x in res_oficial['dezenas']]])
            st.markdown(bolas, unsafe_allow_html=True)

    with tab_b:
        st.subheader("👥 Divisão de Bolão")
        np = st.number_input("Participantes", 1, 100, 1)
        v_total = float(PRECOS_BASE.get(nome, {}).get(dz, 0))
        st.info(f"Valor por pessoa: **{formata_dinheiro(v_total/np)}**")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
