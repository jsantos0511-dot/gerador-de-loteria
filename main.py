import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. CSS Corrigido para Colunas Estreitas (6 por linha)
st.markdown("""
    <style>
    /* Ajuste do container principal */
    .block-container {
        padding: 1rem 0.5rem !important;
    }
    
    /* FORÇAR GRADE DE 6 COLUNAS REAIS */
    div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important; /* Divide em 6 fatias iguais */
        gap: 4px !important;
        width: 100% !important;
    }

    /* Impede que as colunas internas do Streamlit estiquem sozinhas */
    div[data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 !important;
    }

    /* Estilo do Botão: Compacto e Centralizado */
    button {
        height: 40px !important;
        width: 100% !important;
        padding: 0px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        border-radius: 4px !important;
    }

    /* Reset para a área de configurações (não queremos 6 colunas aqui) */
    .config-box div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
        gap: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Pro")

# --- VOLANTE COMPACTO 6 COLUNAS ---
st.subheader("Selecione as Dezenas")
qtd = len(st.session_state.selecionados)
st.write(f"**Selecionados:** {qtd}/60")

# Loop para criar as linhas do volante
for linha in range(10): 
    cols = st.columns(6)
    for coluna in range(6):
        numero = linha * 6 + coluna + 1
        is_sel = numero in st.session_state.selecionados
        
        # Botão renderizado dentro da grade de 6
        if cols[coluna].button(
            f"{numero:02d}", 
            key=f"v_{numero}_{st.session_state.limpar_count}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if is_sel:
                st.session_state.selecionados.remove(numero)
            else:
                st.session_state.selecionados.add(numero)
            st.rerun()

st.divider()

# --- CONFIGURAÇÕES ---
st.markdown('<div class="config-box">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    dez_per_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

st.markdown("### Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máx. Pares", 1, dez_per_jogo, max(1, dez_per_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar", use_container_width=True):
    st.session_state.selecionados = set()
    st.session_state.limpar_count += 1
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- PROCESSAMENTO ---
if gerar:
    st.divider()
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_per_jogo:
        st.error(f"Selecione ao menos {dez_per_jogo} números!")
    else:
        with st.spinner("Gerando..."):
            combos = combinations(lista_n, dez_per_jogo)
            res = []
            for c in combos:
                j = sorted(list(c))
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_fin and len(set(n % 10 for n in j)) == 1: continue
                if f_par:
                    p = len([n for n in j if n % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                res.append(j)
                if len(res) >= qtd_max: break

            st.metric("Jogos", f"{len(res):,}".replace(",", "."))
            st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), 
                             "jogos.csv", "text/csv", use_container_width=True)
