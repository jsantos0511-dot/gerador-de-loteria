import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. Inicialização do Estado (Apenas se não existir)
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'jogos_gerados' not in st.session_state:
    st.session_state.jogos_gerados = None

# 3. CSS para forçar a grade de 6 colunas no iPhone
st.markdown("""
    <style>
    /* Força o container do Streamlit a ser uma grade real */
    div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
    }
    /* Impede o empilhamento em 60 linhas */
    div[data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 !important;
    }
    /* Estilo dos botões do volante */
    .stButton button {
        width: 100% !important;
        height: 45px !important;
        font-weight: bold !important;
        padding: 0 !important;
        font-size: 16px !important;
    }
    /* Proteção para os campos de baixo NÃO ficarem em 6 colunas */
    .config-section div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    /* Ajuste de margens mobile */
    .block-container { padding: 1rem 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro Mobile")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Renderização do Volante
# Criamos 10 linhas de 6 colunas
for r in range(10):
    cols = st.columns(6)
    for c in range(6):
        num = r * 6 + c + 1
        is_sel = num in st.session_state.selecionados
        
        # O segredo: callback direto para não perder o estado
        if cols[c].button(
            f"{num:02d}", 
            key=f"btn_{num}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if num in st.session_state.selecionados:
                st.session_state.selecionados.remove(num)
            else:
                st.session_state.selecionados.add(num)
            st.rerun()

st.divider()

# --- CONFIGURAÇÕES (PROTEGIDAS PELO CSS) ---
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

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- PROCESSAMENTO ---
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

# --- EXIBIÇÃO ---
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
    
    st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), 
                     "jogos.csv", "text/csv", use_container_width=True)
