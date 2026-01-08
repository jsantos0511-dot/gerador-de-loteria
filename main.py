import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Mega Sena", layout="centered")

# 2. Estilização CSS Reforçada (Grade de 6 Colunas + Expander)
st.markdown("""
    <style>
    h1 { font-size: 1.6rem !important; text-align: center; }
    
    /* FORÇA A GRADE DE 6 COLUNAS NO VOLANTE */
    div[data-testid="stSegmentedControl"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
        width: 100% !important;
    }

    div[data-testid="stSegmentedControl"] button {
        min-width: 0px !important;
        width: 100% !important;
        height: 45px !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        font-size: 19px !important;
        padding: 0px !important;
    }
    
    .block-container { padding: 1rem 0.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
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

opcoes_volante = [f"{i:02d}" for i in range(1, 61)]

selecionados_finais = st.segmented_control(
    "Toque nos números:",
    options=opcoes_volante,
    selection_mode="multi",
    key="selecionados",
    label_visibility="collapsed"
)

st.write(f"**Selecionados:** {len(selecionados_finais)} de 60")
st.divider()

# --- CONFIGURAÇÕES BÁSICAS ---
col_a, col_b = st.columns(2)
with col_a:
    dez_por_jogo = st.number_input("Bolas por jogo", 6, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with col_b:
    qtd_max = st.number_input("Limite de Jogos", 1, 1000000, 100)

# --- FILTROS OCULTOS (EXPANDER) ---
with st.expander("🛠️ Filtros Avançados (Opcional)"):
    st.info("Estes filtros removerão combinações que não atendam aos critérios.")
    filtro_seq = st.checkbox("🚫 Evitar números em sequência (ex: 01, 02)", value=False)
    filtro_par_impar = st.checkbox("⚖️ Equilibrar Pares e Ímpares", value=False)
    
    if filtro_par_impar:
        max_pares = st.slider("Máximo de números PARES por jogo", 0, dez_por_jogo, dez_por_jogo // 2)

# --- BOTÃO DE GERAR ---
if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
    if len(selecionados_finais) < dez_por_jogo:
        st.error(f"Selecione pelo menos {dez_por_jogo} números.")
    else:
        lista_n = sorted([int(x) for x in selecionados_finais])
        
        with st.spinner("Gerando jogos com filtros..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            
            for c in combos:
                jogo = list(c)
                
                # Lógica Filtro de Sequência
                if filtro_seq:
                    tem_sequencia = any(jogo[i+1] == jogo[i] + 1 for i in range(len(jogo)-1))
                    if tem_sequencia: continue
                
                # Lógica Filtro Par/Ímpar
                if filtro_par_impar:
                    qtd_pares = len([n for n in jogo if n % 2 == 0])
                    if qtd_pares > max_pares: continue
                    # Também evita jogos com poucos pares se o usuário quiser equilíbrio
                    if (dez_por_jogo - qtd_pares) > max_pares: continue

                res.append(jogo)
                
                if len(res) >= qtd_max:
                    break
            
            if res:
                st.success(f"{len(res)} jogos gerados com sucesso!")
                
                colunas_bolas = [f"Bola {x+1}" for x in range(dez_por_jogo)]
                res_formatado = [[f"{n:02d}" for n in j] for j in res]
                
                df_final = pd.DataFrame(res_formatado, columns=colunas_bolas)
                df_final.index = df_final.index + 1 
                
                st.dataframe(df_final, use_container_width=True)
                
                # CSV
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["ID"] + colunas_bolas)
                for idx, r in enumerate(res):
                    w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                
                st.download_button(
                    "💾 Baixar Planilha", 
                    csv_io.getvalue().encode('utf-8-sig'), 
                    "jogos_mega.csv", "text/csv", use_container_width=True
                )

                st.metric("Investimento Total", f"R$ {len(res)*valor_unit:,.2f}")
            else:
                st.warning("Nenhum jogo encontrado com esses filtros. Tente relaxar as restrições ou selecionar mais números.")
