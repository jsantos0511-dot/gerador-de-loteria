import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES, CORES E LOGOS ---
TEMAS = {
    "Mega-Sena": {
        "cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Logo_Mega-Sena.svg/200px-Logo_Mega-Sena.svg.png"
    },
    "Lotofácil": {
        "cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Logo_Lotof%C3%A1cil.svg/200px-Logo_Lotof%C3%A1cil.svg.png"
    },
    "Quina": {
        "cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Logo_Quina.svg/200px-Logo_Quina.svg.png"
    },
    "Lotomania": {
        "cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Logo_Lotomania.svg/200px-Logo_Lotomania.svg.png"
    },
    "Dupla Sena": {
        "cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5,
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Logo_Dupla_Sena.svg/200px-Logo_Dupla_Sena.svg.png"
    }
}

# --- CONTROLE DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

# Define o tema atual baseado na página
cor_tema = TEMAS[st.session_state.pagina]['cor'] if st.session_state.pagina != "Início" else "#31333F"
cols_volante = TEMAS[st.session_state.pagina]['cols'] if st.session_state.pagina != "Início" else 6

# 2. CSS DINÂMICO
st.markdown(f"""
    <style>
    .titulo-custom {{ color: {cor_tema}; font-size: 1.8rem; font-weight: bold; text-align: center; margin-bottom: 20px; }}
    .card {{
        border-radius: 10px; padding: 20px; text-align: center;
        border: 2px solid #f0f2f6; transition: 0.3s; margin-bottom: 10px;
    }}
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({cols_volante}, 1fr) !important;
        gap: 5px !important;
    }}
    button[role="option"] {{ min-width: 0px !important; width: 100% !important; height: 42px !important; font-size: 17px !important; font-weight: bold !important; }}
    .stButton > button {{ border-radius: 8px !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---

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

def home():
    st.markdown('<div class="titulo-custom">🍀 Portal de Loterias Pro</div>', unsafe_allow_html=True)
    st.write("---")
    
    # Grid de Cards
    col1, col2 = st.columns(2)
    
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        with alvo:
            st.markdown(f"""<div style='text-align: center;'>
                <img src='{dados['logo']}' width='60'><br>
                <b style='color:{dados['cor']};'>{nome}</b>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Abrir {nome}", key=f"btn_{nome}", use_container_width=True):
                st.session_state.pagina = nome
                st.rerun()
            st.write("")

def gerador_loteria(nome, config):
    if st.button("⬅️ Voltar ao Início"):
        st.session_state.pagina = "Início"
        st.rerun()

    col_logo, col_tit = st.columns([1, 4])
    with col_logo: st.image(config['logo'], width=75)
    with col_tit: st.markdown(f'<div class="titulo-custom" style="text-align:left">Gerador {nome}</div>', unsafe_allow_html=True)
    
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
        gerar_tudo = st.checkbox("Gerar TODAS")
        qtd_max = st.number_input("Limite", 1, 1000000, 100, disabled=gerar_tudo)

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
            with st.spinner("Calculando..."):
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

# --- NAVEGAÇÃO ---
if st.session_state.pagina == "Início":
    home()
else:
    gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])

# Menu Lateral como backup/atalho rápido
with st.sidebar:
    st.title("Atalhos")
    if st.button("🏠 Início", use_container_width=True):
        st.session_state.pagina = "Início"
        st.rerun()
    for nome in TEMAS.keys():
        if st.button(nome, key=f"side_{nome}", use_container_width=True):
            st.session_state.pagina = nome
            st.rerun()
