import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# --- ESTADO DA SESSÃO ---
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'jogos_gerados' not in st.session_state:
    st.session_state.jogos_gerados = None

# --- LÓGICA DE CLIQUE VIA URL (SEM REFRESH VISÍVEL) ---
params = st.query_params
if "num" in params:
    n = int(params["num"])
    if n in st.session_state.selecionados:
        st.session_state.selecionados.remove(n)
    else:
        st.session_state.selecionados.add(n)
    st.query_params.clear()
    st.rerun()

st.title("🎰 Gerador Pro Mobile")

# --- CSS PARA FORÇAR 6 COLUNAS (BLINDADO) ---
st.markdown("""
    <style>
    /* Grade de 6 colunas fixa para o volante */
    .volante-wrapper {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 6px;
        width: 100%;
        max-width: 450px;
        margin: 10px 0;
    }
    /* Estilo dos números (Links com cara de Botão) */
    .btn-num {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 45px;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        text-decoration: none !important;
        color: #31333f !important;
        font-weight: bold;
        font-size: 16px;
    }
    .btn-num:active { background-color: #e0e2e6; }
    .btn-num.selected {
        background-color: #ff4b4b !important;
        color: white !important;
        border-color: #ff4b4b;
    }
    /* Proteção para os campos de baixo não ficarem em 6 colunas */
    .config-section div[data-testid="stHorizontalBlock"] {
        display: flex !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- RENDERIZAÇÃO DO VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Construção do HTML do Volante
volante_html = '<div class="volante-wrapper">'
for i in range(1, 61):
    css_class = "btn-num selected" if i in st.session_state.selecionados else "btn-num"
    volante_html += f'<a href="?num={i}" target="_self" class="{css_class}">{i:02d}</a>'
volante_html += '</div>'

st.markdown(volante_html, unsafe_allow_html=True)

st.divider()

# --- ÁREA DE CONFIGURAÇÃO (PROTEGIDA) ---
st.markdown('<div class="config-section">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Limite Jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar Tudo", use_container_width=True):
    st.session_state.selecionados = set()
    st.session_state.jogos_gerados = None
    st.rerun()

if b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True):
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
            st.session_state.jogos_gerados = (res, len(res) * valor_unit)
st.markdown('</div>', unsafe_allow_html=True)

# --- EXIBIÇÃO DOS RESULTADOS (PERSISTENTE AO ROLAR) ---
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
    
    st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
