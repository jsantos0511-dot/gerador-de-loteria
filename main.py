import streamlit as st
import csv
from itertools import combinations
import io
import random

# 1. Configuração da Página
st.set_page_config(page_title="Loteria Mobile", layout="centered")

# 2. Inicialização do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# --- LÓGICA DE CAPTURA DE CLIQUE ---
# Captura o número clicado via parâmetro na URL para evitar o empilhamento dos botões nativos
params = st.query_params
if "n" in params:
    n_clicado = int(params["n"])
    if n_clicado in st.session_state.selecionados:
        st.session_state.selecionados.remove(n_clicado)
    else:
        st.session_state.selecionados.add(n_clicado)
    st.query_params.clear() # Limpa a URL
    st.rerun()

# 3. CSS para o Volante Flexível (Chips)
st.markdown("""
    <style>
    /* Container que agrupa os números sem empilhar */
    .volante-container {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        justify-content: center !important;
        padding: 10px 0 !important;
    }
    
    /* Estilo dos botões (Chips) */
    .chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 45px !important;
        height: 45px !important;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        border-radius: 50%;
        text-decoration: none !important;
        color: #31333f !important;
        font-weight: bold;
        font-size: 16px;
        transition: 0.2s;
    }
    
    .chip:active { transform: scale(0.9); }
    
    .chip.selected {
        background-color: #FF4B4B !important;
        color: white !important;
        border-color: #FF4B4B;
    }
    
    .block-container { padding: 1rem 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro Mobile")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Botões de Ações Rápidas
c1, c2 = st.columns(2)
with c1:
    if st.button("🎲 Surpresinha", use_container_width=True):
        st.session_state.selecionados = set(random.sample(range(1, 61), 6))
        st.rerun()
with c2:
    if st.button("❌ Limpar Tudo", use_container_width=True):
        st.session_state.selecionados = set()
        st.rerun()

# --- RENDERIZAÇÃO DO VOLANTE HTML ---
# Criamos os botões manualmente em HTML para o Streamlit não conseguir empilhá-los
html_volante = '<div class="volante-container">'
for i in range(1, 61):
    clase = "chip selected" if i in st.session_state.selecionados else "chip"
    # O link redireciona para a própria página com o número no parâmetro ?n=
    html_volante += f'<a href="?n={i}" target="_self" class="{clase}">{i:02d}</a>'
html_volante += '</div>'

st.markdown(html_volante, unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES E FILTROS ---
with st.container():
    col_a, col_b = st.columns(2)
    with col_a:
        dez_por_jogo = st.number_input("Dezenas por jogo", 6, 20, 6)
        valor_unit = st.number_input("Valor R$", 0.0, 500.0, 5.0)
    with col_b:
        qtd_max = st.number_input("Limite de jogos", 1, 1000000, 100)
        gerar_tudo = st.checkbox("Gerar todas")

    with st.expander("🛠️ Filtros Avançados"):
        f_seq = st.checkbox("🚫 Sem Sequências", True)
        f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
        max_p = st.slider("Máximo de Pares", 1, dez_por_jogo, dez_por_jogo//2 + 1)

    if st.button("🚀 GERAR JOGOS", type="primary", use_container_width=True):
        lista_n = sorted(list(st.session_state.selecionados))
        if len(lista_n) < dez_por_jogo:
            st.error(f"Escolha ao menos {dez_por_jogo} números!")
        else:
            with st.spinner("Gerando..."):
                limite = 1000000 if gerar_tudo else qtd_max
                combos = combinations(lista_n, dez_por_jogo)
                res = []
                for c in combos:
                    j = list(c)
                    if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                    if f_par:
                        p = len([n for n in j if n % 2 == 0])
                        if p > max_p or (len(j)-p) > max_p: continue
                    res.append(j)
                    if len(res) >= limite: break
                
                if res:
                    st.success(f"{len(res)} jogos gerados!")
                    st.metric("Investimento", f"R$ {len(res)*valor_unit:,.2f}")
                    st.dataframe(res, use_container_width=True)
                    
                    csv_io = io.StringIO()
                    csv_io.write('\ufeff')
                    w = csv.writer(csv_io, delimiter=';')
                    w.writerow(["Jogo"] + [f"D{x+1}" for x in range(dez_por_jogo)])
                    for idx, r in enumerate(res):
                        w.writerow([idx+1] + [f"{n:02d}" for n in r])
                    
                    st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
