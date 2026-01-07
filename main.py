import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. O SEGREDO: CSS que o Safari não pode ignorar
st.markdown("""
    <style>
    /* Força o container de colunas a ser uma GRADE de 6 */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 4px !important;
    }
    
    /* Impede o Streamlit de empilhar em 1 linha (o erro das 60 linhas) */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }

    /* Botões do volante */
    .stButton > button {
        width: 100% !important;
        height: 42px !important;
        padding: 0px !important;
        font-size: 14px !important;
        font-weight: bold !important;
    }

    /* Ajuste para as CONFIGURAÇÕES (para elas não ficarem em 6 colunas) */
    .config-area [data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    
    .block-container {
        padding: 1rem 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Pro")

# --- VOLANTE (PROTEGIDO) ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Gerando o volante
for r in range(10):
    cols = st.columns(6)
    for c in range(6):
        num = r * 6 + c + 1
        is_sel = num in st.session_state.selecionados
        if cols[c].button(
            f"{num:02d}", 
            key=f"v_{num}_{st.session_state.limpar_count}",
            type="primary" if is_sel else "secondary"
        ):
            if is_sel: st.session_state.selecionados.remove(num)
            else: st.session_state.selecionados.add(num)
            st.rerun()

st.divider()

# --- CONFIGURAÇÃO (VOLTA AO NORMAL) ---
st.markdown('<div class="config-area">', unsafe_allow_html=True)

col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with col_cfg2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

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
gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- GERAÇÃO ---
if gerar:
    st.divider()
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
                if len(res) >= qtd_max: break

            st.metric("Jogos", f"{len(res):,}".replace(",", "."))
            st.metric("Custo", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
