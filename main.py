import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# --- 1. MEMÓRIA RESISTENTE ---
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'jogos_gerados' not in st.session_state:
    st.session_state.jogos_gerados = None

# --- 2. LÓGICA DE CLIQUE (SEM REFRESH DE URL) ---
# Usamos um componente oculto para capturar cliques do HTML
def alterar_numero(n):
    if n in st.session_state.selecionados:
        st.session_state.selecionados.remove(n)
    else:
        st.session_state.selecionados.add(n)

# --- 3. CSS "PIXEL PERFEITO" ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* Grade Fixa de 6 colunas que NÃO empilha */
    .volante-wrapper {
        display: grid !important;
        grid-template-columns: repeat(6, 40px) !important;
        gap: 6px !important;
        justify-content: center;
        margin: 15px auto;
    }

    /* Estilo exato solicitado: 40x30px, fonte 15px */
    .num-box {
        width: 40px !important;
        height: 30px !important;
        font-size: 15px !important;
        font-weight: bold;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        background-color: #f0f2f6;
        color: #31333f;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: 0.2s;
    }
    
    .num-box.active {
        background-color: #ff4b4b !important;
        color: white !important;
        border-color: #ff4b4b;
    }
    
    /* Ajuste para os botões nativos de baixo não herdarem a grade */
    .stButton button {
        height: 45px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")

# --- 4. VOLANTE COM COMPONENTES NATIVOS (PARA GARANTIR SELEÇÃO) ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Criamos a grade usando st.columns mas TRAVAMOS o tamanho no CSS
# Usar o st.button nativo aqui é o único jeito de garantir que a sessão não morra
for r in range(10):
    st.markdown('<div class="volante-wrapper">', unsafe_allow_html=True)
    cols = st.columns(6)
    for c in range(6):
        num = r * 6 + c + 1
        is_sel = num in st.session_state.selecionados
        # O botão do Streamlit é o único que garante a persistência do set()
        if cols[c].button(f"{num:02d}", key=f"btn_{num}", type="primary" if is_sel else "secondary"):
            alterar_numero(num)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 5. CONFIGURAÇÕES E FILTROS ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
        valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
    with col2:
        gerar_tudo = st.checkbox("Gerar Todas")
        qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

    st.markdown("### Filtros")
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
                st.session_state.jogos_gerados = (res, len(res) * valor_unit)

# --- 6. EXIBIÇÃO DOS RESULTADOS ---
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
