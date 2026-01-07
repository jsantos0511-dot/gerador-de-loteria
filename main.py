import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. CSS Direcionado (Apenas para o Volante)
st.markdown("""
    <style>
    /* Estilo exclusivo para o container do Volante */
    .volante-grid div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 4px !important;
        width: 100% !important;
    }

    /* Garante que colunas dentro do volante não estiquem */
    .volante-grid div[data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 !important;
    }

    /* Botões do volante mais anatômicos para o dedo */
    .volante-grid button {
        height: 42px !important;
        font-size: 14px !important;
        font-weight: bold !important;
    }

    /* Mantém o restante do app (fora do volante) com layout original */
    div[data-testid="stVerticalBlock"] > div.stButton button {
        height: auto;
    }
    
    .block-container {
        padding: 1rem 0.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Pro")

# --- ÁREA DO VOLANTE (PROTEGIDA PELA CLASSE CSS) ---
st.subheader("Selecione as Dezenas")
qtd = len(st.session_state.selecionados)
st.write(f"**Selecionados:** {qtd}/60")

st.markdown('<div class="volante-grid">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- ÁREA DE CONFIGURAÇÕES (LAYOUT PADRÃO VOLTOU) ---
col_config1, col_config2 = st.columns(2)
with col_config1:
    dez_per_jogo = st.number_input("Dezenas por jogo", 1, 20, 6)
    valor_unit = st.number_input("Valor da aposta (R$)", 0.0, 500.0, 5.0)
with col_config2:
    gerar_tudo = st.checkbox("Gerar TODAS as combinações")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Limite de jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
f_seq = st.checkbox("🚫 Remover Sequências", True)
f_fin = st.checkbox("🚫 Remover Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máximo de Pares permitidos", 1, dez_per_jogo, max(1, dez_per_jogo-1))

# Botões de Ação
c_btn1, c_btn2 = st.columns(2)
with c_btn1:
    if st.button("❌ Limpar Seleção", use_container_width=True):
        st.session_state.selecionados = set()
        st.session_state.limpar_count += 1
        st.rerun()
with c_btn2:
    gerar = st.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- RESULTADOS ---
if gerar:
    st.divider()
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_per_jogo:
        st.error(f"⚠️ Seleção insuficiente! Escolha pelo menos {dez_per_jogo} números.")
    else:
        with st.spinner("Processando..."):
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

            # Métricas
            m1, m2 = st.columns(2)
            m1.metric("Total de Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Investimento", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(res[:500], use_container_width=True)
            
            # Exportação
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_per_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            
            st.download_button("💾 Baixar Planilha CSV/Excel", csv_io.getvalue().encode('utf-8-sig'), 
                             "meus_jogos.csv", "text/csv", use_container_width=True)
