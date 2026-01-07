import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Mobile", layout="wide")

# 2. CSS para Forçar 6 Colunas no Celular e Desktop
st.markdown("""
    <style>
    /* Força o container de botões a ser uma grade de 6 colunas */
    div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
    }
    /* Garante que as colunas ocupem o espaço total sem empilhar */
    div[data-testid="column"] {
        width: 100% !important;
        min-width: unset !important;
        flex: unset !important;
    }
    /* Estilo dos botões: Proporção ideal para 6 colunas */
    button {
        height: 42px !important;
        font-size: 15px !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    /* Área de configuração: Volta ao layout normal (2 colunas) */
    .config-box div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Pro (6 Colunas)")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
qtd = len(st.session_state.selecionados)
st.progress(qtd / 60)
st.write(f"**Selecionados:** {qtd}/60")

# Gerando o volante com 6 colunas (10 linhas de 6)
for linha in range(10): 
    cols = st.columns(6)
    for coluna in range(6):
        numero = linha * 6 + coluna + 1
        is_sel = numero in st.session_state.selecionados
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
    valor_unit = st.number_input("Preço Jogo R$", 0.0, 500.0, 5.0)
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
        with st.spinner("Gerando jogos..."):
            combos = combinations(lista_n, dez_per_jogo)
            res = []
            for c in combos:
                j = sorted(list(c))
                # Filtros
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_fin and len(set(n % 10 for n in j)) == 1: continue
                if f_par:
                    p = len([n for n in j if n % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                
                res.append(j)
                if len(res) >= qtd_max: break

            # Resultados Financeiros
            m1, m2 = st.columns(2)
            m1.metric("Total de Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Custo Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            # Tabela de Visualização
            st.dataframe(res[:500], use_container_width=True)
            
            # CSV para Download
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_per_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), 
                             "jogos_gerados.csv", "text/csv", use_container_width=True)
