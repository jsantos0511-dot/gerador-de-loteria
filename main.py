import streamlit as st
import csv
from itertools import combinations
import io
import random

# 1. Configuração da Página
st.set_page_config(page_title="Loteria Mobile", layout="centered")

# 2. CSS para deixar o seletor com cara de volante de loteria
st.markdown("""
    <style>
    /* Estiliza os botões do seletor para serem circulares/quadrados pequenos */
    button[role="option"] {
        min-width: 45px !important;
        height: 40px !important;
        justify-content: center !important;
        font-weight: bold !important;
    }
    
    /* Garante que o container ocupe a largura total sem margens laterais grandes */
    .block-container { padding: 1rem 0.6rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")

# --- ESTADO DA SESSÃO ---
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = []

# --- FUNÇÃO SURPRESINHA ---
def surpresinha():
    opcoes = [f"{i:02d}" for i in range(1, 61)]
    st.session_state.selecionados = random.sample(opcoes, 6)

st.subheader("Escolha suas dezenas")

# Botões de ação rápida
c1, c2 = st.columns(2)
with c1:
    if st.button("🎲 Surpresinha", use_container_width=True):
        surpresinha()
with c2:
    if st.button("❌ Limpar", use_container_width=True):
        st.session_state.selecionados = []
        st.rerun()

# 3. O SEGREDO: st.segmented_control
# Este componente foi feito para seleções múltiplas de forma compacta
opcoes_volante = [f"{i:02d}" for i in range(1, 61)]

selecionados_finais = st.segmented_control(
    "Toque nos números para selecionar:",
    options=opcoes_volante,
    selection_mode="multi", # Permite escolher vários
    key="selecionados",     # Conectado ao session_state
    label_visibility="collapsed"
)

qtd = len(selecionados_finais)
st.write(f"**Selecionados:** {qtd}/60")

st.divider()

# --- ÁREA DE CÁLCULO ---
col_a, col_b = st.columns(2)
with col_a:
    dez_por_jogo = st.number_input("Dezenas por jogo", 6, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with col_b:
    qtd_max = st.number_input("Limite de jogos", 1, 1000000, 100)

if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
    if len(selecionados_finais) < dez_por_jogo:
        st.error(f"Selecione pelo menos {dez_por_jogo} números.")
    else:
        # Converte strings '01' para inteiros 1 para o cálculo
        lista_n = sorted([int(x) for x in selecionados_finais])
        
        with st.spinner("Gerando..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                res.append(list(c))
                if len(res) >= qtd_max: break
            
            if res:
                st.success(f"{len(res)} jogos gerados!")
                st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}")
                st.dataframe(res, use_container_width=True)
                
                # Exportação CSV
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"D{x+1}" for x in range(dez_por_jogo)])
                for idx, r in enumerate(res):
                    w.writerow([idx+1] + [f"{n:02d}" for n in r])
                
                st.download_button("💾 Baixar Jogos", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
