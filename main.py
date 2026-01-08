import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. CSS Blindado para Mobile
st.markdown("""
    <style>
    /* Reset de margens para mobile */
    .block-container { padding: 1rem 0.5rem !important; }

    /* FORÇAR GRADE: Criamos uma regra que ataca o container do volante sem erro */
    [data-testid="stHorizontalBlock"].volante-container {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
    }
    
    /* Impede o empilhamento das colunas individuais */
    [data-testid="stHorizontalBlock"].volante-container [data-testid="column"] {
        width: 100% !important;
        flex: 1 !important;
        min-width: 0 !important;
    }

    /* Estilo dos botões */
    .stButton > button {
        width: 20% !important;
        height: 60px !important;
        padding: 0 !important;
        font-weight: bold !important;
        font-size: 12px !important;
    }

    /* Garante que os campos de baixo NÃO herdem a grade de 6 */
    .config-area [data-testid="stHorizontalBlock"] {
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

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# O segredo: Injetamos um marcador HTML antes de cada linha para o CSS "pegar"
for r in range(10):
    # Esta div vazia ajuda o Streamlit a agrupar as colunas, 
    # e o CSS acima força a grade.
    st.markdown('<div class="volante-container">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES E FILTROS ---
st.markdown('<div class="config-area">', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
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

# --- RESULTADOS ---
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
                if len(res) >= qtd_max: break

            m1, m2 = st.columns(2)
            m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B1", "B2", "B3", "B4", "B5", "B6"][:dez_por_jogo])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
