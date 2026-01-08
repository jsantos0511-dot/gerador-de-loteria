import streamlit as st
import csv
from itertools import combinations
import io
import random

# 1. Configuração da Página
st.set_page_config(page_title="Loteria Flex Mobile", layout="centered")

# 2. CSS para Botões que se ajustam sozinhos (Flexbox)
st.markdown("""
    <style>
    .flex-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        margin: 15px 0;
    }
    
    /* Botões em formato de ficha (Chip) */
    .stButton > button {
        min-width: 45px !important;
        height: 45px !important;
        border-radius: 50% !important; /* Formato circular de loteria */
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 0 !important;
    }
    
    .block-container {
        padding: 1rem 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Estado da Sessão
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# 4. Funções de Apoio
def alternar_numero(n):
    if n in st.session_state.selecionados:
        st.session_state.selecionados.remove(n)
    else:
        st.session_state.selecionados.add(n)

def surpresinha():
    st.session_state.selecionados = set(random.sample(range(1, 61), 6))

st.title("🎰 Gerador Pro Mobile")

# --- VOLANTE FLEXÍVEL ---
st.subheader("Selecione as Dezenas")
st.write(f"**Marcados:** {len(st.session_state.selecionados)}/60")

# Botões de controle rápido
c_sup1, c_sup2 = st.columns(2)
with c_sup1:
    if st.button("🎲 Surpresinha", use_container_width=True):
        surpresinha()
with c_sup2:
    if st.button("❌ Limpar Tudo", use_container_width=True):
        st.session_state.selecionados = set()

# O "Volante" que se ajusta ao tamanho da tela
st.markdown('<div class="flex-container">', unsafe_allow_html=True)
# Criamos os 60 botões um por um dentro do container flexível
for i in range(1, 61):
    is_sel = i in st.session_state.selecionados
    # Usamos o st.button nativo para garantir que a seleção funcione
    if st.button(f"{i:02d}", key=f"n_{i}", type="primary" if is_sel else "secondary"):
        alternar_numero(i)
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES E GERAÇÃO ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        dez_por_jogo = st.number_input("Dezenas por jogo", 6, 20, 6)
        valor_unit = st.number_input("Valor R$", 0.0, 500.0, 5.0)
    with col2:
        qtd_max = st.number_input("Limite de jogos", 1, 1000000, 100)
        gerar_tudo = st.checkbox("Gerar todas")

    with st.expander("🛠️ Filtros"):
        f_seq = st.checkbox("🚫 Sem Sequências", True)
        f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
        max_p = st.slider("Máx. Pares", 1, dez_por_jogo, dez_por_jogo//2 + 1)

    if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
        lista_n = sorted(list(st.session_state.selecionados))
        if len(lista_n) < dez_por_jogo:
            st.error(f"Escolha pelo menos {dez_por_jogo} números!")
        else:
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                j = list(c)
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_par:
                    p = len([n for n in j if n % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                res.append(j)
                if len(res) >= (1000000 if gerar_tudo else qtd_max): break
            
            if res:
                st.success(f"{len(res)} jogos gerados!")
                st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}")
                st.dataframe(res, use_container_width=True)
                
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"D{x+1}" for x in range(dez_por_jogo)])
                for idx, r in enumerate(res):
                    w.writerow([idx+1] + [f"{n:02d}" for n in r])
                
                st.download_button("💾 Baixar Jogos", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
