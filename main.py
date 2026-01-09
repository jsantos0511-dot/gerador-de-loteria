import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES ---
TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5}
}

# --- NAVEGAÇÃO VIA QUERY PARAMS (Para os cards HTML funcionarem) ---
params = st.query_params
if "escolha" in params:
    st.session_state.pagina = params["escolha"]

if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"

# 2. CSS PARA O MENU DE CARDS GLOSTRY
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    
    /* Estilização dos Cards */
    .card-container {{
        border: 2px solid var(--cor-loteria);
        border-radius: 20px;
        padding: 30px 20px;
        text-align: center;
        background-color: #161b22;
        transition: all 0.3s ease;
        cursor: pointer;
        text-decoration: none !important;
        display: block;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    
    .card-container:hover {{
        transform: translateY(-5px);
        box-shadow: 0 0 20px var(--cor-loteria);
        background-color: #1c2128;
    }}
    
    .card-icon {{ font-size: 40px; margin-bottom: 10px; }}
    .card-title {{ 
        font-size: 22px; 
        font-weight: bold; 
        color: var(--cor-loteria); 
        font-family: 'sans-serif';
    }}

    /* Esconder Sidebar e Menu Padrão */
    [data-testid="stSidebar"] {{ display: none; }}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- PÁGINAS ---

def home():
    st.markdown('<h1 style="text-align:center; margin-bottom:40px;">🍀 Escolha sua Loteria</h1>', unsafe_allow_html=True)
    
    # Criamos colunas para os cards
    col1, col2 = st.columns(2)
    
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        
        # Geramos o Card como um link que recarrega a página com o parâmetro da loteria
        card_html = f"""
        <a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados['cor']};">
            <div class="card-icon">🍀</div>
            <div class="card-title">{nome}</div>
        </a>
        """
        alvo.markdown(card_html, unsafe_allow_html=True)

def gerador_loteria(nome, config):
    # Botão de voltar estilizado
    if st.button("⬅️ Menu Inicial", use_container_width=True):
        st.query_params.clear()
        st.session_state.pagina = "Início"
        st.rerun()

    st.markdown(f'<h1 style="text-align:center; color:{config["cor"]};">🍀 {nome}</h1>', unsafe_allow_html=True)
    st.divider()
    
    # --- LOGICA DO VOLANTE ---
    key_sel = f"sel_{nome}"
    if key_sel not in st.session_state: st.session_state[key_sel] = []
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Surpresinha", use_container_width=True):
            st.session_state[key_sel] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
    with c2:
        if st.button("❌ Limpar Seleção", use_container_width=True):
            st.session_state[key_sel] = []
            st.rerun()

    opcoes = [f"{i:02d}" for i in range(1, config['total'] + 1)]
    st.markdown(f"<style>button[role='option'][aria-selected='true'] {{ background-color: {config['cor']} !important; }}</style>", unsafe_allow_html=True)
    
    selecionados = st.segmented_control("V", options=opcoes, selection_mode="multi", key=key_sel, label_visibility="collapsed")
    
    st.info(f"**{len(selecionados)}** números selecionados")

    # (O restante do código de filtros e geração permanece o mesmo das versões anteriores)
    # ...

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
