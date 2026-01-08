import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração de página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. Inicialização do Estado (Apenas se não existir)
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# 3. CSS "BLINDADO" PARA MOBILE
# Esta regra ignora as colunas do Streamlit e cria sua própria grade
st.markdown("""
    <style>
    /* Força o container do volante a ser uma grade de 6 */
    .volante-grid div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 5px !important;
    }
    
    /* Impede que o Streamlit force 100% de largura nas colunas */
    .volante-grid div[data-testid="column"] {
        width: 100% !important;
        flex: 1 !important;
        min-width: 0 !important;
    }

    /* Estilização dos botões para ficarem fáceis de tocar no celular */
    .stButton > button {
        width: 100% !important;
        height: 45px !important;
        font-weight: bold !important;
        padding: 0 !important;
        font-size: 16px !important;
    }

    /* Ajuste para que o resto da página (filtros/resultados) fique normal */
    .conteudo-normal div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    
    .block-container { padding: 1rem 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Criamos o volante dentro de uma DIV específica para aplicar o CSS de 6 colunas
st.markdown('<div class="volante-grid">', unsafe_allow_html=True)

# Lógica de 10 linhas e 6 colunas
for r in range(10):
    cols = st.columns(6)
    for c in range(6):
        num = r * 6 + c + 1
        is_sel = num in st.session_state.selecionados
        
        # O botão nativo do Streamlit mantém o estado perfeitamente
        if cols[c].button(
            f"{num:02d}", 
            key=f"v_{num}", 
            type="primary" if is_sel else "secondary"
        ):
            if is_sel:
                st.session_state.selecionados.remove(num)
            else:
                st.session_state.selecionados.add(num)
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- ÁREA DE CONFIGURAÇÃO (PROTEGIDA) ---
st.markdown('<div class="conteudo-normal">', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas por jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Máxima de Jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
f_seq = st.checkbox("🚫 Sem números sequenciais", True)
f_fin = st.checkbox("🚫 Sem finais iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Pares/Ímpares", True)
max_p = st.slider("Máximo de Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar Tudo", use_container_width=True):
    st.session_state.selecionados = set()
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- PROCESSAMENTO E RESULTADOS ---
if gerar:
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error(f"Selecione ao menos {dez_por_jogo} números!")
    else:
        with st.spinner("Gerando combinações..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                j = sorted(list(c))
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_fin and len(set(n % 10 for n in j)) == 1: continue
                if f_par:
                    p = len([x for x in j if x % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                res.append(j)
                if len(res) >= qtd_max: break
            
            if res:
                st.success(f"{len(res)} jogos gerados!")
                m1, m2 = st.columns(2)
                m1.metric("Total Jogos", f"{len(res):,}".replace(",", "."))
                m2.metric("Valor Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.dataframe(res[:500], use_container_width=True)
                
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"B{x+1}" for x in range(len(res[0]))])
                for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
                st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
