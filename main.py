import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 1. ESTADO DA SESSÃO
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# 2. LÓGICA DE CLIQUE (Via Query Params para evitar refresh que limpa tudo)
query_params = st.query_params
if "n" in query_params:
    num = int(query_params["n"])
    if num in st.session_state.selecionados:
        st.session_state.selecionados.remove(num)
    else:
        st.session_state.selecionados.add(num)
    st.query_params.clear()
    st.rerun()

# 3. CSS PARA O VOLANTE E PARA PROTEGER OS BOTÕES NATIVOS
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* GRADE DO VOLANTE - TOTALMENTE MANUAL */
    .grid-volante {
        display: grid !important;
        grid-template-columns: repeat(6, 40px) !important;
        gap: 6px !important;
        justify-content: center;
        margin-bottom: 20px;
    }
    
    /* ESTILO DOS BOTÕES DO VOLANTE */
    .btn-num {
        width: 40px !important;
        height: 30px !important;
        display: flex !important;
        align-items: center;
        justify-content: center;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        text-decoration: none !important;
        color: #31333f !important;
        font-size: 15px !important;
        font-weight: bold;
    }
    
    .btn-num.active {
        background-color: #ff4b4b !important;
        color: white !important;
        border-color: #ff4b4b;
    }

    /* PROTEÇÃO: Garante que os botões nativos do Streamlit NÃO sejam afetados pela grade */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")

# --- VOLANTE (HTML PURO) ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Construindo a grade de 6x10 em HTML
volante_html = '<div class="grid-volante">'
for i in range(1, 61):
    clase = "btn-num active" if i in st.session_state.selecionados else "btn-num"
    volante_html += f'<a href="?n={i}" target="_self" class="{clase}">{i:02d}</a>'
volante_html += '</div>'

st.markdown(volante_html, unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES E FILTROS (COMPONENTES NATIVOS) ---
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
if b1.button("❌ Limpar Seleção", use_container_width=True):
    st.session_state.selecionados = set()
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

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

            st.divider()
            m1, m2 = st.columns(2)
            m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
