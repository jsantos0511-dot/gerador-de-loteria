import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Portal Loterias", layout="centered")

# CSS Global para garantir o layout em todas as páginas
st.markdown("""
    <style>
    h1 { font-size: 1.6rem !important; text-align: center; }
    div[data-testid="stSegmentedControl"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
        width: 100% !important;
    }
    div[data-testid="stSegmentedControl"] button {
        min-width: 0px !important; width: 100% !important; height: 45px !important;
        font-weight: bold !important; border-radius: 6px !important; font-size: 19px !important;
    }
    .block-container { padding: 1rem 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def gerar_mega(selecionados, dezenas, limite, f_seq, f_finais, f_par, max_p):
    lista_n = sorted([int(x) for x in selecionados])
    combos = combinations(lista_n, dezenas)
    resultado = []
    for c in combos:
        jogo = list(c)
        if f_seq and any(jogo[i+1] == jogo[i]+1 for i in range(len(jogo)-1)): continue
        if f_finais:
            finais = [n % 10 for n in jogo]
            if any(finais.count(f) > 4 for f in finais): continue
        if f_par:
            p = len([n for n in jogo if n % 2 == 0])
            if p > max_p or (dezenas - p) > max_p: continue
        resultado.append(jogo)
        if len(resultado) >= limite: break
    return resultado

# --- PÁGINAS ---

def home():
    st.title("🍀 Gerador de Loterias Pro")
    st.write("Selecione uma modalidade no menu lateral para começar.")
    st.info("Este aplicativo utiliza filtros estatísticos para otimizar seus jogos.")

def mega_sena():
    st.title("🎰 Mega-Sena")
    if 'mega_sel' not in st.session_state: st.session_state.mega_sel = []
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🎲 Surpresinha", use_container_width=True):
            st.session_state.mega_sel = [f"{i:02d}" for i in random.sample(range(1, 61), 6)]
    with col_btn2:
        if st.button("❌ Limpar", use_container_width=True):
            st.session_state.mega_sel = []
            st.rerun()

    sel = st.segmented_control("Selecione:", options=[f"{i:02d}" for i in range(1, 61)], 
                               selection_mode="multi", key="mega_sel", label_visibility="collapsed")
    
    st.write(f"**Selecionados:** {len(sel)}")
    
    with st.expander("🛠️ Filtros e Configurações"):
        d_jogo = st.number_input("Bolas por jogo", 6, 20, 6)
        v_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
        l_jogos = st.number_input("Limite de Jogos", 1, 1000, 100)
        f_s = st.checkbox("🚫 Evitar sequências")
        f_f = st.checkbox("🚫 Evitar +4 finais iguais")
        f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
        m_p = st.slider("Máx Pares", 0, d_jogo, d_jogo//2) if f_p else d_jogo

    if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
        if len(sel) < d_jogo: st.error(f"Selecione {d_jogo} números!")
        else:
            res = gerar_mega(sel, d_jogo, l_jogos, f_s, f_f, f_p, m_p)
            if res:
                df = pd.DataFrame(res, columns=[f"Bola {i+1}" for i in range(d_jogo)])
                df.index += 1
                st.dataframe(df, use_container_width=True)
                st.metric("Total", f"R$ {len(res)*v_unit:,.2f}")
            else: st.warning("Nenhum jogo com esses filtros!")

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Escolha a Loteria:", ["Início", "Mega-Sena", "Lotofácil", "Quina"])

if menu == "Início": home()
elif menu == "Mega-Sena": mega_sena()
else: st.sidebar.warning("Em desenvolvimento...")
