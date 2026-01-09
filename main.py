import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES ---
TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5}
}

# --- NAVEGAÇÃO VIA QUERY PARAMS ---
params = st.query_params
if "escolha" in params:
    st.session_state.pagina = params["escolha"]

if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

# 2. CSS PARA O MENU DE CARDS E VOLANTE
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    
    /* Estilização dos Cards da Home */
    .card-container {{
        border: 2px solid var(--cor-loteria);
        border-radius: 20px;
        padding: 30px 20px;
        text-align: center;
        background-color: #161b22;
        transition: all 0.3s ease;
        cursor: pointer;
        text-decoration: none !important;
        display: block;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .card-container:hover {{
        transform: translateY(-5px);
        box-shadow: 0 0 20px var(--cor-loteria);
        background-color: #1c2128;
    }}
    .card-icon {{ font-size: 40px; margin-bottom: 10px; }}
    .card-title {{ font-size: 22px; font-weight: bold; color: var(--cor-loteria); }}

    /* Estilo do Volante (Segmented Control) */
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({cols_v}, 1fr) !important;
        gap: 5px !important;
    }}

    [data-testid="stSidebar"] {{ display: none; }}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE FILTRO ---
def aplicar_filtros(combos, f_seq, f_finais, f_par, max_p, dez_jogo, limite, gerar_tudo):
    res = []
    for c in combos:
        jogo = list(c)
        if f_seq and any(jogo[i+1] == jogo[i]+1 for i in range(len(jogo)-1)): continue
        if f_finais:
            finais = [n % 10 for n in jogo]
            if any(finais.count(f) > 4 for f in finais): continue
        if f_par:
            p = len([n for n in jogo if n % 2 == 0])
            if p > max_p or (dez_jogo - p) > max_p: continue
        res.append(jogo)
        if not gerar_tudo and len(res) >= limite: break
    return res

# --- PÁGINAS ---

def home():
    st.markdown('<h1 style="text-align:center; margin-bottom:40px;">🍀 Portal de Loterias</h1>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        card_html = f"""
        <a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados['cor']};">
            <div class="card-icon">🍀</div>
            <div class="card-title">{nome}</div>
        </a>
        """
        alvo.markdown(card_html, unsafe_allow_html=True)

def gerador_loteria(nome, config):
    # Cabeçalho da Página da Loteria
    col_voltar, col_titulo = st.columns([1, 4])
    with col_voltar:
        if st.button("⬅️ Menu", use_container_width=True):
            st.query_params.clear()
            st.session_state.pagina = "Início"
            st.rerun()
    with col_titulo:
        st.markdown(f'<h2 style="color:{config["cor"]}; margin:0;">🍀 {nome}</h2>', unsafe_allow_html=True)

    st.divider()
    
    # --- VOLANTE E SELEÇÃO ---
    key_sel = f"sel_{nome}"
    if key_sel not in st.session_state: st.session_state[key_sel] = []
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Surpresinha", use_container_width=True):
            st.session_state[key_sel] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
    with c2:
        if st.button("❌ Limpar Seleção", use_container_width=True):
            st.session_state[key_sel] = []
            st.rerun()

    opcoes = [f"{i:02d}" for i in range(1, config['total'] + 1)]
    selecionados = st.segmented_control("V", options=opcoes, selection_mode="multi", key=key_sel, label_visibility="collapsed")
    
    st.info(f"**{len(selecionados)}** números selecionados no volante.")

    # --- CONFIGURAÇÕES TÉCNICAS ---
    st.subheader("⚙️ Configurações da Aposta")
    col_a, col_b = st.columns(2)
    with col_a:
        dez_por_jogo = st.number_input("Dezenas por jogo", config['min_sel'], config['total'], config['min_sel'])
        valor_unit = st.number_input("Preço da aposta (R$)", 0.0, 5000.0, config['preco'])
    with col_b:
        gerar_tudo = st.checkbox("Gerar todas as combinações")
        qtd_max = st.number_input("Limite de jogos", 1, 1000000, 100, disabled=gerar_tudo)

    # --- FILTROS ---
    with st.expander("🛠️ Filtros Avançados"):
        f_s = st.checkbox("🚫 Evitar Sequências (ex: 01-02-03)")
        f_f = st.checkbox("🚫 Limitar Finais Iguais (máx 4)")
        f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
        m_p = st.slider("Quantidade de Pares permitida", 0, dez_por_jogo, dez_por_jogo // 2) if f_p else dez_por_jogo

    # --- PROCESSAMENTO ---
    if st.button(f"🚀 GERAR JOGOS PARA {nome.upper()}", type="primary", use_container_width=True):
        if len(selecionados) < dez_por_jogo:
            st.error(f"Selecione pelo menos {dez_por_jogo} números no volante para gerar apostas de {dez_por_jogo} dezenas!")
        else:
            lista_n = sorted([int(x) for x in selecionados])
            with st.spinner("Calculando combinações..."):
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                
                if res:
                    st.success(f"Sucesso! {len(res)} jogos gerados.")
                    st.metric("Investimento Total", f"R$ {len(res)*valor_unit:,.2f}")
                    
                    df = pd.DataFrame(res, columns=[f"D{i+1}" for i in range(dez_por_jogo)])
                    st.dataframe(df, use_container_width=True)
                    
                    # Preparação do CSV
                    csv_io = io.StringIO()
                    csv_io.write('\ufeff') # UTF-8 BOM para Excel
                    w = csv.writer(csv_io, delimiter=';')
                    w.writerow(["ID"] + [f"D{i+1}" for i in range(dez_por_jogo)])
                    for idx, r in enumerate(res):
                        w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                    
                    st.download_button(
                        label="💾 Baixar Resultados em CSV",
                        data=csv_io.getvalue().encode('utf-8-sig'),
                        file_name=f"jogos_{nome.lower()}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("Nenhum jogo atendeu aos filtros selecionados. Tente relaxar as restrições.")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
