import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Mobile", layout="wide")

# 2. CSS Avançado para Forçar a Grade 10x6 no Celular
st.markdown("""
    <style>
    /* Força o container de botões a ser uma grade de 10 colunas */
    div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(10, 1fr) !important;
        gap: 2px !important;
    }
    /* Remove o espaçamento extra que o Streamlit coloca entre colunas */
    div[data-testid="column"] {
        width: 100% !important;
        min-width: unset !important;
        flex: unset !important;
    }
    /* Estilização dos botões para ficarem quadrados e compactos */
    button {
        padding: 5px 0px !important;
        height: 35px !important;
        font-size: 12px !important;
        border-radius: 4px !important;
    }
    /* Ajuste para as configurações NÃO ficarem em 10 colunas */
    .config-area div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Pro")

# Layout Principal
col_volante, col_resultados = st.columns([0.4, 0.6])

with col_volante:
    st.subheader("Volante")
    
    atual = sorted(list(st.session_state.selecionados))
    qtd_sel = len(atual)
    st.progress(qtd_sel / 60, text=f"{qtd_sel}/60 Selecionados")
    
    # Renderização do Volante (Forçando a grade de 10)
    # Criamos as 60 colunas de uma vez para o CSS organizar em 10x6
    cols = st.columns(60)
    for i in range(1, 61):
        is_sel = i in st.session_state.selecionados
        if cols[i-1].button(
            f"{i:02d}", 
            key=f"v_{i}_{st.session_state.limpar_count}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if is_sel:
                st.session_state.selecionados.remove(i)
            else:
                if len(st.session_state.selecionados) < 60:
                    st.session_state.selecionados.add(i)
            st.rerun()

    st.divider()
    
    # Área de Configurações (Protegida pelo CSS para não virar grade de 10)
    st.markdown('<div class="config-area">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
        valor_unit = st.number_input("Valor R$", 0.0, 100.0, 5.0)
    with c2:
        gerar_tudo = st.checkbox("Gerar Tudo", False)
        qtd_jogos = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)
    
    st.markdown("### Filtros")
    f_seq = st.checkbox("🚫 Sem Sequências", True)
    f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
    f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
    max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

    b1, b2 = st.columns(2)
    with b1:
        if st.button("❌ Limpar", use_container_width=True):
            st.session_state.selecionados = set()
            st.session_state.limpar_count += 1
            st.rerun()
    with b2:
        gerar = st.button("🚀 GERAR!", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_resultados:
    if gerar:
        st.subheader("Resultados")
        lista_n = sorted(list(st.session_state.selecionados))
        
        if len(lista_n) < dez_por_jogo:
            st.error("Selecione mais números!")
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
                    if len(res) >= qtd_jogos: break

                st.metric("Jogos", f"{len(res):,}".replace(",", "."))
                st.metric("Custo", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.dataframe(res[:1000], use_container_width=True)
                
                # Download
                csv_data = io.StringIO()
                csv_data.write('\ufeff')
                w = csv.writer(csv_data, delimiter=';')
                w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
                for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
                st.download_button("💾 Baixar Excel", csv_data.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
