import streamlit as st
import csv
from itertools import combinations
import io
import random
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Portal Loterias Pro", layout="centered")

# --- DICIONÁRIO DE CONFIGURAÇÕES E ÍCONES (EMOJIS PARA GARANTIR VISUALIZAÇÃO) ---
TEMAS = {
    "Mega-Sena": {
        "cor": "#209869", "total": 60, "cols": 6, "min_sel": 6, "preco": 5.0,
        "icone": "🟢", "desc": "Sorteios quartas e sábados"
    },
    "Lotofácil": {
        "cor": "#930089", "total": 25, "cols": 5, "min_sel": 15, "preco": 3.0,
        "icone": "🟣", "desc": "Fácil de jogar e ganhar"
    },
    "Quina": {
        "cor": "#260085", "total": 80, "cols": 8, "min_sel": 5, "preco": 3.5,
        "icone": "🔵", "desc": "Concorra a prêmios diários"
    },
    "Lotomania": {
        "cor": "#f7941d", "total": 100, "cols": 10, "min_sel": 50, "preco": 3.0,
        "icone": "🟠", "desc": "A mania de ganhar"
    },
    "Dupla Sena": {
        "cor": "#a61324", "total": 50, "cols": 10, "min_sel": 6, "preco": 2.5,
        "icone": "🔴", "desc": "Dobro de chances"
    }
}

# --- CONTROLE DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#31333F"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

# 2. CSS DINÂMICO
st.markdown(f"""
    <style>
    .titulo-custom {{ color: {cor_tema}; font-size: 2rem; font-weight: bold; text-align: center; margin-bottom: 5px; }}
    .subtitulo {{ text-align: center; color: #666; margin-bottom: 20px; }}
    
    /* Estilo dos Cards na Home */
    .card-home {{
        background-color: white;
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}
    .icone-grande {{ font-size: 40px; margin-bottom: 10px; }}
    
    /* Estilo do Volante */
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{
        display: grid !important;
        grid-template-columns: repeat({cols_v}, 1fr) !important;
        gap: 4px !important;
    }}
    button[role="option"] {{ 
        min-width: 0px !important; width: 100% !important; height: 42px !important; 
        font-size: 16px !important; font-weight: bold !important; padding: 0 !important; 
    }}
    
    /* Esconder Sidebar */
    [data-testid="stSidebar"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE FILTRO ---
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
    st.markdown('<div class="titulo-custom">🍀 Portal Loterias Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Gerador de combinações inteligentes</div>', unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        with alvo:
            st.markdown(f"""
                <div class="card-home">
                    <div class="icone-grande">{dados['icone']}</div>
                    <div style="color:{dados['cor']}; font-weight:bold; font-size:18px;">{nome}</div>
                    <div style="font-size:12px; color:#888;">{dados['desc']}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Abrir {nome}", key=f"btn_{nome}", use_container_width=True):
                st.session_state.pagina = nome
                st.rerun()
            st.write("")

def gerador_loteria(nome, config):
    if st.button("⬅️ Voltar ao Menu Principal", use_container_width=True):
        st.session_state.pagina = "Início"
        st.rerun()

    st.markdown(f'<div class="titulo-custom">{config["icone"]} Gerador {nome}</div>', unsafe_allow_html=True)
    
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
            with st.spinner("Gerando..."):
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                
                if res:
                    st.success(f"{len(res)} jogos gerados!")
                    st.metric("Investimento Total", f"R$ {len(res)*valor_unit:,.2f}")
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
