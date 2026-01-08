import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração inicial - DEVE ser a primeira linha
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. Inicialização Robusta do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# --- LÓGICA DE CLIQUE (PROCESSAMENTO) ---
# O truque aqui é processar antes de renderizar qualquer HTML
params = st.query_params
if "add" in params:
    try:
        num_clicado = int(params["add"])
        # Inverte a seleção
        if num_clicado in st.session_state.selecionados:
            st.session_state.selecionados.remove(num_clicado)
        else:
            st.session_state.selecionados.add(num_clicado)
        
        # IMPORTANTE: Limpa o parâmetro para não entrar em loop, 
        # mas mantém a sessão ativa.
        st.query_params.clear()
        st.rerun()
    except:
        pass

# 3. CSS para a Tabela (Sua estética aprovada)
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.5rem !important; }
    .volante-table {
        width: 100%;
        max-width: 450px;
        border-collapse: separate;
        border-spacing: 5px;
        margin: 10px 0;
    }
    .volante-table td { width: 16.66%; }
    .num-link {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 48px;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        text-decoration: none !important;
        color: #31333f !important;
        font-weight: bold;
        font-size: 18px;
        font-family: sans-serif;
    }
    .num-link:hover { background-color: #e2e4e9; }
    .num-link.selected {
        background-color: #FF4B4B !important;
        color: white !important;
        border-color: #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# 4. Construção da Tabela HTML
html_table = '<table class="volante-table">'
for row in range(10):
    html_table += '<tr>'
    for col in range(6):
        n = row * 6 + col + 1
        sel_class = "selected" if n in st.session_state.selecionados else ""
        # Usamos target="_self" para não abrir nova aba
        html_table += f'<td><a href="?add={n}" target="_self" class="num-link {sel_class}">{n:02d}</a></td>'
    html_table += '</tr>'
html_table += '</table>'

st.markdown(html_table, unsafe_allow_html=True)

st.divider()

# --- 5. CONFIGURAÇÕES E FILTROS ---
with st.container():
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
    max_p = st.slider("Máximo de Pares permitidos", 1, dez_por_jogo, max(1, dez_por_jogo-1))

    col_b1, col_b2 = st.columns(2)
    if col_b1.button("❌ Limpar Tudo", use_container_width=True):
        st.session_state.selecionados = set()
        st.query_params.clear()
        st.rerun()
    
    gerar = col_b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- 6. GERAÇÃO DE JOGOS ---
if gerar:
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error(f"Selecione pelo menos {dez_por_jogo} números no volante!")
    else:
        with st.spinner("Calculando combinações..."):
            combos = combinations(lista_n, dez_por_jogo)
            res = []
            for c in combos:
                j = sorted(list(c))
                # Filtros
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                if f_fin and len(set(n % 10 for n in j)) == 1: continue
                if f_par:
                    p = len([x for x in j if x % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                
                res.append(j)
                if len(res) >= qtd_max: break
            
            if not res:
                st.warning("Nenhum jogo encontrado com esses filtros.")
            else:
                st.success(f"Sucesso! {len(res)} jogos gerados.")
                m1, m2 = st.columns(2)
                m1.metric("Total Jogos", f"{len(res):,}".replace(",", "."))
                m2.metric("Valor Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(res[:500], use_container_width=True)
                
                # Download
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"Bola {x+1}" for x in range(len(res[0]))])
                for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
                
                st.download_button("💾 Baixar Planilha (.csv)", csv_io.getvalue().encode('utf-8-sig'), 
                                 "meus_jogos.csv", "text/csv", use_container_width=True)
