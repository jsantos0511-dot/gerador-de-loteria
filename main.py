import streamlit as st
import csv
from itertools import combinations
import io
import random

# 1. Configuração da Página
st.set_page_config(page_title="Loteria Mobile", layout="centered")

# 2. Inicialização do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# 3. CSS para Forçar Botões Pequenos e Lado a Lado
st.markdown("""
    <style>
    /* Remove o limite de largura que faz o Streamlit empilhar colunas */
    [data-testid="column"] {
        min-width: 0px !important;
        flex: 1 1 0% !important;
        padding: 2px !important;
    }
    
    /* Estilo dos botões nativos para parecerem Chips */
    .stButton > button {
        width: 100% !important;
        height: 38px !important;
        padding: 0px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }

    /* Reduz margens do app para mobile */
    .block-container { padding: 1rem 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Marcados:** {len(st.session_state.selecionados)}")

# Botões de Ações Rápidas
c_sup1, c_sup2 = st.columns(2)
with c_sup1:
    if st.button("🎲 Surpresinha", use_container_width=True):
        st.session_state.selecionados = set(random.sample(range(1, 61), 6))
        st.rerun()
with c_sup2:
    if st.button("❌ Limpar Tudo", use_container_width=True):
        st.session_state.selecionados = set()
        st.rerun()

# --- GRADE DE BOTÕES (6 COLUNAS QUE NÃO QUEBRAM) ---
# Em vez de 10 linhas, vamos criar blocos menores para o Streamlit aceitar melhor
for linha in range(10):
    cols = st.columns(6) # Criamos 6 colunas reais
    for coluna in range(6):
        num = linha * 6 + coluna + 1
        is_sel = num in st.session_state.selecionados
        
        # O segredo: use_container_width=True faz ele respeitar a largura da mini-coluna
        if cols[coluna].button(
            f"{num:02d}", 
            key=f"n_{num}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if is_sel:
                st.session_state.selecionados.remove(num)
            else:
                st.session_state.selecionados.add(num)
            st.rerun()

st.divider()

# --- CONFIGURAÇÕES E GERAÇÃO ---
col_a, col_b = st.columns(2)
with col_a:
    dez_por_jogo = st.number_input("Dezenas por jogo", 6, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with col_b:
    qtd_max = st.number_input("Limite de jogos", 1, 1000000, 50)

if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error(f"Selecione ao menos {dez_por_jogo} números!")
    else:
        with st.spinner("Gerando..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                res.append(list(c))
                if len(res) >= qtd_max: break
            
            if res:
                st.success(f"{len(res)} jogos gerados!")
                st.dataframe(res, use_container_width=True)
                
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"D{x+1}" for x in range(dez_por_jogo)])
                for idx, r in enumerate(res):
                    w.writerow([idx+1] + [f"{n:02d}" for n in r])
                
                st.download_button("💾 Baixar Jogos", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
