import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="🎰 Gerador Mega-Sena PRO", layout="wide")
st.title("🎰 Gerador Mega-Sena - Clique Múltiplo!")

# Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# CSS Profissional
st.markdown("""
<style>
.volante-table {width:100%;max-width:450px;border-collapse:separate;border-spacing:6px;margin:20px auto;}
.volante-table td{width:16.66%;}
.numero-btn {
  width:100%;height:55px;background:linear-gradient(145deg,#f8fafc,#e2e8f0);
  border:2px solid #cbd5e1;border-radius:12px;color:#1e293b!important;
  font-weight:700;font-size:20px;cursor:pointer;transition:all 0.2s;
  display:flex;align-items:center;justify-content:center;
}
.numero-btn:hover{transform:scale(1.05);background:linear-gradient(145deg,#e2e8f0,#cbd5e1)!important;}
.numero-btn.selecionado{
  background:linear-gradient(145deg,#ef4444,#dc2626)!important;color:white!important;
  border-color:#b91c1c;box-shadow:0 6px 20px rgba(239,68,68,0.4);
}
</style>
""", unsafe_allow_html=True)

# Contador
st.markdown(f"### **Selecionados: {len(st.session_state.selecionados)}/60** 👆")

# VOLANTE com CALLBACK JS (SEM RELOAD!)
col_esq, col_dir = st.columns([1,3])
with col_esq:
    st.markdown('<table class="volante-table">', unsafe_allow_html=True)
    for linha in range(10):
        st.markdown('<tr>', unsafe_allow_html=True)
        for coluna in range(6):
            n = linha * 6 + coluna + 1
            selecionado = n in st.session_state.selecionados
            classe = "selecionado" if selecionado else ""
            
            st.button(
                str(n).zfill(2),
                key=f"num_{n}",
                on_click=lambda num=n: toggle_numero(num),
                help=f"Clique para {'remover' if selecionado else 'adicionar'} {n}",
                args=(),
                use_container_width=True
            )
        st.markdown('</tr>', unsafe_allow_html=True)
    st.markdown('</table>', unsafe_allow_html=True)

def toggle_numero(numero):
    """Callback - Toggle sem reload!"""
    if numero in st.session_state.selecionados:
        st.session_state.selecionados.remove(numero)
    else:
        st.session_state.selecionados.add(numero)
    # st.rerun() REMOVIDO - Streamlit detecta automaticamente!

# Botão LIMPAR
if st.button("🗑️ LIMPAR TUDO", type="secondary"):
    st.session_state.selecionados.clear()
    st.rerun()

st.divider()

# CONFIG + GERAÇÃO (igual ao original)
col1, col2 = st.columns(2)
dezenas_input = st.text_area("Suas dezenas (1-60, vírgula):", 
                           value=",".join(map(str, sorted(st.session_state.selecionados))), height=80)
num_jogos = st.number_input("Jogos?", 1, 999999, 50)
min_pares = st.slider("Mín pares/jogo", 0, 5, 2)
max_pares = st.slider("Máx pares/jogo", 1, 6, 4)
shuffle_jogos = st.checkbox("Embaralhar", True)

if st.button("🚀 GERAR JOGOS!", type="primary"):

    def gerar_jogos_balanceados(dezenas_str, num_jogos, min_pares, max_pares, shuffle=False):
        try:
            dezenas = sorted(set(int(x.strip()) for x in dezenas_str.split(",") if x.strip().isdigit()))
            todas_combos = list(combinations(dezenas, 6))
            jogos_ok = []
            for combo in todas_combos:
                pares = sum(1 for x in combo if x % 2 == 0)
                if min_pares <= pares <= max_pares:
                    jogos_ok.append(list(combo))
            if shuffle:
                import random
                random.shuffle(jogos_ok)
            return jogos_ok[:num_jogos]
        except:
            return []

    with st.spinner("Calculando..."):
        jogos = gerar_jogos_balanceados(dezenas_input, num_jogos, min_pares, max_pares, shuffle_jogos)
        
        if jogos:
            st.success(f"✅ **{len(jogos)} jogos gerados!**")
            
            # Tabela
            df = [{"Jogo": i+1, "Dezenas": ", ".join(f"{n:02d}" for n in sorted(jogo))} 
                  for i, jogo in enumerate(jogos)]
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download CSV (semicolons pro Excel)
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer, delimiter=';')
            writer.writerow(["Jogo", "Dezenas"])
            for row in df:
                writer.writerow([row["Jogo"], row["Dezenas"]])
            
            st.download_button(
                "💾 CSV Excel", csv_buffer.getvalue(),
                "mega_sena_jogos.csv", "text/csv", use_container_width=True
            )
            
            # Stats
            st.subheader("📊 Stats")
            col1, col2, col3 = st.columns(3)
            col1.metric("Jogos", len(jogos))
            col2.metric("Dezenas únicas", len(set().union(*[set(j) for j in jogos])))
            total_combos = len(list(combinations([int(x.strip()) for x in dezenas_input.split(",") if x.strip().isdigit()], 6)))
            col3.metric("Combos possíveis", f"{total_combos:,}")
            
        else:
            st.error("❌ Sem jogos. Ajuste filtros!")

st.caption("🔧 **FIX:** `st.button(on_click)` substitui `href/query_params` - Zero reloads!")
