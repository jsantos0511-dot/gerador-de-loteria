import streamlit as st
import csv
from itertools import combinations
import io

# 1. Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# 2. CSS Robusto para o Volante e Layout
st.markdown("""
    <style>
    /* Container do Volante em Grade Real */
    .volante-container {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 6px;
        width: 100%;
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* Estilização dos Botões Numéricos */
    .num-button {
        width: 100%;
        aspect-ratio: 1 / 1;
        border: 1px solid #ccc;
        background-color: #f0f2f6;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: 0.2s;
    }
    
    .num-button.selected {
        background-color: #ff4b4b;
        color: white;
        border-color: #ff4b4b;
    }

    /* Ajuste de Margens do App */
    .block-container {
        padding: 1rem 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

st.title("🎰 Gerador Pro")

# --- VOLANTE COM 6 COLUNAS FIXAS ---
st.subheader("Selecione as Dezenas")
qtd = len(st.session_state.selecionados)
st.write(f"**Selecionados:** {qtd}/60")

# Criamos o volante usando as colunas nativas do Streamlit mas com CSS forçado
# O truque é usar st.button mas injetar uma largura fixa via CSS inline
for linha in range(10):
    cols = st.columns(6)
    for coluna in range(6):
        numero = linha * 6 + coluna + 1
        is_sel = numero in st.session_state.selecionados
        
        # O diferencial aqui é o use_container_width=True combinado com o CSS de grid acima
        if cols[coluna].button(
            f"{numero:02d}", 
            key=f"btn_{numero}", 
            type="primary" if is_sel else "secondary",
            use_container_width=True
        ):
            if is_sel:
                st.session_state.selecionados.remove(numero)
            else:
                st.session_state.selecionados.add(numero)
            st.rerun()

# Forçamos o layout das colunas específicas acima via CSS injetado agora
st.markdown("""
    <style>
    /* Força especificamente os blocos que contêm os botões do volante */
    [data-testid="column"] {
        flex: 1 1 calc(16.66% - 4px) !important;
        min-width: calc(16.66% - 4px) !important;
    }
    
    /* Protege o restante do layout para não quebrar em 6 colunas */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    
    /* Regra para as configurações voltarem ao normal (2 colunas) */
    .config-section [data-testid="column"] {
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES (Encapsuladas para não quebrar) ---
st.markdown('<div class="config-section">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas por jogo", 1, 20, 6)
    valor_unit = st.number_input("Valor R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Qtd Jogos", 1, 1000000, 50)

st.markdown("### Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar Seleção", use_container_width=True):
    st.session_state.selecionados = set()
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- LÓGICA DE GERAÇÃO ---
if gerar:
    st.divider()
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_per_jogo:
        st.error(f"Selecione ao menos {dez_per_jogo} números!")
    else:
        with st.spinner("Processando..."):
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

            st.metric("Total de Jogos", f"{len(res):,}".replace(",", "."))
            st.metric("Investimento", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
