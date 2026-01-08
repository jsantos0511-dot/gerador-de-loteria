import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias", layout="centered")

# --- DICIONÁRIO DE CORES TEMÁTICAS ---
TEMAS = {
    "Início": {"cor": "#31333F", "titulo": "Portal de Loterias"},
    "Mega-Sena": {"cor": "#209869", "titulo": "Mega-Sena"},     # Verde Oficial
    "Lotofácil": {"cor": "#930089", "titulo": "Lotofácil"},     # Roxo Oficial
    "Quina": {"cor": "#260085", "titulo": "Quina"},             # Azul Oficial
    "Lotomania": {"cor": "#f7941d", "titulo": "Lotomania"}      # Laranja Oficial
}

# --- MENU DE NAVEGAÇÃO ---
menu = st.sidebar.radio("Escolha a Loteria:", list(TEMAS.keys()))
tema_atual = TEMAS[menu]

# 2. CSS DINÂMICO (Muda conforme a seleção)
st.markdown(f"""
    <style>
    /* Cor do Título Dinâmica */
    .titulo-custom {{
        color: {tema_atual['cor']};
        font-size: 1.8rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }}

    /* Estilo dos Botões do Volante (Cores Oficiais) */
    button[role="option"][aria-selected="true"] {{
        background-color: {tema_atual['cor']} !important;
        color: white !important;
    }}

    /* Grade de 6 colunas para Mega e Quina, 5 para Lotofácil */
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({5 if menu == "Lotofácil" else 6 if menu == "Mega-Sena" else 8}, 1fr) !important;
        gap: 5px !important;
    }}

    button[role="option"] {{
        min-width: 0px !important; width: 100% !important; height: 45px !important;
        font-weight: bold !important; border-radius: 6px !important; font-size: 18px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE PÁGINA ---

def home():
    st.markdown(f'<div class="titulo-custom">{tema_atual["titulo"]}</div>', unsafe_allow_html=True)
    st.info("Selecione uma modalidade ao lado para gerar seus jogos com filtros estatísticos.")

def gerador_loteria(nome_loteria, total_numeros):
    st.markdown(f'<div class="titulo-custom">Gerador {nome_loteria}</div>', unsafe_allow_html=True)
    
    key_sel = f"sel_{nome_loteria}"
    if key_sel not in st.session_state: st.session_state[key_sel] = []
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Surpresinha", use_container_width=True):
            st.session_state[key_sel] = [f"{i:02d}" for i in random.sample(range(1, total_numeros + 1), 6)]
    with c2:
        if st.button("❌ Limpar", use_container_width=True):
            st.session_state[key_sel] = []
            st.rerun()

    opcoes = [f"{i:02d}" for i in range(1, total_numeros + 1)]
    selecionados = st.segmented_control("Volante", options=opcoes, selection_mode="multi", key=key_sel, label_visibility="collapsed")
    
    st.write(f"**Selecionados:** {len(selecionados)}")
    st.divider()

    # --- CONFIGS E GERAÇÃO ---
    with st.expander("🛠️ Filtros Avançados"):
        d_jogo = st.number_input("Dezenas por jogo", 6, 20, 6)
        l_jogos = st.number_input("Limite de combinações", 1, 1000, 100)
        f_s = st.checkbox("🚫 Sem sequências")

    if st.button(f"🚀 GERAR JOGOS {nome_loteria.upper()}", type="primary", use_container_width=True):
        if len(selecionados) < d_jogo:
            st.error(f"Selecione no mínimo {d_jogo} números!")
        else:
            # Lógica simples de geração (pode ser expandida com seus filtros anteriores)
            lista_n = sorted([int(x) for x in selecionados])
            res = [list(c) for c in combinations(lista_n, d_jogo)][:l_jogos]
            
            df = pd.DataFrame(res, columns=[f"B{i+1}" for i in range(d_jogo)])
            df.index += 1
            st.dataframe(df, use_container_width=True)

# --- ROTEAMENTO ---
if menu == "Início":
    home()
elif menu == "Mega-Sena":
    gerador_loteria("Mega-Sena", 60)
elif menu == "Lotofácil":
    gerador_loteria("Lotofácil", 25)
elif menu == "Quina":
    gerador_loteria("Quina", 80)
else:
    st.write("Em desenvolvimento...")
