import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 1. CSS "BRUTO" - Força a grade e anula o empilhamento automático do Streamlit
st.markdown("""
    <style>
    /* Reset de margens mobile */
    .block-container { padding: 1rem 0.5rem !important; }

    /* Alvo: O container que segura os botões */
    /* Usamos um seletor de atributo para pegar apenas o container do volante */
    div[data-testid="stVerticalBlock"] > div.element-container:has(#volante-marcador) + div {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
    }

    /* FORÇA cada coluna a manter 1/6 da largura, proibindo o empilhamento */
    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 100% !important;
    }

    /* Estilo dos botões */
    button {
        height: 45px !important;
        padding: 0px !important;
        font-weight: bold !important;
    }

    /* Estilo para as métricas e configurações (ZONA PROTEGIDA) */
    .config-area div[data-testid="column"] {
        flex: 1 1 50% !important; /* Mantém 2 colunas nas configurações */
        min-width: 120px !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'jogos_gerados' not in st.session_state:
    st.session_state.jogos_gerados = None

st.title("🎰 Gerador Pro")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Marcador invisível para o CSS localizar onde começa o volante
st.markdown('<div id="volante-marcador"></div>', unsafe_allow_html=True)

# Criamos as linhas. Para garantir que o Streamlit não tente ser "esperto",
# vamos manter a estrutura de colunas, mas o CSS acima vai travar o layout.
for r in range(10):
    cols = st.columns(6)
    for c in range(6):
        num = r * 6 + c + 1
        is_sel = num in st.session_state.selecionados
        if cols[c].button(f"{num:02d}", key=f"v_{num}", type="primary" if is_sel else "secondary"):
            if is_sel: st.session_state.selecionados.remove(num)
            else: st.session_state.selecionados.add(num)
            st.rerun()

st.divider()

# --- CONFIGURAÇÕES (ZONA PROTEGIDA PELO CSS) ---
st.markdown('<div class="config-area">', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas por jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

st.markdown("### Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máximo de Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar", use_container_width=True):
    st.session_state.selecionados = set()
    st.session_state.jogos_gerados = None
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

if gerar:
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error(f"Selecione ao menos {dez_por_jogo} números!")
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
            st.session_state.jogos_gerados = (res, len(res) * valor_unit)

if st.session_state.jogos_gerados:
    res, custo = st.session_state.jogos_gerados
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
    m2.metric("Total", f"R$ {custo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(res[:500], use_container_width=True)
    
    csv_io = io.StringIO()
    csv_io.write('\ufeff')
    w = csv.writer(csv_io, delimiter=';')
    w.writerow(["Jogo"] + [f"B{x+1}" for x in range(len(res[0]))])
    for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
    st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
