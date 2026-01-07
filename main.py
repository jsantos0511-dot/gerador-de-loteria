import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

# 1. Configuração da Página e CSS para Celular
st.set_page_config(page_title="Gerador Loteria Mobile", layout="wide")

# Este bloco CSS força as colunas a não empilharem no celular
st.markdown("""
    <style>
    [data-testid="column"] {
        width: 10% !important;
        flex: 1 1 10% !important;
        min-width: 10% !important;
        padding: 0px 1px !important;
    }
    div.stButton > button {
        padding: 5px 0px !important;
        font-size: 14px !important;
        margin-bottom: -10px;
    }
    /* Ajuste para não quebrar as colunas de configurações */
    @media (max-width: 640px) {
        .config-col [data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
            min-width: 50% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização do Estado
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador Loteria Pro")

# Layout de Colunas: No celular elas ficarão uma sob a outra, o que é ideal
col_volante, col_resultados = st.columns([0.35, 0.65], gap="medium")

with col_volante:
    st.subheader("Volante")
    
    atual = sorted(list(st.session_state.selecionados))
    qtd_sel = len(atual)
    st.progress(qtd_sel / 60, text=f"Selecionados: {qtd_sel}/60")
    
    # Lista de números mais compacta
    texto_sel = ", ".join(f"{n:02d}" for n in atual) if atual else "Selecione..."
    st.caption(f"**Números:** {texto_sel}")

    # Volante Compacto
    for linha in range(6):
        cols = st.columns(10)
        for coluna in range(10):
            numero = linha * 10 + coluna + 1
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

    st.divider()
    
    # Container para configurações (usando classe CSS para não quebrar 10 colunas aqui)
    st.markdown('<div class="config-col">', unsafe_allow_html=True)
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        dez_por_jogo = st.number_input("Dezenas/bilhete", 1, 20, 6)
        valor_unit_jogo = st.number_input("Valor Jogo R$", min_value=0.0, value=5.0, step=0.5)
    with c_in2:
        gerar_tudo = st.checkbox("Gerar TODAS", value=False)
        num_max_jogos = 1048576 if gerar_tudo else st.number_input("Qtd. Jogos", 1, 1000000, 50)
    
    st.markdown('### 🛠️ Filtros')
    f_seq = st.checkbox("🚫 Sem sequências", value=True)
    f_fin = st.checkbox("🚫 Sem finais iguais", value=True)
    f_par = st.checkbox("⚖️ Equilibrar Par/Ímpar", value=True)
    max_p = st.slider("Máximo de pares", 1, dez_por_jogo, max(1, dez_por_jogo-1))
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("❌ Limpar", use_container_width=True):
            st.session_state.selecionados = set()
            st.session_state.limpar_count += 1
            st.rerun()
    with c_btn2:
        gerar = st.button("🚀 GERAR!", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_resultados:
    st.subheader("📋 Resultados")
    
    if gerar:
        lista_final = sorted(list(st.session_state.selecionados))
        
        if len(lista_final) < dez_por_jogo:
            st.error("Selecione mais números.")
        else:
            with st.spinner("Processando..."):
                combos = combinations(lista_final, dez_por_jogo)
                jogos_processados = []
                
                for c in combos:
                    jogo = sorted(list(c))
                    if f_seq and any(jogo[n+1] == jogo[n] + 1 for n in range(len(jogo)-1)): continue
                    if f_fin:
                        finais = [n % 10 for n in jogo]
                        if finais.count(finais[0]) == len(finais): continue
                    if f_par:
                        p = len([n for n in jogo if n % 2 == 0])
                        if p > max_p or (len(jogo)-p) > max_p: continue
                    
                    jogos_processados.append(jogo)
                    if len(jogos_processados) >= num_max_jogos: break

                total_jogos = len(jogos_processados)
                investimento = total_jogos * valor_unit_jogo
                
                st.metric("Jogos", f"{total_jogos:,}".replace(",", "."))
                st.metric("Total", f"R$ {investimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                st.dataframe(jogos_processados[:1000], use_container_width=True, height=400)

                output = io.StringIO()
                output.write('\ufeff')
                writer = csv.writer(output, delimiter=';', lineterminator='\n')
                writer.writerow(["Jogo"] + [f"Bola {x+1}" for x in range(dez_por_jogo)])
                for idx, j in enumerate(jogos_processados):
                    writer.writerow([idx + 1] + [f"{n:02d}" for n in j])

                st.download_button("💾 Baixar Planilha", output.getvalue().encode('utf-8-sig'), 
                                 "jogos.csv", "text/csv", use_container_width=True)
    else:
        st.info("Selecione e clique em GERAR.")
