import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria", layout="centered")

# 2. Estilização Mobile com Aumento de Fonte no Volante
st.markdown("""
    <style>
    /* Estiliza os botões do seletor (Volante) */
    button[role="option"] {
        min-width: 48px !important;
        height: 45px !important;
        justify-content: center !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        /* Aumentado em 3px (de 16px para 19px) */
        font-size: 19px !important; 
    }
    
    /* Ajuste para o texto não ficar colado na borda no mobile */
    .block-container { padding: 1rem 0.6rem !important; }
    
    /* Melhora a legibilidade do cabeçalho da tabela */
    [data-testid="stHeader"] { font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Mega Sena")

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

# Componente Segmented Control (Volante)
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
                
                # Cabeçalhos Bola 1, Bola 2...
                colunas_bolas = [f"Bola {x+1}" for x in range(dez_por_jogo)]
                
                # Formatação com 2 dígitos para a tabela
                res_formatado = [[f"{n:02d}" for n in jogo] for jogo in res]
                
                df_final = pd.DataFrame(res_formatado, columns=colunas_bolas)
                df_final.index = df_final.index + 1 
                
                st.dataframe(df_final, use_container_width=True)
                
                # --- CSV PARA DOWNLOAD ---
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
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
