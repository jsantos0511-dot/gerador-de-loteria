import streamlit as st
import csv
from itertools import combinations
import io
import random

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria", layout="centered")

# 2. Estilização dos componentes para Mobile
st.markdown("""
    <style>
    button[role="option"] {
        min-width: 45px !important;
        height: 40px !important;
        justify-content: center !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    .block-container { padding: 1rem 0.6rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = []

def surpresinha():
    opcoes = [f"{i:02d}" for i in range(1, 61)]
    st.session_state.selecionados = random.sample(opcoes, 6)

st.subheader("Escolha suas dezenas")

c1, c2 = st.columns(2)
with c1:
    if st.button("🎲 Surpresinha", use_container_width=True):
        surpresinha()
with c2:
    if st.button("❌ Limpar", use_container_width=True):
        st.session_state.selecionados = []
        st.rerun()

opcoes_volante = [f"{i:02d}" for i in range(1, 61)]

selecionados_finais = st.segmented_control(
    "Toque nos números:",
    options=opcoes_volante,
    selection_mode="multi",
    key="selecionados",
    label_visibility="collapsed"
)

st.write(f"**Selecionados:** {len(selecionados_finais)}/60")
st.divider()

# --- CONFIGURAÇÕES ---
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
        lista_n = sorted([int(x) for x in selecionados_finais])
        
        with st.spinner("Gerando..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                res.append(list(c))
                if len(res) >= qtd_max: break
            
            if res:
                st.success(f"{len(res)} combinações geradas!")
                
                # --- TABELA COM CABEÇALHO 'BOLA X' E ÍNDICE INICIANDO EM 1 ---
                colunas_bolas = [f"Bola {x+1}" for x in range(dez_por_jogo)]
                
                # Criamos o DataFrame formatando os números com dois dígitos (01, 02...)
                # O índice [1, 2, 3...] substitui a palavra 'Jogo'
                import pandas as pd
                df_final = pd.DataFrame(res, columns=colunas_bolas)
                df_final.index = df_final.index + 1 
                
                st.dataframe(df_final, use_container_width=True)
                
                # --- CSV PARA DOWNLOAD ---
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                # Cabeçalho do CSV
                w.writerow(["ID"] + colunas_bolas)
                
                for idx, r in enumerate(res):
                    w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                
                st.download_button(
                    "💾 Baixar Planilha", 
                    csv_io.getvalue().encode('utf-8-sig'), 
                    "jogos_gerados.csv", 
                    "text/csv", 
                    use_container_width=True
                )

                st.metric("Investimento Total", f"R$ {len(res)*valor_unit:,.2f}")
