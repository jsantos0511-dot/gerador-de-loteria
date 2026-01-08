import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES ---
TEMAS = {
    "Mega-Sena": {"cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0},
    "Lotofácil": {"cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0},
    "Quina": {"cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5},
    "Lotomania": {"cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0},
    "Dupla Sena": {"cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5}
}

# --- CONTROLE DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

# 2. CSS DINÂMICO (DARK MODE + CARDS COLORIDOS)
estilos_cards = ""
for nome, dados in TEMAS.items():
    estilos_cards += f"""
    /* Formata o botão para parecer um Card */
    div[data-testid="stButton"] button[key="btn_{nome}"] {{
        height: 120px !important;
        background-color: #0e1117 !important;
        border: 2px solid {dados['cor']} !important;
        color: {dados['cor']} !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        font-size: 24px !important;
        margin-bottom: 20px !important;
        transition: 0.3s !important;
    }}
    /* Efeito ao passar o mouse */
    div[data-testid="stButton"] button[key="btn_{nome}"]:hover {{
        background-color: {dados['cor']}20 !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
        transform: translateY(-3px) !important;
    }}
    """

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    .titulo-custom {{ color: {cor_tema}; font-size: 2.2rem; font-weight: bold; text-align: center; margin-bottom: 25px; }}
    
    /* Injeção dos estilos dos botões-cards */
    {estilos_cards}

    /* Estilo do Volante (Segmented Control) */
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({cols_v}, 1fr) !important;
        gap: 4px !important;
    }}
    
    [data-testid="stSidebar"] {{ display: none; }}
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
    st.markdown('<div class="titulo-custom">🍀 Portal de Loterias</div>', unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        with alvo:
            # O próprio botão agora é o Card. O texto é apenas o Nome.
            # O trevo 🍀 é opcional, deixei dentro do nome para manter o estilo
            if st.button(f"🍀 {nome}", key=f"btn_{nome}", use_container_width=True):
                st.session_state.pagina = nome
                st.rerun()

def gerador_loteria(nome, config):
    if st.button("⬅️ Menu Principal", use_container_width=True):
        st.session_state.pagina = "Início"
        st.rerun()

    st.markdown(f'<div class="titulo-custom">🍀 {nome}</div>', unsafe_allow_html=True)
    
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
    
    st.info(f"**{len(selecionados)}** números selecionados")

    col_a, col_b = st.columns(2)
    with col_a:
        dez_por_jogo = st.number_input("Dezenas por jogo", config['min_sel'], config['total'], config['min_sel'])
        valor_unit = st.number_input("Valor da aposta R$", 0.0, 5000.0, config['preco'])
    with col_b:
        gerar_tudo = st.checkbox("Gerar TODAS possíveis")
        qtd_max = st.number_input("Limite de jogos", 1, 1000000, 100, disabled=gerar_tudo)

    with st.expander("🛠️ Filtros Inteligentes"):
        f_s = st.checkbox("🚫 Evitar Sequências")
        f_f = st.checkbox("🚫 Evitar Finais Repetidos")
        f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
        m_p = st.slider("Máximo de Pares", 0, dez_por_jogo, dez_por_jogo // 2) if f_p else dez_por_jogo

    if st.button(f"🚀 GERAR JOGOS", type="primary", use_container_width=True):
        if len(selecionados) < dez_por_jogo:
            st.error(f"Selecione pelo menos {dez_por_jogo} números no volante!")
        else:
            lista_n = sorted([int(x) for x in selecionados])
            with st.spinner("Calculando combinações..."):
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                
                if res:
                    st.success(f"{len(res)} jogos gerados!")
                    st.metric("Investimento", f"R$ {len(res)*valor_unit:,.2f}")
                    df = pd.DataFrame(res, columns=[f"D{i+1}" for i in range(dez_por_jogo)])
                    st.dataframe(df, use_container_width=True)
                    
                    csv_io = io.StringIO()
                    csv_io.write('\ufeff')
                    w = csv.writer(csv_io, delimiter=';')
                    w.writerow(["Jogo"] + [f"D{i+1}" for i in range(dez_por_jogo)])
                    for idx, r in enumerate(res):
                        w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                    st.download_button("💾 Baixar CSV", csv_io.getvalue().encode('utf-8-sig'), f"jogos_{nome.lower()}.csv", "text/csv", use_container_width=True)

# --- NAVEGAÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
