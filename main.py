import streamlit as st
import csv
from itertools import combinations
import io
import random
import math

# Configuração da Página
st.set_page_config(page_title="Gerador Loteria Pro", layout="wide")

# Inicialização do Estado (State Management)
if 'selecionados' not in st.session_state:
    st.session_state.selecionados = set()
if 'limpar_count' not in st.session_state:
    st.session_state.limpar_count = 0

st.title("🎰 Gerador de Combinações Profissional")

# Layout de Colunas: 35% Volante | 65% Resultados
col_volante, col_resultados = st.columns([0.35, 0.65], gap="large")

with col_volante:
    st.subheader("Volante de Seleção")
    
    # Progresso e Lista de Selecionados
    atual = sorted(list(st.session_state.selecionados))
    qtd_sel = len(atual)
    st.progress(qtd_sel / 60, text=f"Selecionados: {qtd_sel} de 60")
    st.info(", ".join(f"{n:02d}" for n in atual) if atual else "Selecione as dezenas no volante")

    # Construção do Volante (6x10)
    with st.container():
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
    
    # Configurações de Jogo e Valor
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        dez_por_jogo = st.number_input("Dezenas por bilhete", 1, 20, 6)
        valor_unit_jogo = st.number_input("Valor por jogo (R$)", min_value=0.0, value=5.0, step=0.50)
    with c_in2:
        gerar_tudo = st.checkbox("Gerar TODAS as possíveis", value=False)
        num_max_jogos = 1048576 if gerar_tudo else st.number_input("Qtd. de jogos desejada", 1, 1000000, 50)

    # Painel de Filtros
    st.markdown("### 🛠️ Filtros Inteligentes")
    f_seq = st.checkbox("🚫 Sem números sequenciais", value=True)
    f_fin = st.checkbox("🚫 Sem finais todos iguais", value=True)
    f_par = st.checkbox("⚖️ Equilibrar Pares/Ímpares", value=True)
    max_p = st.slider("Máximo de pares permitidos", 1, dez_por_jogo, dez_por_jogo-1 if dez_por_jogo > 1 else 1)
    
    st.divider()
    
    # Botões de Controle
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("❌ Limpar Seleção", use_container_width=True):
            st.session_state.selecionados = set()
            st.session_state.limpar_count += 1
            st.rerun()
    with c_btn2:
        gerar = st.button("🚀 GERAR JOGOS!", type="primary", use_container_width=True)

with col_resultados:
    st.subheader("📋 Painel de Resultados")
    
    if gerar:
        lista_final = sorted(list(st.session_state.selecionados))
        
        if len(lista_final) < dez_por_jogo:
            st.error(f"Selecione no mínimo {dez_por_jogo} números.")
        else:
            with st.spinner("Filtrando e processando combinações..."):
                combos = combinations(lista_final, dez_por_jogo)
                jogos_processados = []
                
                for c in combos:
                    jogo = sorted(list(c))
                    
                    # Aplicação do Filtro Sequencial
                    if f_seq and any(jogo[n+1] == jogo[n] + 1 for n in range(len(jogo)-1)):
                        continue
                    
                    # Aplicação do Filtro de Finais
                    if f_fin:
                        finais = [n % 10 for n in jogo]
                        if finais.count(finais[0]) == len(finais):
                            continue
                            
                    # Aplicação do Filtro Par/Ímpar
                    if f_par:
                        p = len([n for n in jogo if n % 2 == 0])
                        i = len(jogo) - p
                        if p > max_p or i > max_p:
                            continue
                    
                    jogos_processados.append(jogo)
                    if len(jogos_processados) >= num_max_jogos:
                        break

                # Cálculos Financeiros e Métricas
                total_jogos = len(jogos_processados)
                investimento = total_jogos * valor_unit_jogo
                
                m1, m2 = st.columns(2)
                m1.metric("Jogos Gerados", f"{total_jogos:,}".replace(",", "."))
                m2.metric("Investimento Total", f"R$ {investimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                # Tabela de Visualização (Top 1000)
                titulos = [f"Bola {x+1}" for x in range(dez_por_jogo)]
                st.dataframe(jogos_processados[:1000], use_container_width=True, height=500)
                if total_jogos > 1000:
                    st.caption("Nota: A visualização mostra os primeiros 1.000 jogos. O download contém a lista completa.")

                # Preparação do CSV para Download (Padrão Excel BR)
                output = io.StringIO()
                output.write('\ufeff')
                writer = csv.writer(output, delimiter=';', lineterminator='\n')
                writer.writerow(["Jogo"] + titulos)
                for idx, j in enumerate(jogos_processados):
                    writer.writerow([idx + 1] + [f"{n:02d}" for n in j])

                st.download_button(
                    label="💾 Baixar Planilha Completa (Excel/CSV)",
                    data=output.getvalue().encode('utf-8-sig'),
                    file_name="meus_jogos_filtrados.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.info("Aguardando comando... Selecione as dezenas e clique em GERAR JOGOS.")
