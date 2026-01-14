import streamlit as st
import random
import pandas as pd
import requests
import numpy as np
from supabase import create_client, Client
from itertools import combinations
from datetime import datetime, timedelta

# Importação protegida do Plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    PLOTLY_AVAILABLE = False

# --- INICIALIZAÇÃO DE SEGURANÇA ---
def inicializar_estado():
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Início"
    
    q_params = st.query_params
    if "escolha" in q_params:
        st.session_state.pagina = q_params["escolha"]
    else:
        st.session_state.pagina = "Início"

    loterias = ["Mega-Sena", "Lotofácil", "Quina", "Lotomania", "Dupla Sena"]
    for loteria in loterias:
        if f"sel_{loteria}" not in st.session_state:
            st.session_state[f"sel_{loteria}"] = []

inicializar_estado()

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
    "Mega-Sena": {"cor": "#209869", "total": 60, "min_sel": 6, "api": "megasena", "garantias": ["Quadra", "Quina"]},
    "Lotofácil": {"cor": "#930089", "total": 25, "min_sel": 15, "api": "lotofacil", "garantias": ["11 Pontos", "12 Pontos"]},
    "Quina": {"cor": "#260085", "total": 80, "min_sel": 5, "api": "quina", "garantias": ["Terno", "Quadra"]},
    "Lotomania": {"cor": "#f7941d", "total": 100, "min_sel": 50, "api": "lotomania", "garantias": ["16 Pontos", "17 Pontos"]},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "min_sel": 6, "api": "duplasena", "garantias": ["Quadra", "Quina"]}
}

# --- FUNÇÕES DE APOIO ---
def formata_dinheiro(valor):
    try: return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def formata_data_br(data_string):
    try: return datetime.fromisoformat(data_string.split('.')[0].replace('Z', '')).strftime("%d/%m/%Y %H:%M")
    except: return data_string

@st.cache_data(ttl=3600)
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
st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem !important; }
    .stApp { background-color: #0e1117; color: #ffffff; }
    .main-title { text-align: center; font-size: 1.75rem; font-weight: bold; margin-top: -5px; margin-bottom: 1rem; color: #ffffff; }
    .sub-title { font-size: 1.1rem !important; font-weight: bold; margin-bottom: 8px; }
    .card-link { text-decoration: none !important; color: white !important; }
    .card-container { 
        border: 2px solid var(--cor-loteria); border-radius: 10px; padding: 18px; 
        text-align: center; background-color: #161b22; margin-bottom: 8px; 
        cursor: pointer; transition: 0.3s ease-in-out;
    }
    .card-container:hover { box-shadow: 0 0 15px var(--cor-loteria), 0 0 5px var(--cor-loteria) inset; transform: translateY(-2px); }
    .notificacao { padding: 8px; border-radius: 6px; background: #1c2128; border-left: 4px solid #ffcc00; font-size: 0.65rem; height: 100%; }
    .resultado-bola {
        display: inline-block; width: 30px; height: 30px; line-height: 30px;
        background-color: #209869; color: white; border-radius: 50%;
        text-align: center; margin: 2px; font-weight: bold; font-size: 0.8rem;
    }
    .contador-badge {
        background: #30363d; padding: 5px 12px; border-radius: 20px; 
        font-weight: bold; border: 1px solid #58a6ff; color: #58a6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TELAS ---

def home():
    st.markdown('<div class="main-title">🍀 Gerador Profissional & Analytics</div>', unsafe_allow_html=True)
    
    loterias_check = ["megasena", "quina", "duplasena", "lotofacil"]
    cols_n = st.columns(len(loterias_check), gap="small")
    for idx, slug in enumerate(loterias_check):
        res = buscar_resultado_api(slug)
        if res:
            estimativa = res.get('valorEstimadoProximoConcurso', 0)
            cor_borda = "border: 2px solid #00ff00;" if estimativa > 50000000 else "border-left: 4px solid #ffcc00;"
            cols_n[idx].markdown(f'<div class="notificacao" style="{cor_borda}"><b>{slug.upper()}</b><br><span style="color:#00ff00;">{formata_dinheiro(estimativa)}</span></div>', unsafe_allow_html=True)

    st.write("---")
    col1, col2 = st.columns(2, gap="small")
    loterias_lista = list(TEMAS.items())
    for i in range(len(loterias_lista)):
        nome, dados = loterias_lista[i]
        alvo = col1 if i % 2 == 0 else col2
        alvo.markdown(f'<a href="/?escolha={nome}" target="_self" class="card-link"><div class="card-container" style="--cor-loteria: {dados["cor"]};"><b style="font-size:16px;">{nome}</b></div></a>', unsafe_allow_html=True)
    
    st.write("---")
    tab_hist, tab_stats = st.tabs(["📂 Histórico", "📊 Analytics"])
    
    with tab_hist:
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Início:", value=None, key="hist_ini")
        d_fim = c2.date_input("Fim:", value=None, key="hist_fim")
        if supabase:
            try:
                dados_db = supabase.table("meus_jogos").select("*").order("created_at", desc=True).execute().data
                if d_ini and d_fim:
                    dados_db = [j for j in dados_db if d_ini.strftime("%Y-%m-%d") <= j['created_at'][:10] <= d_fim.strftime("%Y-%m-%d")]
                else:
                    corte = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
                    dados_db = [j for j in dados_db if j['created_at'][:10] >= corte]
                for item in dados_db:
                    with st.expander(f"📅 {formata_data_br(item['created_at'])} - {item['loteria']}"):
                        st.dataframe(pd.DataFrame(item['dezenas']), use_container_width=True)
            except: st.info("Conectando ao histórico...")

    with tab_stats:
        if PLOTLY_AVAILABLE and supabase:
            try:
                dados_db_stats = supabase.table("meus_jogos").select("*").execute().data
                all_nums = [n for j in dados_db_stats for sublist in j['dezenas'] for n in sublist]
                if all_nums:
                    df_counts = pd.DataFrame(all_nums, columns=['Dezena']).value_counts().reset_index(name='Frequência')
                    st.plotly_chart(px.bar(df_counts.head(10), x='Dezena', y='Frequência', title="Dezenas mais usadas por você"), use_container_width=True)
            except: st.info("Sem dados estatísticos.")

def gerador_loteria(nome, config):
    st.markdown(f'<div class="main-title" style="color:{config["cor"]};">🍀 {nome}</div>', unsafe_allow_html=True)
    
    if st.button("⬅️ Voltar ao Início"):
        st.query_params.clear()
        st.session_state.pagina = "Início"
        st.rerun()

    aba_gerar, aba_fechamento, aba_conferir, aba_bolao = st.tabs(["🚀 Gerador", "🛡️ Fechamentos", "✅ Conferir", "👥 Bolão"])

    with aba_gerar:
        res_oficial = buscar_resultado_api(config['api'])
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🎲 Surpresa", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
        with c2:
            if st.button("🔥 Quentes (Últimos)", use_container_width=True) and res_oficial:
                st.session_state[f"sel_{nome}"] = [f"{int(n):02d}" for n in res_oficial['dezenas']]
        with c3:
            if st.button("🗑️ Limpar", use_container_width=True):
                st.session_state[f"sel_{nome}"] = []; st.rerun()

        selecionados = st.session_state[f"sel_{nome}"]
        qtd_sel = len(selecionados)
        cor_cont = "#00ff00" if qtd_sel >= config['min_sel'] else "#58a6ff"
        st.markdown(f'**Selecionados:** <span class="contador-badge" style="color:{cor_cont}; border-color:{cor_cont};">{qtd_sel}</span> dezenas', unsafe_allow_html=True)

        selecionados = st.segmented_control("V", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: dez_jogo = st.number_input("Dezenas por Jogo", config['min_sel'], config['total'], config['min_sel'], key=f"dez_{nome}")
        with col_p2: 
            tudo = st.checkbox("Gerar Tudo", key=f"tudo_{nome}")
            q_max = st.number_input("Limite Máx.", 1, 1000, 100, disabled=tudo, key=f"lim_{nome}")
        with col_p3:
            qtd_para_preco = len(selecionados) if (selecionados and len(selecionados) >= config['min_sel']) else config['min_sel']
            preco = PRECOS_BASE.get(nome, {}).get(qtd_para_preco, "Consulte")
            st.metric("Custo Estimado", formata_dinheiro(preco))

        with st.expander("🛠️ Filtros Inteligentes"):
            f_s = st.checkbox("Sem sequências", key=f"fs_{nome}")
            f_f = st.checkbox("Limitar finais", key=f"ff_{nome}")
            f_p = st.checkbox("Controlar Par/Ímpar", key=f"fp_{nome}")
            m_p = st.slider("Máx Pares", 0, dez_jogo, dez_jogo // 2) if f_p else dez_jogo

        nome_bolao = st.text_input("Identificador (Apostador/Bolão):", "Manual", key=f"id_{nome}")

        # --- SUBSTITUA APENAS O BLOCO DE SALVAMENTO NO SEU CÓDIGO ---

        if st.button("🚀 GERAR E SALVAR", type="primary", use_container_width=True):
            if not selecionados or len(selecionados) < dez_jogo: 
                st.error(f"Selecione pelo menos {dez_jogo} números.")
            else:
                res = aplicar_filtros(combinations(sorted([int(x) for x in selecionados]), dez_jogo), f_s, f_f, f_p, m_p, dez_jogo, q_max, tudo)
                if res:
                    st.dataframe(pd.DataFrame(res), use_container_width=True)
                    if supabase:
                        try:
                            # Inserção com captura de erro bruto para diagnóstico
                            data_insert = {
                                "loteria": nome, 
                                "dezenas": res, 
                                "participantes": nome_bolao
                            }
                            response = supabase.table("meus_jogos").insert(data_insert).execute()
                            st.toast("✅ Jogos salvos!")
                        except Exception as e:
                            # Isso mostrará o erro real do Supabase (ex: 'column loteria does not exist')
                            st.error(f"Erro técnico no banco: {str(e)}")
                            st.info("Dica: Verifique no Supabase se a tabela 'meus_jogos' tem as colunas: loteria, dezenas e participantes.")
                else: st.warning("Nenhum jogo atendeu aos filtros.")
    with aba_conferir:
        if res_oficial:
            st.info(f"Concurso **{res_oficial['concurso']}** - {res_oficial['data']}")
            st.markdown("".join([f'<div class="resultado-bola" style="background-color:{config["cor"]}">{n:02d}</div>' for n in [int(n) for n in res_oficial['dezenas']]]), unsafe_allow_html=True)
            if supabase:
                try:
                    dt_sorteio = datetime.strptime(res_oficial['data'], "%d/%m/%Y").date()
                    dt_sorteio_previo = dt_sorteio - timedelta(days=5)
                    jogos_db = supabase.table("meus_jogos").select("*").eq("loteria", nome).execute().data
                    jogos_v = [j for j in jogos_db if dt_sorteio_previo.strftime("%Y-%m-%d") < j['created_at'][:10] <= dt_sorteio.strftime("%Y-%m-%d")]
                    if jogos_v:
                        oficiais = [int(n) for n in res_oficial['dezenas']]
                        for bloco in jogos_v:
                            with st.expander(f"Aposta: {bloco.get('participantes')} - {formata_data_br(bloco['created_at'])}"):
                                res_lista = [{"Jogo": j, "Acertos": len(set(j) & set(oficiais))} for j in bloco['dezenas']]
                                df_res = pd.DataFrame(res_lista).sort_values("Acertos", ascending=False)
                                st.dataframe(df_res, use_container_width=True)
                                if df_res['Acertos'].max() >= (config['min_sel'] - 2): st.balloons(); st.success("🏆 PREMIADO!")
                except: st.info("Conectando ao histórico...")

    with aba_bolao:
        st.subheader("👥 Divisão de Cotas")
        n_pessoas = st.number_input("Total de Participantes:", 1, 100, 1, key=f"np_{nome}")
        valor_base = float(PRECOS_BASE.get(nome, {}).get(dez_jogo, 0))
        if n_pessoas > 0:
            st.info(f"Valor por pessoa: **{formata_dinheiro(valor_base / n_pessoas)}**")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": 
    home()
else: 
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
