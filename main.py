import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES E LOGOS ---
TEMAS = {
    "Início": {"cor": "#31333F", "titulo": "Portal de Loterias", "cols": 6, "total": 0},
    "Mega-Sena": {
        "cor": "#209869", "total": 60, "cols": 6, "min_sel": 6,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Logo_Mega-Sena.svg/200px-Logo_Mega-Sena.svg.png"
    },
    "Lotofácil": {
        "cor": "#930089", "total": 25, "cols": 5, "min_sel": 15,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Logo_Lotof%C3%A1cil.svg/200px-Logo_Lotof%C3%A1cil.svg.png"
    },
    "Quina": {
        "cor": "#260085", "total": 80, "cols": 8, "min_sel": 5,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Logo_Quina.svg/200px-Logo_Quina.svg.png"
    },
    "Lotomania": {
        "cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Logo_Lotomania.svg/200px-Logo_Lotomania.svg.png"
    }
}

# --- MENU LATERAL ---
st.sidebar.title("Escolha o Jogo")
menu = st.sidebar.radio("Modalidades:", list(TEMAS.keys()))
tema_atual = TEMAS[menu]

# 2. CSS DINÂMICO
st.markdown(f"""
    <style>
    .titulo-custom {{
        color: {tema_atual['cor']};
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 10px;
    }}
    button[role="option"][aria-selected="true"] {{
        background-color: {tema_atual['cor']} !important;
        color: white !important;
    }}
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({tema_atual['cols']}, 1fr) !important;
        gap: 5px !important;
    }}
    button[role="option"] {{
        min-width: 0px !important; width: 100% !important; height: 42px !important;
        font-weight: bold !important; border-radius: 6px !important; font-size: 17px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE FILTRAGEM ---
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
    st.markdown(f'<div class="titulo-custom" style="text-align:center">{tema_atual["titulo"]}</div>', unsafe_allow_html=True)
    st.info("Selecione uma modalidade no menu lateral para começar.")

def gerador_loteria(nome, config):
    # CABEÇALHO COM LOGO
    col_logo, col_tit = st.columns([1, 4])
    with col_logo:
        st.image(config['logo'], width=70)
    with col_tit:
        st.markdown(f'<div class="titulo-custom">Gerador {nome}</div>', unsafe_allow_html=True)
    
    key_sel = f"sel_{nome}"
    if key_sel not in st.session_state: st.session_state[key_sel] = []
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Surpresinha", use_container_width=True):
            st.session_state[key_sel] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
    with c2:
        if st.button("❌ Limpar", use_container_width=True):
            st.session_state[key_sel] = []
            st.rerun()

    opcoes = [f"{i:02d}" for i in range(1, config['total'] + 1)]
    selecionados = st.segmented_control("V", options=opcoes, selection_mode="multi", key=key_sel, label_visibility="collapsed")
    
    st.write(f"**Selecionados:** {len(selecionados)}")
    
    col_a, col_b = st.columns(2)
    with col_a:
        dez_por_jogo = st.number_input("Bolas por jogo", config['min_sel'], config['total'], config['min_sel'])
        valor_unit = st.number_input("Preço R$", 0.0, 5000.0, 5.0)
    with col_b:
        gerar_tudo = st.checkbox("Gerar TODAS")
        qtd_max = st.number_input("Limite", 1, 1000000, 100, disabled=gerar_tudo)

    with st.expander("🛠️ Filtros Avançados"):
        f_s = st.checkbox("🚫 Sem sequências")
        f_f = st.checkbox("🚫 Sem +4 finais iguais")
        f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
        m_p = st.slider("Máx Pares", 0, dez_por_jogo, dez_por_jogo // 2) if f_p else dez_por_jogo

    if st.button(f"🚀 GERAR JOGOS", type="primary", use_container_width=True):
        if len(selecionados) < dez_por_jogo:
            st.error(f"Selecione {dez_por_jogo} números!")
        else:
            lista_n = sorted([int(x) for x in selecionados])
            with st.spinner("Gerando..."):
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                
                if res:
                    st.success(f"{len(res)} jogos!")
                    st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}")
                    df = pd.DataFrame(res, columns=[f"Bola {i+1}" for i in range(dez_por_jogo)])
                    df.index += 1
                    st.dataframe(df, use_container_width=True)
                    
                    csv_io = io.StringIO()
                    csv_io.write('\ufeff')
                    w = csv.writer(csv_io, delimiter=';')
                    w.writerow(["ID"] + [f"Bola {i+1}" for i in range(dez_por_jogo)])
                    for idx, r in enumerate(res):
                        w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                    st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), f"jogos_{nome}.csv", "text/csv", use_container_width=True)

# --- ROTEAMENTO FINAL ---
if menu == "Início":
    home()
else:
    gerador_loteria(menu, tema_atual)
