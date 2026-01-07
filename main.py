import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# Inicialização do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

# Função para gerenciar seleção
def toggle_numero(n):
    if n in st.session_state.selecionados:
        st.session_state.selecionados.remove(n)
    else:
        st.session_state.selecionados.add(n)

st.title("🎰 Gerador Loteria Pro")

# --- CSS PARA O VOLANTE FIXO ---
st.markdown("""
    <style>
    .volante-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 5px;
        max-width: 100%;
        margin-bottom: 20px;
    }
    .stButton > button {
        width: 100% !important;
        height: 45px !important;
        padding: 0 !important;
        font-weight: bold !important;
    }
    /* Estilo para garantir que o resto não quebre */
    [data-testid="column"] {
        min-width: 150px !important;
    }
    @media (max-width: 600px) {
        [data-testid="column"] {
            min-width: 45% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- ÁREA DO VOLANTE ---
st.subheader("Selecione as Dezenas")
qtd = len(st.session_state.selecionados)
st.write(f"**Selecionados: {qtd}/60**")

# Criamos o volante usando um container fixo
with st.container():
    # Para evitar que o Streamlit empilhe, vamos criar as linhas manualmente 
    # mas sem usar o st.columns principal para o layout todo
    for r in range(10): # 10 linhas
        cols = st.columns(6) # 6 colunas
        for c in range(6):
            num = r * 6 + c + 1
            is_sel = num in st.session_state.selecionados
            if cols[c].button(
                f"{num:02d}", 
                key=f"btn_{num}_{st.session_state.limpar_count}",
                type="primary" if is_sel else "secondary"
            ):
                toggle_numero(num)
                st.rerun()

st.divider()

# --- ÁREA DE CONFIGURAÇÃO (ORGANIZADA) ---
col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with col_cfg2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máximo de Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

c_btn1, c_btn2 = st.columns(2)
if c_btn1.button("❌ Limpar Tudo", use_container_width=True):
    st.session_state.selecionados = set()
    st.session_state.limpar_count += 1
    st.rerun()

gerar = c_btn2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- PROCESSAMENTO E RESULTADOS ---
if gerar:
    st.divider()
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error(f"Selecione pelo menos {dez_por_jogo} números.")
    else:
        with st.spinner("Calculando combinações..."):
            combos = combinations(lista_n, dez_por_jogo)
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

            # Exibição
            m1, m2 = st.columns(2)
            m1.metric("Jogos Gerados", f"{len(res):,}".replace(",", "."))
            m2.metric("Custo Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(res[:500], use_container_width=True)
            
            # CSV para Download
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"Bola {x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            
            st.download_button("💾 Baixar para Excel", csv_io.getvalue().encode('utf-8-sig'), 
                             "jogos_loteria.csv", "text/csv", use_container_width=True)
