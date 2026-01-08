import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# --- LÓGICA DE PERSISTÊNCIA NA URL ---
# Lemos os números que já estão na URL
params = st.query_params
selecionados_na_url = params.get_all("n") # Pega todos os valores de 'n'
selecionados = [int(x) for x in selecionados_na_url]

# Se houver um novo clique
if "clique" in params:
    num_clicado = int(params.get("clique"))
    if num_clicado in selecionados:
        selecionados.remove(num_clicado)
    else:
        selecionados.append(num_clicado)
    
    # Atualiza a URL com a nova lista e recarrega
    st.query_params.from_dict({"n": selecionados})
    st.rerun()

st.title("🎰 Gerador Pro")

# --- VISUAL DO VOLANTE (HTML PURO) ---
st.subheader("Selecione as Dezenas")
st.write(f"**Selecionados:** {len(selecionados)}/60")

html_volante = """
<style>
    .grid-container {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 6px;
        width: 100%;
        max-width: 400px;
        margin: 10px 0;
    }
    .num-btn {
        background-color: #F0F2F6;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        height: 45px;
        font-family: sans-serif;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        color: #31333F;
    }
    .num-btn.active {
        background-color: #FF4B4B;
        color: white;
        border-color: #FF4B4B;
    }
</style>
<div class="grid-container">
"""

# Criamos os links mantendo os números já selecionados na URL
base_url = "?"
for s in selecionados:
    base_url += f"n={s}&"

for i in range(1, 61):
    clase = "num-btn active" if i in selecionados else "num-btn"
    # Cada botão envia o seu número para o parâmetro 'clique'
    url_botao = f"{base_url}clique={i}"
    html_volante += f'<a href="{url_botao}" target="_self" class="{clase}">{i:02d}</a>'

html_volante += "</div>"
st.markdown(html_volante, unsafe_allow_html=True)

st.divider()

# --- CONFIGURAÇÕES ---
c1, c2 = st.columns(2)
with c1:
    dez_por_jogo = st.number_input("Dezenas/jogo", 1, 20, 6)
    valor_unit = st.number_input("Preço R$", 0.0, 500.0, 5.0)
with c2:
    gerar_tudo = st.checkbox("Gerar Todas")
    qtd_max = 1048576 if gerar_tudo else st.number_input("Limite Jogos", 1, 1000000, 50)

st.markdown("### 🛠️ Filtros")
f_seq = st.checkbox("🚫 Sem Sequências", True)
f_fin = st.checkbox("🚫 Sem Finais Iguais", True)
f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", True)
max_p = st.slider("Máx. Pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))

b1, b2 = st.columns(2)
if b1.button("❌ Limpar Tudo", use_container_width=True):
    st.query_params.clear()
    st.rerun()

gerar = b2.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

# --- PROCESSAMENTO ---
if gerar:
    st.divider()
    lista_n = sorted(selecionados)
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

            m1, m2 = st.columns(2)
            m1.metric("Jogos", f"{len(res):,}".replace(",", "."))
            m2.metric("Total", f"R$ {len(res)*valor_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(res[:500], use_container_width=True)
            
            csv_io = io.StringIO()
            csv_io.write('\ufeff')
            w = csv.writer(csv_io, delimiter=';')
            w.writerow(["Jogo"] + [f"B{x+1}" for x in range(dez_por_jogo)])
            for idx, r in enumerate(res): w.writerow([idx+1] + [f"{n:02d}" for n in r])
            st.download_button("💾 Baixar Planilha", csv_io.getvalue().encode('utf-8-sig'), "jogos.csv", "text/csv", use_container_width=True)
