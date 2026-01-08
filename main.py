import streamlit as st
import csv
from itertools import combinations
import io
import random

# Configuração da Página
st.set_page_config(page_title="Loteria Mobile Pro", layout="centered")

st.title("🎰 Gerador de Jogos")

# --- ESTADO DA SESSÃO ---
# Precisamos disso para que o botão de surpresinha consiga "escrever" no multiselect
if 'selecionados_fichas' not in st.session_state:
    st.session_state.selecionados_fichas = []

# --- FUNÇÃO SURPRESINHA ---
def gerar_surpresinha():
    # Gera 6 números aleatórios únicos que ainda não foram selecionados
    total_opcoes = [f"{i:02d}" for i in range(1, 61)]
    # Se quiser que a surpresinha sempre gere 6 novos:
    st.session_state.selecionados_fichas = random.sample(total_opcoes, 6)

# --- SELEÇÃO DE NÚMEROS ---
st.subheader("1. Escolha suas dezenas")

col_sup1, col_sup2 = st.columns([3, 1])

with col_sup2:
    # Botão de Surpresinha posicionado estrategicamente
    if st.button("🎲 Surpresa", use_container_width=True, help="Gera 6 números aleatórios"):
        gerar_surpresinha()

with col_sup1:
    opcoes = [f"{i:02d}" for i in range(1, 61)]
    selecionados_str = st.multiselect(
        "Números selecionados:",
        options=opcoes,
        key="selecionados_fichas", # Vincula ao estado da sessão
        help="Toque para adicionar ou remover"
    )

# Conversão para cálculos
selecionados = [int(n) for n in selecionados_str]
qtd = len(selecionados)

if qtd > 0:
    st.info(f"✅ {qtd} números prontos para combinar.")

st.divider()

# --- CONFIGURAÇÕES ---
st.subheader("2. Ajustes e Filtros")

c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas por jogo", 6, 20, 6)
    valor_unit = st.number_input("Preço da Aposta R$", 0.0, 1000.0, 5.0)
with c2:
    qtd_max = st.number_input("Limite de jogos", 1, 1000000, 100)
    gerar_tudo = st.checkbox("Gerar todas")

# Filtros Compactos
with st.expander("🛠️ Filtros de Combinação"):
    f_seq = st.checkbox("🚫 Remover Sequências", True)
    f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
    max_p = st.slider("Máximo de Pares", 1, dez_por_jogo, dez_por_jogo//2 + 1)

# Botão Principal
if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
    if len(selecionados) < dez_por_jogo:
        st.error(f"Selecione pelo menos {dez_por_jogo} números.")
    else:
        with st.spinner("Criando combinações..."):
            limite = 1000000 if gerar_tudo else qtd_max
            combos = combinations(sorted(selecionados), dez_por_jogo)
            res = []
            
            for c in combos:
                j = list(c)
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_par:
                    p = len([n for n in j if n % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                
                res.append(j)
                if len(res) >= limite: break

            if not res:
                st.warning("Nenhum jogo atende aos filtros escolhidos.")
            else:
                st.success(f"Sucesso! {len(res)} jogos gerados.")
                
                st.metric("Investimento Total", f"R$ {len(res)*valor_unit:,.2f}")
                st.dataframe(res, use_container_width=True)
                
                # Exportação
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"D{x+1}" for x in range(dez_por_jogo)])
                for idx, r in enumerate(res):
                    w.writerow([idx+1] + [f"{n:02d}" for n in r])
                
                st.download_button(
                    "💾 BAIXAR PLANILHA", 
                    csv_io.getvalue().encode('utf-8-sig'), 
                    "jogos_loteria.csv", 
                    "text/csv", 
                    use_container_width=True
                )
