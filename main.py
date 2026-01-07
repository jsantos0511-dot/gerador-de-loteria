import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# --- CSS DEFINITIVO PARA MOBILE ---
st.markdown("""
    <style>
    /* Esconde menus desnecessários no mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Força o container principal a não ter margens exageradas no celular */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* O SEGREDO: Grade Estática para o Volante */
    .volante-container {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 4px;
        margin-bottom: 15px;
        max-width: 500px;
    }

    /* Estilo dos botões do Streamlit dentro da grade */
    div[data-testid="column"] {
        width: unset !important;
        flex: unset !important;
        min-width: unset !important;
    }
    
    /* Força botões a serem pequenos e quadrados */
    button[kind="secondary"], button[kind="primary"] {
        width: 100% !important;
        height: 38px !important;
        padding: 0px !important;
        font-size: 11px !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Ajuste para as colunas de configurações (2 por linha no mobile) */
    .config-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Mobile")

# Criamos o volante usando um loop de colunas, mas o CSS acima vai forçar 10 por linha
st.subheader("Selecione as Dezenas")

# Informações de status
qtd = len(st.session_state.selecionados)
st.progress(qtd / 60)
st.caption(f"**Selecionados: {qtd}/60** → {sorted(list(st.session_state.selecionados))}")

# VOLANTE (Grade 10x6)
for linha in range(6):
    cols = st.columns(10)
    for coluna in range(10):
        num = linha * 10 + coluna + 1
        is_sel = num in st.session_state.selecionados
        if cols[coluna].button(
            f"{num:02d}", 
            key=f"v_{num}_{st.session_state.limpar_count}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if is_sel:
                st.session_state.selecionados.remove(num)
            else:
                st.session_state.selecionados.add(num)
            st.rerun()

st.divider()

# ÁREA DE CONFIGURAÇÕES
with st.container():
    c1, c2 = st.columns(2)
    with c1:
        dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
        valor_aposta = st.number_input("Valor R$", 0.0, 500.0, 5.0)
    with c2:
        gerar_tudo = st.checkbox("Gerar Tudo")
        qtd_limite = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

    st.markdown("### Filtros")
    f_seq = st.checkbox("🚫 Sem Sequências", True)
    f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
    f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
    max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

    b1, b2 = st.columns(2)
    if b1.button("❌ Limpar", use_container_width=True):
        st.session_state.selecionados = set()
        st.session_state.limpar_count += 1
        st.rerun()
    
    gerar = b2.button("🚀 GERAR!", type="primary", use_container_width=True)

if gerar:
    st.divider()
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error("Selecione os números!")
    else:
        with st.spinner("Gerando..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                j = sorted(list(c))
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_fin and len(set(n % 10 for n in j)) == 1: continue
                if f_par:
                    p = len([n for n in j if n % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                res.append(j)
                if len(res) >= qtd_limite: break

            st.metric("Jogos", f"{len(res):,}".replace(",", "."))
            st.metric("Custo", f"R$ {len(res)*valor_aposta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(res[:500], use_container_width=True)
            
            # Export
            csv_data = io.StringIO()
            csv_data.write('\ufeff')
            w = csv.writer(csv_data, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Planilha", csv_data.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
