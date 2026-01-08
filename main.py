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
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0, "icone": "🍀"},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0, "icone": "🍀"},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5, "icone": "🍀"},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0, "icone": "🍀"},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5, "icone": "🍀"}
}

# --- CONTROLE DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#31333F"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

# 2. CSS DINÂMICO (COM FOCO EM CENTRALIZAÇÃO)
st.markdown(f"""
    <style>
    .titulo-custom {{ color: {cor_tema}; font-size: 2rem; font-weight: bold; text-align: center; margin-bottom: 25px; }}
    
    /* CENTRALIZAÇÃO DOS NÚMEROS NO VOLANTE */
    button[role="option"] {{ 
        min-width: 0px !important; 
        width: 100% !important; 
        height: 45px !important; 
        font-weight: bold !important; 
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        padding: 0 !important;
        font-size: 18px !important;
    }}
    
    button[role="option"][aria-selected="true"] {{ 
        background-color: {cor_tema} !important; 
        color: white !important; 
    }}

    /* GRADE DO VOLANTE */
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({cols_v}, 1fr) !important;
        gap: 6px !important;
        justify-items: center !important;
    }}

    /* CARDS DA HOME - BOTÕES GIGANTES */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div > div > div[data-testid="stButton"] > button[key^="card_"] {{
        height: 120px !important;
        background-color: white !important;
        border: 2px solid #f0f2f6 !important;
        border-radius: 15px !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        color: #333 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: pre-line !important;
    }}

    /* BOTÕES DE COMANDO PADRÃO */
    .stButton > button {{ border-radius: 8px !important; }}
    
    /* ESCONDER SIDEBAR */
    [data-testid="stSidebar"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE FILTRO ---
def aplicar_filtros(combos, f_seq, f_finais, f_par, max_p, dez_jogo, limite, gerar_tudo):
    res = []
    for c in combos:
        jogo = list(c)
        if f_seq and any(jogo[i+1] == jogo[i]+1 for i in range(len(jogo)-1)): continue
        if f_finais:
            finais = [n % 10 for n in jogo]
            if any(finais.count(f) > 4 for f in finais): continue
        if f_par:
            p = len([n for n in jogo if n % 2 == 0])
            if p > max_p or (dez_jogo - p) > max_p: continue
        res.append(jogo)
        if not gerar_tudo and len(res) >= limite: break
    return res

# --- PÁGINAS ---

def home():
    st.markdown('<div class="titulo-custom">🍀 Portal de Loterias</div>', unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        with alvo:
            if st.button(f"🍀\n{nome}", key=f"card_{nome}", use_container_width=True):
                st.session_state.pagina = nome
                st.rerun()

def gerador_loteria(nome, config):
    if st.button("⬅️ Voltar ao Menu", key="btn_voltar", use_container_width=True):
        st.session_state.pagina = "Início"
        st.rerun()

    st.markdown(f'<div class="titulo-custom">🍀 {nome}</div>', unsafe_allow_html=True)
    
    key_sel = f"sel_{nome}"
    if key_sel not in st.session_state: st.session_state[key_sel] = []
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Surpresinha", key="btn_surp", use_container_width=True):
            st.session_state[key_sel] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
    with c2:
        if st.button("❌ Limpar", key="btn_limp", use_container_width=True):
            st.session_state[key_sel] = []
            st.rerun()

    # O volante agora está configurado com os estilos de centralização acima
    opcoes = [f"{i:02d}" for i in range(1, config['total'] + 1)]
    selecionados = st.segmented_control("V", options=opcoes, selection_mode="multi", key=key_sel, label_visibility="collapsed")
    
    st.write(f"**Selecionados:** {len(selecionados)}")
