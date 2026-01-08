import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página e Prevenção de Zoom no Mobile
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. CSS Direcionado (Ajustado para Pixel Perfeito)
st.markdown("""
    <style>
    /* Estilo exclusivo para o container do Volante */
    .volante-grid div[data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(6, 1fr) !important;
        gap: 6px !important;
        width: 100% !important;
    }

    .volante-grid div[data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 !important;
    }

    /* Botão solicitado: Altura otimizada e fonte 15px */
    .volante-grid button {
        height: 35px !important;
        width: 50% !important;
        font-size: 15px !important;
        font-weight: bold !important;
        padding: 0 !important;
    }

    /* Remove padding excessivo lateral no celular */
    .block-container {
        padding: 1rem 0.5rem !important;
    }
    
    /* Melhora a visualização das métricas no celular */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização de Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Loteria")

# --- ÁREA DO VOLANTE ---
st.subheader("Escolha seus números")
qtd = len(st.session_state.selecionados)
st.write(f"**Selecionados:** {qtd}/60")

# Container que força as 6 colunas
st.markdown('<div class="volante-grid">', unsafe_allow_html=True)
for linha in range(10): 
    cols = st.columns(6)
    for coluna in range(6):
        numero = linha * 6 + coluna + 1
        is_sel = numero in st.session_state.selecionados
        if cols[coluna].button(
            f"{numero:02d}", 
            key=f"v_{numero}_{st.session_state.limpar_count}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if is_sel:
                st.session_state.selecionados.remove(numero)
            else:
                st.session_state.selecionados.add(numero)
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES ---
col_config1, col_config2 = st.columns(2)
with col_config1:
    dez_per_jogo = st.number_input("Números por jogo", 6, 20, 6)
    valor_unit = st.number_input("Preço da Aposta R$", 0.0, 1000.0, 5.0)
with col_config2:
    gerar_tudo = st.checkbox("Gerar todas possíveis")
    qtd_max = 1000000 if gerar_tudo else st.number_input("Limite de jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
c_f1, c_f2 = st.columns(2)
with c_f1:
    f_seq = st.checkbox("🚫 Sem Sequências", True)
    f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
with c_f2:
    f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
    max_p = st.slider("Máx. de Pares", 1, dez_per_jogo, dez_per_jogo//2 + 1)

# Botões de Ação
st.write("")
c_btn1, c_btn2 = st.columns(2)
with c_btn1:
    if st.button("❌ Limpar Tudo", use_container_width=True):
        st.session_state.selecionados = set()
        st.session_state.limpar_count += 1
        st.rerun()
with c_btn2:
    gerar = st.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- PROCESSAMENTO ---
if gerar:
    st.divider()
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_per_jogo:
        st.error(f"Escolha pelo menos {dez_per_jogo} números no volante.")
    else:
        with st.spinner("Criando combinações..."):
            combos = combinations(lista_n, dez_per_jogo)
            res = []
            for c in combos:
                j = sorted(list(c))
                # Filtro Sequência
                if f_seq and any(j[n+1] == j[n]+1 for n in range(len(j)-1)): continue
                # Filtro Finais
                if f_fin and len(set(n % 10 for n in j)) == 1: continue
                # Filtro Par/Ímpar
                if f_par:
                    p = len([n for n in j if n % 2 == 0])
                    if p > max_p or (len(j)-p) > max_p: continue
                
                res.append(j)
                if len(res) >= qtd_max: break

            if not res:
                st.warning("Nenhum jogo encontrado com esses filtros.")
            else:
                m1, m2 = st.columns(2)
                m1.metric("Total de Jogos", f"{len(res):,}".replace(",", "."))
                m2.metric("Valor Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.dataframe(res[:500], use_container_width=True)
                
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"Dezena {x+1}" for x in range(dez_per_jogo)])
                for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
                
                st.download_button("💾 Baixar Jogos (CSV)", csv_io.getvalue().encode('utf-8-sig'), 
                                 "meus_jogos_loteria.csv", "text/csv", use_container_width=True)
