import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Mega Sena", layout="centered")

# 2. CSS REFORÇADO (FORÇA 6 COLUNAS NO MOBILE)
st.markdown("""
    <style>
    /* Reduz o título principal */
    h1 { font-size: 1.6rem !important; text-align: center; }

    /* SELETOR REFORÇADO: Ataca a estrutura interna do componente de seleção */
    div[role="group"][aria-label="Volante:"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 6px !important;
        width: 100% !important;
    }

    /* Estilo dos botões (Bolas) */
    div[role="group"] button {
        width: 100% !important;
        min-width: 0px !important;
        height: 42px !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        font-size: 19px !important; /* Tamanho solicitado */
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Garante que o container mobile não esmague a grade */
    .block-container {
        padding: 1rem 0.5rem !important;
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador de Mega Sena")

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = []

def surpresinha():
    opcoes = [f"{i:02d}" for i in range(1, 61)]
    st.session_state.selecionados = random.sample(opcoes, 6)

# --- ÁREA DE SELEÇÃO ---
st.subheader("Escolha suas dezenas")

c1, c2 = st.columns(2)
with c1:
    if st.button("🎲 Surpresinha", use_container_width=True):
        surpresinha()
with c2:
    if st.button("❌ Limpar Seleção", use_container_width=True):
        st.session_state.selecionados = []
        st.rerun()

# Volante com 6 colunas fixas
opcoes_volante = [f"{i:02d}" for i in range(1, 61)]

# O 'label' aqui deve ser exatamente igual ao do CSS lá em cima
selecionados_finais = st.segmented_control(
    "Volante:",
    options=opcoes_volante,
    selection_mode="multi",
    key="selecionados",
    label_visibility="collapsed"
)

st.write(f"**Selecionados:** {len(selecionados_finais)} de 60")
st.divider()

# --- CONFIGURAÇÕES ---
col_a, col_b = st.columns(2)
with col_a:
    dez_per_jogo = st.number_input("Bolas por jogo", 6, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with col_b:
    qtd_max = st.number_input("Limite", 1, 1000000, 100)

if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
    if len(selecionados_finais) < dez_per_jogo:
        st.error(f"Selecione pelo menos {dez_per_jogo} números.")
    else:
        lista_n = sorted([int(x) for x in selecionados_finais])
        
        with st.spinner("Gerando..."):
            combos = combinations(lista_n, dez_per_jogo)
            res = []
            for c in combos:
                res.append(list(c))
                if len(res) >= qtd_max: break
            
            if res:
                st.success(f"{len(res)} combinações!")
                colunas_bolas = [f"Bola {x+1}" for x in range(dez_por_jogo)]
                res_formatado = [[f"{n:02d}" for n in jogo] for jogo in res]
                
                df_final = pd.DataFrame(res_formatado, columns=colunas_bolas)
                df_final.index = df_final.index + 1 
                
                st.dataframe(df_final, use_container_width=True)
                
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["ID"] + colunas_bolas)
                for idx, r in enumerate(res):
                    w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                
                st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), 
                                 "jogos_mega.csv", "text/csv", use_container_width=True)
                
                st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}")
