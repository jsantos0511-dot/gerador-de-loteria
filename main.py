import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# --- ESTADO DA SESSÃO (PERSISTENTE) ---
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'jogos_gerados' not in st.session_state:
    st.session_state.jogos_gerados = None
if 'custo_total' not in st.session_state:
    st.session_state.custo_total = 0

# --- FUNÇÃO DE CALLBACK PARA O CLIQUE ---
def processar_clique(n):
    if n in st.session_state.selecionados:
        st.session_state.selecionados.remove(n)
    else:
        st.session_state.selecionados.add(n)

st.title("🎰 Gerador Pro Mobile")

# --- VISUAL DO VOLANTE (HTML + CSS) ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# CSS para forçar 6 colunas e botões bonitos
st.markdown("""
    <style>
    .volante-container {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 6px;
        width: 100%;
        max-width: 400px;
        margin-bottom: 20px;
    }
    .stButton > button {
        width: 100% !important;
        height: 45px !important;
        font-weight: bold !important;
        padding: 0 !important;
    }
    /* Estilo para as métricas não quebrarem */
    [data-testid="stMetric"] {
        background: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Renderização do Volante usando colunas do Streamlit dentro de uma div
# O segredo é que o st.button nativo não faz refresh na página inteira
with st.container():
    for r in range(10):
        cols = st.columns(6)
        for c in range(6):
            num = r * 6 + c + 1
            is_sel = num in st.session_state.selecionados
            # O botão do Streamlit preserva o estado sem recarregar a URL
            if cols[c].button(
                f"{num:02d}", 
                key=f"v_{num}",
                type="primary" if is_sel else "secondary",
                use_container_width=True
            ):
                processar_clique(num)
                st.rerun()

st.divider()

# --- CONFIGURAÇÕES ---
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

col_b1, col_b2 = st.columns(2)
if col_b1.button("❌ Limpar Tudo", use_container_width=True):
    st.session_state.selecionados = set()
    st.session_state.jogos_gerados = None
    st.rerun()

# Botão de Gerar
if col_b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True):
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
            
            # Salva no estado para não sumir ao rolar a tela
            st.session_state.jogos_gerados = res
            st.session_state.custo_total = len(res) * valor_unit

# --- EXIBIÇÃO DOS RESULTADOS (PERSISTENTE) ---
if st.session_state.jogos_gerados is not None:
    st.divider()
    res = st.session_state.jogos_gerados
    
    m1, m2 = st.columns(2)
    m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
    m2.metric("Total", f"R$ {st.session_state.custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.dataframe(res[:500], use_container_width=True)
    
    csv_io = io.StringIO()
    csv_io.write('\ufeff')
    w = csv.writer(csv_io, delimiter=';')
    w.writerow(["Jogo"] + [f"B{x+1}" for x in range(len(res[0]) if res else 6)])
    for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
    
    st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
