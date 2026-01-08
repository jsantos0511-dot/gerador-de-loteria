import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# --- 1. ESTADO DA SESSÃO ---
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# --- 2. LÓGICA DE CLIQUE (CAPTURADA POR QUERY PARAMS) ---
# Usamos o rerun imediato para garantir que a seleção seja salva
p = st.query_params
if "n" in p:
    num = int(p["n"])
    if num in st.session_state.selecionados:
        st.session_state.selecionados.remove(num)
    else:
        st.session_state.selecionados.add(num)
    st.query_params.clear()
    st.rerun()

# --- 3. CSS "PIXEL PERFEITO" SEM COLUNAS STREAMLIT ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* Grade manual que ignora o layout do Streamlit */
    .grade-fixa {
        display: grid !important;
        grid-template-columns: repeat(6, 40px) !important;
        gap: 5px !important;
        justify-content: center;
        margin: 10px auto;
        padding: 0;
        width: 270px; /* Largura total exata para evitar quebra */
    }

    /* Botões HTML com tamanho 40x30px e fonte 15px */
    .btn-loteria {
        width: 40px !important;
        height: 30px !important;
        font-size: 15px !important;
        font-weight: bold;
        text-align: center;
        line-height: 30px;
        text-decoration: none !important;
        background-color: #f0f2f6;
        color: #31333f !important;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        display: inline-block;
    }

    .btn-loteria.ativo {
        background-color: #ff4b4b !important;
        color: white !important;
        border-color: #ff4b4b;
    }

    /* Protege o resto do app do CSS acima */
    .area-normal { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎰 Gerador Pro")
st.subheader("Selecione as Dezenas")
st.write(f"**Marcados:** {len(st.session_state.selecionados)}/60")

# --- 4. O VOLANTE (HTML PURO) ---
# Aqui eliminamos o st.columns e o st.button, que causavam o empilhamento
volante_html = '<div class="grade-fixa">'
for i in range(1, 61):
    ativo = "ativo" if i in st.session_state.selecionados else ""
    volante_html += f'<a href="?n={i}" target="_self" class="btn-loteria {ativo}">{i:02d}</a>'
volante_html += '</div>'

st.markdown(volante_html, unsafe_allow_html=True)

st.divider()

# --- 5. CONFIGURAÇÕES E FILTROS (ÁREA NORMAL) ---
st.markdown('<div class="area-normal">', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Limite de Jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar Tudo", use_container_width=True):
    st.session_state.selecionados = set()
    st.query_params.clear()
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- 6. PROCESSAMENTO ---
if gerar:
    lista_n = sorted(list(st.session_state.selecionados))
    if len(lista_n) < dez_por_jogo:
        st.error(f"Selecione pelo menos {dez_por_jogo} dezenas!")
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

            if res:
                st.divider()
                m1, m2 = st.columns(2)
                m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
                m2.metric("Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.dataframe(res[:500], use_container_width=True)
                
                csv_io = io.StringIO()
                csv_io.write('\ufeff')
                w = csv.writer(csv_io, delimiter=';')
                w.writerow(["Jogo"] + [f"B{x+1}" for x in range(len(res[0]))])
                for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
                st.download_button("💾 Baixar Excel", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
