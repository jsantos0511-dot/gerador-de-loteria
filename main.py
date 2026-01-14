import streamlit as st
import random
import pandas as pd
import requests
import numpy as np
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime, timedelta

# Tenta importar o Plotly; se falhar, o app continua funcionando sem os gráficos
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- INICIALIZAÇÃO E CONTROLE DE NAVEGAÇÃO ---
def reset_navegacao():
    st.query_params.clear()
    st.session_state.pagina = "Início"
    st.rerun()

if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"

# Sincroniza estado com a URL
q_params = st.query_params
if "escolha" in q_params:
    st.session_state.pagina = q_params["escolha"]

# Inicializa seleções para evitar erros de chaves ausentes
loterias_nomes = ["Mega-Sena", "Lotofácil", "Quina", "Lotomania", "Dupla Sena"]
for lot in loterias_nomes:
    if f"sel_{lot}" not in st.session_state:
        st.session_state[f"sel_{lot}"] = []

# --- CONFIGURAÇÕES DO BANCO DE DADOS ---
SUPABASE_URL = "https://ryzcivhjohgtzixqflwo.supabase.co"
SUPABASE_KEY = "sb_publishable_Mbx3FHs_VoprLY2e9d1QMQ_5309Bglr"

@st.cache_resource
def get_supabase():
    try: return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None

supabase = get_supabase()

# --- CONFIGURAÇÕES DE PREÇOS E TEMAS ---
PRECOS_BASE = {
    "Mega-Sena": {6: 6.0, 7: 42.0, 8: 168.0, 9: 504.0, 10: 1260.0},
    "Lotofácil": {15: 3.5, 16: 56.0, 17: 476.0, 18: 2856.0, 19: 13566.0, 20: 54264.0},
    "Quina": {5: 3.0, 6: 18.0, 7: 63.0, 8: 168.0, 9: 378.0, 10: 756.0},
    "Lotomania": {50: 3.0},
    "Dupla Sena": {6: 3.0, 7: 21.0, 8: 84.0, 9: 252.0, 10: 630.0}
}

TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "min_sel": 6, "api": "megasena", "garantias": ["Quadra", "Quina"]},
    "Lotofácil": {"cor": "#930089", "total": 25, "min_sel": 15, "api": "lotofacil", "garantias": ["11 Pontos", "12 Pontos"]},
    "Quina": {"cor": "#260085", "total": 80, "min_sel": 5, "api": "quina", "garantias": ["Terno", "Quadra"]},
    "Lotomania": {"cor": "#f7941d", "total": 100, "min_sel": 50, "api": "lotomania", "garantias": ["16 Pontos", "17 Pontos"]},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "min_sel": 6, "api": "duplasena", "garantias": ["Quadra", "Quina"]}
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

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main-title { text-align: center; font-size: 1.8rem; font-weight: bold; margin-bottom: 1rem; }
    .card-container { 
        border: 2px solid var(--cor); border-radius: 10px; padding: 20px; 
        text-align: center; background: #161b22; margin-bottom: 10px; cursor: pointer;
    }
    .notificacao { padding: 10px; border-radius: 8px; background: #1c2128; border-left: 5px solid #ffcc00; font-size: 0.7rem; height: 100%; }
    .resultado-bola {
        display: inline-block; width: 32px; height: 32px; line-height: 32px;
        background-color: #209869; color: white; border-radius: 50%;
        text-align: center; margin: 3px; font-weight: bold;
    }
    .contador-flutuante {
        background: #21262d; padding: 8px 15px; border-radius: 30px;
        border: 1px solid #58a6ff; color: #58a6ff; font-weight: bold;
        text-align: center; margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TELAS ---

def home():
    st.markdown('<div class="main-title">🍀 Gerador e Conferidor Pro</div>', unsafe_allow_html=True)
    
    # Alertas de Acumulados
    loterias_alerta = ["megasena", "lotofacil", "quina", "duplasena"]
    cols = st.columns(len(loterias_alerta))
    for i, slug in enumerate(loterias_alerta):
        res = buscar_resultado_api(slug)
        if res:
            valor = res.get('valorEstimadoProximoConcurso', 0)
            cor_b = "border: 2px solid #00ff00;" if valor > 50000000 else ""
            cols[i].markdown(f'<div class="notificacao" style="{cor_b}"><b>{slug.upper()}</b><br><span style="color:#00ff00;">{formata_dinheiro(valor)}</span></div>', unsafe_allow_html=True)

    st.write("---")
    c1, c2 = st.columns(2)
    items = list(TEMAS.items())
    for i in range(len(items)):
        nome, d = items[i]
        alvo = c1 if i % 2 == 0 else c2
        alvo.markdown(f'<a href="/?escolha={nome}" target="_self" style="text-decoration:none; color:white;"><div class="card-container" style="--cor:{d["cor"]}"><b style="font-size:18px;">{nome}</b></div></a>', unsafe_allow_html=True)

    st.write("---")
    t1, t2 = st.tabs(["📂 Histórico por Intervalo", "📊 Analytics"])
    
    with t1:
        ca, cb = st.columns(2)
        ini = ca.date_input("De:", value=datetime.now()-timedelta(days=15))
        fim = cb.date_input("Até:", value=datetime.now())
        if supabase:
            try:
                dados = supabase.table("meus_jogos").select("*").order("created_at", desc=True).execute().data
                filtrados = [j for j in dados if ini.strftime("%Y-%m-%d") <= j['created_at'][:10] <= fim.strftime("%Y-%m-%d")]
                for j in filtrados:
                    with st.expander(f"📅 {formata_data_br(j['created_at'])} - {j['loteria']}"):
                        st.dataframe(pd.DataFrame(j['dezenas']), use_container_width=True)
            except: st.info("Histórico indisponível no momento.")

    with t2:
        if PLOTLY_AVAILABLE and supabase and 'dados' in locals() and dados:
            nums = [n for j in dados for sub in j['dezenas'] for n in sub]
            if nums:
                df = pd.DataFrame(nums, columns=['Num']).value_counts().reset_index(name='Freq')
                st.plotly_chart(px.bar(df.head(10), x='Num', y='Freq', title="Suas 10 dezenas mais geradas", color_discrete_sequence=['#58a6ff']), use_container_width=True)
        else: st.info("Gere jogos para ver estatísticas.")

def gerador_loteria(nome, config):
    st.markdown(f'<div class="main-title" style="color:{config["cor"]};">{nome}</div>', unsafe_allow_html=True)
    
    # Botão Voltar (Reset Total)
    if st.button("⬅️ Voltar para Início", use_container_width=True):
        reset_navegacao()

    tab_g, tab_c, tab_b = st.tabs(["🎲 Gerar Jogos", "✅ Conferir Resultados", "👥 Bolão"])

    with tab_g:
        res_api = buscar_resultado_api(config['api'])
        ca, cb, cc = st.columns(3)
        with ca: 
            if st.button("🎲 Surpresa"): st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total']+1), config['min_sel'])]
        with cb:
            if st.button("🔥 Quentes") and res_api: st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in res_api['dezenas']]
        with cc:
            if st.button("🗑️ Limpar"): st.session_state[f"sel_{nome}"] = []; st.rerun()

        # CONTADOR DE DEZENAS
        selecionados = st.session_state[f"sel_{nome}"]
        qtd = len(selecionados)
        cor_txt = "#00ff00" if qtd >= config['min_sel'] else "#58a6ff"
        st.markdown(f'<div class="contador-flutuante" style="color:{cor_txt}; border-color:{cor_txt}">Selecionados: {qtd} de {config["min_sel"]} (mínimo)</div>', unsafe_allow_html=True)

        sel = st.segmented_control("Números", options=[f"{i:02d}" for i in range(1, config['total']+1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        c1, c2, c3 = st.columns(3)
        with c1: dz = st.number_input("Dezenas/Jogo", config['min_sel'], config['total'], config['min_sel'])
        with c2: lim = st.number_input("Limite de Jogos", 1, 1000, 100)
        with c3:
            p_qtd = len(sel) if (sel and len(sel) >= config['min_sel']) else config['min_sel']
            st.metric("Custo Estimado", formata_dinheiro(PRECOS_BASE.get(nome, {}).get(p_qtd, 0)))

        with st.expander("🛠️ Filtros Inteligentes"):
            f_s = st.checkbox("Sem sequências")
            f_f = st.checkbox("Limitar finais repetidos")
            f_p = st.checkbox("Controlar Pares/Ímpares")
            m_p = st.slider("Máximo de Pares", 0, dz, dz//2) if f_p else dz

        if st.button("🚀 GERAR E SALVAR NO HISTÓRICO", type="primary", use_container_width=True):
            if not sel or len(sel) < dz:
                st.error(f"Selecione pelo menos {dz} dezenas.")
            else:
                jogos = aplicar_filtros(combinations(sorted([int(x) for x in sel]), dz), f_s, f_f, f_p, m_p, dz, lim, False)
                if jogos:
                    st.dataframe(pd.DataFrame(jogos), use_container_width=True)
                    if supabase:
                        try:
                            # Tenta salvar apenas os campos básicos para evitar APIError de colunas inexistentes
                            supabase.table("meus_jogos").insert({"loteria": nome, "dezenas": jogos}).execute()
                            st.success("Salvo com sucesso!")
                        except: st.warning("Jogo gerado, mas houve um erro ao salvar no banco.")
                else: st.warning("Nenhum jogo encontrado com esses filtros.")

    with tab_c:
        if res_api:
            st.info(f"Concurso {res_api['concurso']} ({res_api['data']})")
            bolas = "".join([f'<div class="resultado-bola" style="background:{config["cor"]}">{n:02d}</div>' for n in [int(x) for x in res_api['dezenas']]])
            st.markdown(bolas, unsafe_allow_html=True)
            if supabase:
                try:
                    dt_sort = datetime.strptime(res_api['data'], "%d/%m/%Y").date()
                    meus = supabase.table("meus_jogos").select("*").eq("loteria", nome).execute().data
                    validos = [m for m in meus if (dt_sort - timedelta(days=7)).strftime("%Y-%m-%d") <= m['created_at'][:10] <= dt_sort.strftime("%Y-%m-%d")]
                    for b in validos:
                        with st.expander(f"Seu Jogo de {formata_data_br(b['created_at'])}"):
                            ofic = [int(x) for x in res_api['dezenas']]
                            res_l = [{"Jogo": j, "Acertos": len(set(j) & set(ofic))} for j in b['dezenas']]
                            df_r = pd.DataFrame(res_l).sort_values("Acertos", ascending=False)
                            st.dataframe(df_r, use_container_width=True)
                            if df_r['Acertos'].max() >= (config['min_sel'] - 2): st.balloons(); st.success("🏆 Premiação Detectada!")
                except: st.write("Aguardando sorteio...")

    with tab_b:
        st.subheader("👥 Calculadora de Bolão")
        np = st.number_input("Participantes", 1, 100, 1)
        v_total = float(PRECOS_BASE.get(nome, {}).get(dz, 0))
        st.info(f"Cada um paga: {formata_dinheiro(v_total/np)}")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
