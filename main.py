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

# --- CONTROLE DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#31333F"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

# 2. CONSTRUÇÃO DO CSS DOS CARDS CLICÁVEIS
estilos_cards = ""
for nome, dados in TEMAS.items():
    # Este seletor busca o botão pelo texto (label) exato
    estilos_cards += f"""
    button[aria-label="🍀 {nome}"] {{
        height: 120px !important;
        background-color: white !important;
        border: 2px solid {dados['cor']} !important;
        color: {dados['cor']} !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        font-size: 20px !important;
        display: block !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05) !important;
    }}
    button[aria-label="🍀 {nome}"]:hover {{
        background-color: {dados['cor']}08 !important; /* Efeito suave no clique */
        border-color: {dados['cor']} !important;
    }}
    """

st.markdown(f"""
    <style>
    .titulo-custom {{ color: {cor_tema}; font-size: 2rem; font-weight: bold; text-align: center; margin-bottom: 25px; }}
    
    /* Estilo do Volante */
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({cols_v}, 1fr) !important;
        gap: 4px !important;
    }}
    
    /* Injeção dos estilos dos cards clicáveis */
    {estilos_cards}

    /* Botões internos (Gerar, Limpar, Voltar) ficam normais */
    .stButton > button {{ border-radius: 8px !important; }}
    
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
            # O label do botão deve ser exatamente o que está no CSS aria-label
            if st.button(f"🍀 {nome}", use_container_width=True):
                st.session_state.pagina = nome
                st.rerun()

def gerador_loteria(nome, config):
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.pagina = "Início"
        st.rerun()

    st.markdown(f'<div class="titulo-custom">🍀 Gerador {nome}</div>', unsafe_allow_html=True)
    
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
    
    st.write(f"**Selecionados:** {len(selecionados)}")
    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        dez_por_jogo = st.number_input("Bolas por jogo", config['min_sel'], config['total'], config['min_sel'])
        valor_unit = st.number_input("Preço R$", 0.0, 5000.0, config['preco'])
    with col_b:
        gerar_tudo = st.checkbox("Gerar TODAS possíveis")
        qtd_max = st.number_input("Limite de Jogos", 1, 1000000, 100, disabled=gerar_tudo)

    with st.expander("🛠️ Filtros Avançados"):
        f_s = st.checkbox("🚫 Evitar sequências")
        f_f = st.checkbox("🚫 Evitar +4 finais iguais")
        f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
        m_p = st.slider("Máximo de Pares", 0, dez_por_jogo, dez_por_jogo // 2) if f_p else dez_por_jogo

    if st.button(f"🚀 GERAR JOGOS", type="primary", use_container_width=True):
        if len(selecionados) < dez_por_jogo:
            st.error(f"Selecione no mínimo {dez_por_jogo} números!")
        else:
            lista_n = sorted([int(x) for x in selecionados])
            with st.spinner("Gerando combinações..."):
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                
                if res:
                    st.success(f"{len(res)} jogos gerados!")
                    st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}")
                    df = pd.DataFrame(res, columns=[f"B{i+1}" for i in range(dez_por_jogo)])
                    df.index += 1
                    st.dataframe(df, use_container_width=True)
                    
                    csv_io = io.StringIO()
                    csv_io.write('\ufeff')
                    w = csv.writer(csv_io, delimiter=';')
                    w.writerow(["ID"] + [f"B{i+1}" for i in range(dez_por_jogo)])
                    for idx, r in enumerate(res):
                        w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                    st.download_button("💾 Baixar CSV", csv_io.getvalue().encode('utf-8-sig'), f"jogos_{nome.lower()}.csv", "text/csv", use_container_width=True)

# --- NAVEGAÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
