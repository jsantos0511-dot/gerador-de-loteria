import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 1. CSS "ULTIMATUM" - Força 5 colunas e ignora as travas do Streamlit
st.markdown("""
    <style>
    /* Ajuste de margens do app */
    .block-container { padding: 1rem 0.5rem !important; }

    /* Alvo: O container de colunas do Streamlit */
    /* Forçamos a grade de 5 colunas independente do tamanho da tela */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(5, 1fr) !important; /* TESTE COM 5 COLUNAS */
        gap: 6px !important;
    }

    /* Impede cada coluna de virar 'bloco' (empilhar) */
    [data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 !important;
    }

    /* Estilo dos botões do volante */
    .stButton button {
        height: 50px !important;
        width: 100% !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 0px !important;
    }

    /* ZONA PROTEGIDA: Faz o restante do app ignorar a grade de 5 */
    .config-area [data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    
    .config-area [data-testid="column"] {
        flex: 1 1 50% !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'jogos_gerados' not in st.session_state:
    st.session_state.jogos_gerados = None

st.title("🎰 Gerador Pro")

# --- VOLANTE (Agora com lógica de 5 colunas) ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Renderizamos 12 linhas de 5 colunas (12 * 5 = 60)
for r in range(12):
    cols = st.columns(5)
    for c in range(5):
        num = r * 5 + c + 1
        is_sel = num in st.session_state.selecionados
        if cols[c].button(f"{num:02d}", key=f"v_{num}", type="primary" if is_sel else "secondary"):
            if is_sel: st.session_state.selecionados.remove(num)
            else: st.session_state.selecionados.add(num)
            st.rerun()

st.divider()

# --- CONFIGURAÇÕES (Limpas e sem grade de 5) ---
st.markdown('<div class="config-area">', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    dez_per_jogo = st.number_input("Dezenas por jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

st.markdown("### Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máximo de Pares", 1, dez_per_jogo, max(1, dez_per_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar Seleção", use_container_width=True):
    st.session_state.selecionados = set()
    st.session_state.jogos_gerados = None
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

if gerar:
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
            st.session_state.jogos_gerados = (res, len(res) * valor_unit)

if st.session_state.jogos_gerados:
    res, custo = st.session_state.jogos_gerados
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric("Total Jogos", f"{len(res):,}".replace(",", "."))
    m2.metric("Valor Total", f"R$ {custo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(res[:500], use_container_width=True)
    
    csv_io = io.StringIO()
    csv_io.write('\ufeff')
    w = csv.writer(csv_io, delimiter=';')
    w.writerow(["Jogo"] + [f"B{x+1}" for x in range(len(res[0]))])
    for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
    st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
