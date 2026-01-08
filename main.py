import streamlit as st
import csv
from itertools import combinations
import io

st.set_page_config(page_title="🎰 Mega-Sena Mobile", layout="wide", initial_sidebar_state="collapsed")
st.title("🎰 Mega-Sena PRO 📱")

# Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()

# CSS MOBILE RESPONSIVO (5 colunas largas)
st.markdown("""
<style>
* { font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
.stButton > button { width: 100% !important; height: 55px !important; border-radius: 12px !important; font-size: 22px !important; font-weight: 700 !important; }
.volante-container { max-width: 100% !important; overflow-x: auto; }
.volante-table { 
  width: 100% !important; border-collapse: separate !important; border-spacing: 8px 8px !important; 
  min-width: 420px !important; 
}
.volante-table td { width: 20% !important; height: 65px !important; padding: 0 !important; }
.numero-btn {
  width: 100% !important; height: 100% !important; 
  background: linear-gradient(145deg, #f1f5f9, #e2e8f0) !important;
  border: 3px solid #cbd5e1 !important; border-radius: 16px !important;
  color: #1e293b !important; font-size: 24px !important; font-weight: 800 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important; transition: all 0.2s ease !important;
}
.numero-btn:hover { 
  transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
  background: linear-gradient(145deg, #e2e8f0, #cbd5e1) !important;
}
.numero-btn.selecionado {
  background: linear-gradient(145deg, #ef4444, #dc2626) !important; 
  border-color: #b91c1c !important; color: white !important !important;
  box-shadow: 0 8px 25px rgba(239,68,68,0.5) !important; transform: scale(1.05) !important;
}
@media (max-width: 768px) {
  .volante-table { min-width: 380px !important; border-spacing: 6px 6px !important; }
  .volante-table td { height: 58px !important; }
  .numero-btn { font-size: 22px !important; }
}
</style>
""", unsafe_allow_html=True)

# Header Mobile
st.markdown(f"""
<div style='text-align:center; padding: 1rem; background: linear-gradient(90deg, #3b82f6, #1d4ed8); 
            color: white; border-radius: 20px; margin: 1rem 0;'>
  <h2 style='margin:0;'>🔢 {len(st.session_state.selecionados)}/60 SELECIONADOS</h2>
</div>
""", unsafe_allow_html=True)

# FUNÇÃO CALLBACK (CRÍTICA)
def toggle_numero(numero):
    if numero in st.session_state.selecionados:
        st.session_state.selecionados.remove(numero)
    else:
        st.session_state.selecionados.add(numero)
    # Sem st.rerun() - botão já atualiza!

# VOLANTE 5 COLUNAS RESPONSIVO
with st.container():
    st.markdown('<div class="volante-container">', unsafe_allow_html=True)
    st.markdown('<table class="volante-table">', unsafe_allow_html=True)
    
    for linha in range(12):  # 60 números
        if linha % 2 == 0:  # Nova linha pares
            st.markdown('<tr>', unsafe_allow_html=True)
        # 5 colunas largas
        for pos in range(5):
            n = linha * 5 + pos + 1
            if n > 60: break
            selecionado = n in st.session_state.selecionados
            st.button(
                f"{n:02d}",
                key=f"btn_{n}",
                on_click=toggle_numero,
                args=(n,),
                help=f"{'Remover' if selecionado else 'Adicionar'} {n}",
            )
        st.markdown('</tr>', unsafe_allow_html=True)
    
    st.markdown('</table></div>', unsafe_allow_html=True)

# CONTROLES MOBILE
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ LIMPAR TUDO", type="secondary", use_container_width=True):
        st.session_state.selecionados.clear()
        st.experimental_rerun()

# CONFIG COMPACTA
st.markdown("---")
dezenas_input = st.text_area(
    "📝 Dezenas (auto-preenche):", 
    value=",".join(map(str, sorted(st.session_state.selecionados))), 
    height=80, key="input_dezenas"
)
num_jogos = st.number_input("🎯 Jogos:", 1, 999999, 50, key="num_jogos")
min_pares = st.slider("⚖️ Mín pares:", 0, 5, 2)
max_pares = st.slider("⚖️ Máx pares:", 1, 6, 4)

if st.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True, help="Gera combinações balanceadas"):
    
    def gerar_balanceado(dezenas_str, qtd, min_p, max_p):
        try:
            dezenas = sorted(set(int(x) for x in dezenas_str.split(",") if x.isdigit()))
            combos = list(combinations(dezenas, 6))
            jogos_ok = [list(c) for c in combos if min_p <= sum(1 for x in c if x%2==0) <= max_p]
            import random; random.shuffle(jogos_ok)
            return jogos_ok[:qtd]
        except: return []
    
    jogos = gerar_balanceado(dezenas_input, num_jogos, min_pares, max_pares)
    
    if jogos:
        st.success(f"✅ **{len(jogos)} jogos prontos!**")
        
        # DataFrame Mobile
        df = [{"#": i+1, **{f"N{j+1}": f"{n:02d}" for j,n in enumerate(sorted(jogo))}} 
              for i,jogo in enumerate(jogos)]
        st.dataframe(df, use_container_width=True, height=400)
        
        # CSV DOWNLOAD (semicolons Excel)
        csv_data = io.StringIO()
        writer = csv.writer(csv_data, delimiter=';')
        writer.writerow(["Jogo"] + [f"Dezena{i+1}" for i in range(6)])
        for row in df: writer.writerow([row["#"]] + [row[f"N{i+1}"] for i in range(6)])
        
        st.download_button(
            "💾 PLANILHA EXCEL", csv_data.getvalue(),
            f"mega_sena_{len(jogos)}_jogos.csv", "text/csv"
        )
    else:
        st.error("❌ Ajuste dezenas/filtros!")

st.markdown("---")
st.caption("📱 **Otimizado Mobile** | ROSECON Engenharia")
