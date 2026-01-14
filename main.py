import streamlit as st
import random
import pandas as pd
import requests
import numpy as np
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime, timedelta

# Importação protegida para o Analytics
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- CONTROLE DE ESTADO E NAVEGAÇÃO ---
if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"

def voltar_home():
    st.query_params.clear()
    st.session_state.pagina = "Início"
    st.rerun()

# --- CONEXÃO BANCO DE DADOS ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = get_supabase()

# --- CONFIGURAÇÕES TÉCNICAS (RESTAURADAS) ---
PRECOS_BASE = {
    "Mega-Sena": {6: 6.0, 7: 42.0, 8: 168.0, 9: 504.0, 10: 1260.0, 11: 2772.0, 12: 5544.0},
    "Lotofácil": {15: 3.0, 16: 48.0, 17: 408.0, 18: 2448.0, 19: 11628.0, 20: 46512.0},
    "Quina": {5: 2.5, 6: 15.0, 7: 52.5, 8: 140.0, 9: 315.0, 10: 630.0},
    "Lotomania": {50: 3.0},
    "Dupla Sena": {6: 2.5, 7: 17.5, 8: 70.0, 9: 210.0, 10: 525.0}
}

TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "min_sel": 6, "api": "megasena"},
    "Lotofácil": {"cor": "#930089", "total": 25, "min_sel": 15, "api": "lotofacil"},
    "Quina": {"cor": "#260085", "total": 80, "min_sel": 5, "api": "quina"},
    "Lotomania": {"cor": "#f7941d", "total": 100, "min_sel": 50, "api": "lotomania"},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "min_sel": 6, "api": "duplasena"}
}

# --- FUNÇÕES AUXILIARES ---
def formata_dinheiro(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(ttl=3600)
def buscar_resultado(slug):
    try:
        r = requests.get(f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest", timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

def aplicar_filtros(combos, f_seq, f_fin, f_par, max_p, dez_jogo, limite, tudo):
    res = []
    for c in combos:
        j = list(c)
        if f_seq and any(j[i+1] == j[i]+1 for i in range(len(j)-1)): continue
        if f_fin and any([n % 10 for n in j].count(f) > 3 for f in [n % 10 for n in j]): continue
        if f_par:
            p = len([n for n in j if n % 2 == 0])
            if p > max_p or (dez_jogo - p) > max_p: continue
        res.append(j)
        if not tudo and len(res) >= limite: break
    return res

# --- ESTILO CSS (INTERFACE LIMPA) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .card-loteria { 
        border: 2px solid var(--c); border-radius: 12px; padding: 25px; 
        text-align: center; background: #161b22; transition: 0.3s;
    }
    .card-loteria:hover { transform: scale(1.02); box-shadow: 0 0 15px var(--c); }
    .status-badge { 
        background: #1c2128; border: 1px solid #58a6ff; color: #58a6ff;
        padding: 10px; border-radius: 10px; text-align: center; font-weight: bold;
    }
    .bola {
        display: inline-block; width: 35px; height: 35px; line-height: 35px;
        background: #209869; border-radius: 50%; text-align: center; margin: 4px; font-weight: bold;
    }
    .alerta-acumulado {
        padding: 10px; border-radius: 8px; background: #1c2128; 
        border-left: 5px solid #00ff00; font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE TELAS ---

def home():
    st.markdown('<h1 style="text-align:center;">🍀 Central de Loterias Pro</h1>', unsafe_allow_html=True)
    
    # Seção de Alertas (Acumulados)
    loterias_monitor = ["megasena", "lotofacil", "quina"]
    cols_a = st.columns(len(loterias_monitor))
    for i, slug in enumerate(loterias_monitor):
        res = buscar_resultado(slug)
        if res:
            valor = res.get('valorEstimadoProximoConcurso', 0)
            cols_a[i].markdown(f'<div class="alerta-acumulado"><b>{slug.upper()}</b><br>{formata_dinheiro(valor)}</div>', unsafe_allow_html=True)

    st.write("---")
    
    # Grid de Loterias
    c1, c2 = st.columns(2)
    lots = list(TEMAS.items())
    for i, (nome, d) in enumerate(lots):
        alvo = c1 if i % 2 == 0 else c2
        if alvo.button(f"➔ {nome}", use_container_width=True):
            st.query_params.escolha = nome
            st.session_state.pagina = nome
            st.rerun()

    st.write("---")
    tab_h, tab_a = st.tabs(["📂 Histórico Geral", "📊 Analytics de Uso"])
    
    with tab_h:
        if supabase:
            try:
                dados = supabase.table("meus_jogos").select("*").order("created_at", desc=True).limit(20).execute().data
                if dados:
                    for j in dados:
                        with st.expander(f"{j['created_at'][:10]} - {j['loteria']}"):
                            st.write(j['dezenas'])
                else: st.info("Nenhum jogo salvo ainda.")
            except: st.error("Erro ao carregar banco de dados.")

    with tab_a:
        if PLOTLY_AVAILABLE and 'dados' in locals() and dados:
            all_n = [n for j in dados for sub in j['dezenas'] for n in sub]
            if all_n:
                df = pd.DataFrame(all_n, columns=['Dezena']).value_counts().reset_index(name='Vezes')
                st.plotly_chart(px.bar(df.head(15), x='Dezena', y='Vezes', title="Suas dezenas preferidas"), use_container_width=True)
        else: st.warning("Analytics requer dados salvos e biblioteca Plotly.")

def gerador_loteria(nome, config):
    # Header com Voltar à Esquerda
    col_v, col_t = st.columns([1, 4])
    with col_v:
        if st.button("⬅ Voltar"): voltar_home()
    with col_t:
        st.markdown(f'<h2 style="color:{config["cor"]};">{nome}</h2>', unsafe_allow_html=True)

    t_gerar, t_conf, t_bol = st.tabs(["🎲 Gerar", "✅ Resultados", "👥 Bolão"])

    with t_gerar:
        res_api = buscar_resultado(config['api'])
        
        # Botões de Ação Centralizados
        _, centro, _ = st.columns([1, 6, 1])
        with centro:
            ca, cb, cc = st.columns(3)
            if ca.button("🎲 Surpresa", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total']+1), config['min_sel'])]
            if cb.button("🔥 Tendência", use_container_width=True) and res_api:
                st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in res_api['dezenas']]
            if cc.button("🗑 Limpar", use_container_width=True):
                st.session_state[f"sel_{nome}"] = []; st.rerun()

        # Contador de Dezenas
        selecionados = st.session_state.get(f"sel_{nome}", [])
        qtd_s = len(selecionados)
        st.markdown(f'<div class="status-badge">Selecionados: {qtd_s} de {config["min_sel"]} (mínimo)</div>', unsafe_allow_html=True)

        sel = st.segmented_control("Escolha", options=[f"{i:02d}" for i in range(1, config['total']+1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        # Parâmetros
        c1, c2, c3 = st.columns(3)
        with c1: dz = st.number_input("Dezenas p/ Jogo", config['min_sel'], config['total'], config['min_sel'])
        with c2: 
            tudo = st.checkbox("Gerar Tudo", help="Ignora o limite e gera todas as combinações")
            lim = st.number_input("Limite", 1, 10000, 100, disabled=tudo)
        with c3:
            p_val = len(sel) if (sel and len(sel) >= config['min_sel']) else config['min_sel']
            st.metric("Custo Base", formata_dinheiro(PRECOS_BASE.get(nome, {}).get(p_val, 0)))

        with st.expander("🛠 Filtros Avançados (Tendências)"):
            f_s = st.checkbox("Eliminar Sequências (ex: 01, 02, 03)")
            f_f = st.checkbox("Evitar muitos números com mesmo final")
            f_p = st.checkbox("Equilibrar Par/Ímpar")
            m_p = st.slider("Qtd Máxima de Pares", 0, dz, dz//2) if f_p else dz

        if st.button("🚀 GERAR JOGOS AGORA", type="primary", use_container_width=True):
            if len(sel) < dz:
                st.error(f"Selecione ao menos {dz} números.")
            else:
                jogos = aplicar_filtros(combinations(sorted([int(x) for x in sel]), dz), f_s, f_f, f_p, m_p, dz, lim, tudo)
                if jogos:
                    st.success(f"{len(jogos)} jogos criados!")
                    st.dataframe(pd.DataFrame(jogos), use_container_width=True)
                    if supabase:
                        try: supabase.table("meus_jogos").insert({"loteria": nome, "dezenas": jogos}).execute()
                        except: pass
                else: st.warning("Nenhum jogo passou pelos filtros.")

    with t_conf:
        if res_api:
            st.subheader(f"Concurso {res_api['concurso']} ({res_api['data']})")
            bolas_html = "".join([f'<div class="bola" style="background:{config["cor"]}">{n:02d}</div>' for n in [int(x) for x in res_api['dezenas']]])
            st.markdown(bolas_html, unsafe_allow_html=True)
            st.write(f"**Prêmio Estimado:** {formata_dinheiro(res_api.get('valorEstimadoProximoConcurso', 0))}")

    with t_bol:
        st.subheader("👥 Divisão de Cotas")
        np = st.number_input("Total de Amigos/Cotas", 1, 200, 1)
        v_jogo = float(PRECOS_BASE.get(nome, {}).get(dz, 0))
        st.info(f"Cada cota custará: **{formata_dinheiro(v_jogo/np)}**")

# --- START ---
if "escolha" in st.query_params:
    st.session_state.pagina = st.query_params.escolha

if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
