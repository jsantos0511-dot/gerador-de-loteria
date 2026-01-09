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

# --- NAVEGAÇÃO ---
params = st.query_params
if "escolha" in params:
    st.session_state.pagina = params["escolha"]

if 'pagina' not in st.session_state:
    st.session_state.pagina = "Início"

p_atual = st.session_state.pagina
cor_tema = TEMAS[p_atual]['cor'] if p_atual != "Início" else "#ffffff"
cols_v = TEMAS[p_atual]['cols'] if p_atual != "Início" else 6

# 2. CSS (Base mantida e refinada)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: #ffffff; }}
    .card-container {{
        border: 2px solid var(--cor-loteria);
        border-radius: 12px;
        padding: 12px 8px;
        text-align: center;
        background-color: #161b22;
        transition: all 0.2s ease;
        cursor: pointer;
        text-decoration: none !important;
        display: block;
        margin-bottom: 12px;
    }}
    .card-container:hover {{ transform: scale(1.02); box-shadow: 0 0 15px var(--cor-loteria); }}
    .card-title {{ font-size: 17px; font-weight: bold; color: var(--cor-loteria); }}
    button[role="option"][aria-selected="true"] {{ background-color: {cor_tema} !important; color: white !important; }}
    div[data-testid="stSegmentedControl"] {{ display: grid !important; grid-template-columns: repeat({cols_v}, 1fr) !important; gap: 3px !important; }}
    [data-testid="stSidebar"] {{ display: none; }}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE LÓGICA ---
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

# --- TELAS ---

def home():
    st.markdown('<h2 style="text-align:center; margin-bottom:25px;">🍀 Portal Loterias</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for i, (nome, dados) in enumerate(TEMAS.items()):
        alvo = col1 if i % 2 == 0 else col2
        card_html = f"""<a href="/?escolha={nome}" target="_self" class="card-container" style="--cor-loteria: {dados['cor']};">
            <div style="font-size:22px;">🍀</div><div class="card-title">{nome}</div></a>"""
        alvo.markdown(card_html, unsafe_allow_html=True)

def gerador_loteria(nome, config):
    c_v, c_t = st.columns([1, 4])
    with c_v:
        if st.button("⬅️ Sair"):
            st.query_params.clear()
            st.session_state.pagina = "Início"
            st.rerun()
    with c_t: st.markdown(f'<h3 style="color:{config["cor"]}; margin:0;">🍀 {nome}</h3>', unsafe_allow_html=True)

    aba_gerar, aba_estatisticas, aba_conferir = st.tabs(["🚀 Gerador", "📊 Estatísticas", "🎯 Conferidor"])

    # --- ABA GERADOR ---
    with aba_gerar:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎲 Surpresinha", use_container_width=True):
                st.session_state[f"sel_{nome}"] = [f"{i:02d}" for i in random.sample(range(1, config['total'] + 1), config['min_sel'])]
        with c2:
            if st.button("❌ Limpar", use_container_width=True):
                st.session_state[f"sel_{nome}"] = []
                st.rerun()

        selecionados = st.segmented_control("V", options=[f"{i:02d}" for i in range(1, config['total'] + 1)], selection_mode="multi", key=f"sel_{nome}", label_visibility="collapsed")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a: dez_por_jogo = st.number_input("Dezenas", config['min_sel'], config['total'], config['min_sel'])
        with col_b: valor_unit = st.number_input("Preço R$", 0.0, 5000.0, config['preco'])
        with col_c: 
            gerar_tudo = st.checkbox("Gerar Todos")
            qtd_max = st.number_input("Limite", 1, 1000000, 100, disabled=gerar_tudo)

        # FILTROS OCULTOS POR PADRÃO (expanded=False)
        with st.expander("🛠️ Filtros Inteligentes", expanded=False):
            f_s = st.checkbox("🚫 Sem sequências")
            f_f = st.checkbox("🚫 Limitar finais iguais (máx 4)")
            f_p = st.checkbox("⚖️ Equilibrar Par/Ímpar")
            m_p = st.slider("Máx. Pares", 0, dez_por_jogo, dez_por_jogo // 2) if f_p else dez_por_jogo

        if st.button(f"🚀 GERAR JOGOS", type="primary", use_container_width=True):
            if len(selecionados) < dez_por_jogo: st.error(f"Selecione no mínimo {dez_por_jogo} números!")
            else:
                lista_n = sorted([int(x) for x in selecionados])
                combos = combinations(lista_n, dez_por_jogo)
                res = aplicar_filtros(combos, f_s, f_f, f_p, m_p, dez_por_jogo, qtd_max, gerar_tudo)
                st.session_state[f"ultimos_jogos_{nome}"] = res 
                
                if res:
                    st.success(f"{len(res)} jogos!")
                    st.metric("Total", f"R$ {len(res)*valor_unit:,.2f}")
                    df = pd.DataFrame(res, columns=[f"B{i+1}" for i in range(dez_por_jogo)])
                    st.dataframe(df, use_container_width=True)
                    
                    csv_io = io.StringIO()
                    w = csv.writer(csv_io, delimiter=';')
                    w.writerow(["ID"] + [f"B{i+1}" for i in range(dez_por_jogo)])
                    for idx, r in enumerate(res): w.writerow([idx + 1] + [f"{n:02d}" for n in r])
                    st.download_button("💾 Baixar CSV", csv_io.getvalue().encode('utf-8-sig'), f"{nome}.csv", use_container_width=True)

    # --- ABA ESTATÍSTICAS ---
    with aba_estatisticas:
        st.subheader("📊 Análise da Seleção Atual")
        if not selecionados:
            st.info("Selecione números no volante para ver as estatísticas da sua escolha.")
        else:
            nums_int = [int(n) for n in selecionados]
            pares = [n for n in nums_int if n % 2 == 0]
            impares = [n for n in nums_int if n % 2 != 0]
            
            c1, c2 = st.columns(2)
            c1.metric("Pares", len(pares))
            c2.metric("Ímpares", len(impares))
            
            # Gráfico de Finais
            finais_contagem = pd.Series([n % 10 for n in nums_int]).value_counts().sort_index()
            st.write("**Distribuição por Final (0-9):**")
            st.bar_chart(finais_contagem, color=config['cor'])
            
            # Gráfico de Dezenas (Faixas)
            faixas = pd.cut(nums_int, bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 
                           labels=['1-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100'])
            st.write("**Distribuição por Faixas Numéricas:**")
            st.bar_chart(faixas.value_counts().sort_index(), color=config['cor'])

    # --- ABA CONFERIR ---
    with aba_conferir:
        st.subheader("🎯 Conferir Acertos")
        if f"ultimos_jogos_{nome}" not in st.session_state:
            st.warning("Gere jogos primeiro para poder conferir os acertos.")
        else:
            txt_resultado = st.text_input("Números sorteados", placeholder="Ex: 05, 12, 28, 40, 52, 60")
            if txt_resultado:
                try:
                    num_sorteados = [int(n.strip()) for n in txt_resultado.replace(',', ' ').split() if n.strip().isdigit()]
                    if len(num_sorteados) > 0:
                        jogos = st.session_state[f"ultimos_jogos_{nome}"]
                        resultados_conferidos = []
                        for j in jogos:
                            acertos = set(j).intersection(set(num_sorteados))
                            resultados_conferidos.append(list(j) + [len(acertos)])
                        
                        df_res = pd.DataFrame(resultados_conferidos, columns=[f"D{i+1}" for i in range(len(jogos[0]))] + ["✅ Acertos"])
                        df_res = df_res.sort_values(by="✅ Acertos", ascending=False)
                        st.dataframe(df_res.style.highlight_max(subset=["✅ Acertos"], color=config['cor']), use_container_width=True)
                except:
                    st.error("Formato inválido.")

# --- EXECUÇÃO ---
if st.session_state.pagina == "Início": home()
else: gerador_loteria(st.session_state.pagina, TEMAS[st.session_state.pagina])
