import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 1. Inicialização do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = []

# 2. Lógica de clique via Parâmetros de URL (Query Params)
params = st.query_params
if "add" in params:
    num = int(params["add"])
    if num in st.session_state.selecionados:
        st.session_state.selecionados.remove(num)
    else:
        st.session_state.selecionados.append(num)
    st.query_params.clear()
    st.rerun()

# 3. CSS para a Tabela do Volante
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* A TABELA É IMUTÁVEL */
    .volante-table {
        width: 100%;
        max-width: 400px;
        border-collapse: separate;
        border-spacing: 4px;
        margin: 10px 0;
    }
    .volante-table td {
        width: 16.66%; /* Força 6 colunas exatas */
    }
    .num-link {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 45px;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        text-decoration: none !important;
        color: #31333f !important;
        font-weight: bold;
        font-size: 16px;
        font-family: sans-serif;
    }
    .num-link.selected {
        background-color: #ff4b4b !important;
        color: white !important;
        border-color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# 4. Construção do Volante em HTML (Tabela Rígida)
html_table = '<table class="volante-table">'
for row in range(10):
    html_table += '<tr>'
    for col in range(6):
        n = row * 6 + col + 1
        sel_class = "selected" if n in st.session_state.selecionados else ""
        html_table += f'<td><a href="?add={n}" target="_self" class="num-link {sel_class}">{n:02d}</a></td>'
    html_table += '</tr>'
html_table += '</table>'

st.markdown(html_table, unsafe_allow_html=True)

st.divider()

# --- ÁREA DE CONFIGURAÇÕES (Protegida) ---
# Usamos o container para isolar os componentes nativos
with st.container():
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
    if b1.button("❌ Limpar Seleção", use_container_width=True):
        st.session_state.selecionados = []
        st.rerun()
    gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# 5. Processamento e Resultados
if gerar:
    lista_n = sorted(st.session_state.selecionados)
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
            m1.metric("Total Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Valor Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(len(res[0]) if res else 6)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
