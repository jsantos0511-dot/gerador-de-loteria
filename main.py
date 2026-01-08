import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. CSS com Medidas Fixas (px) para Mobile
st.markdown("""
    <style>
    /* Reset de margens para o celular */
    .block-container { padding: 0.5rem !important; }

    /* Forçamos a grade de 6 colunas no container do volante */
    .volante-container div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 40px) !important; /* 6 colunas de 40px */
        gap: 5px !important;
        justify-content: center; /* Centraliza o volante na tela */
    }

    /* Removemos qualquer interferência das colunas do Streamlit */
    .volante-container div[data-testid="column"] {
        width: 40px !important;
        min-width: 40px !important;
        flex: none !important;
    }

    /* Botões com tamanhos fixos solicitados */
    .stButton > button {
        width: 40px !important;
        height: 30px !important;
        padding: 0 !important;
        font-size: 15px !important;
        font-weight: bold !important;
        line-height: 30px !important; /* Alinha o texto no centro */
    }

    /* Garante que o restante do app use o layout normal do Streamlit */
    .area-normal div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        grid-template-columns: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Pro")

# --- VOLANTE ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(st.session_state.selecionados)}/60")

# Aplicamos o container para isolar o volante
st.markdown('<div class="volante-container">', unsafe_allow_html=True)

for r in range(10):
    cols = st.columns(6)
    for c in range(6):
        num = r * 6 + c + 1
        is_sel = num in st.session_state.selecionados
        if cols[c].button(
            f"{num:02d}", 
            key=f"v_{num}_{st.session_state.limpar_count}",
            type="primary" if is_sel else "secondary"
        ):
            if is_sel: st.session_state.selecionados.remove(num)
            else: st.session_state.selecionados.add(num)
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES E FILTROS (ÁREA NORMAL) ---
st.markdown('<div class="area-normal">', unsafe_allow_html=True)

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
        valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
    with c2:
        gerar_tudo = st.checkbox("Gerar Todas")
        qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

    st.markdown("### Filtros")
    f_seq = st.checkbox("🚫 Sem Sequências", True)
    f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
    f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
    max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("❌ Limpar Seleção", use_container_width=True):
        st.session_state.selecionados = set()
        st.session_state.limpar_count += 1
        st.rerun()
    
    gerar = col_btn2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- PROCESSAMENTO E RESULTADOS ---
if gerar:
    lista_n = sorted(list(st.session_state.selecionados))
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
            m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
