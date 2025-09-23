import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO  # Necessário para manipulação de arquivos em memória

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Comércio Exterior do Paraná",
    page_icon="📊",
    layout="wide"
)

# --- MAPA DE MESES PARA MELHOR VISUALIZAÇÃO ---
meses_map = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
meses_map_rev = {v: k for k, v in meses_map.items()}

# --- FUNÇÃO DE FORMATAÇÃO PARA O PADRÃO BRASILEIRO ---
def formatar_brl(valor):
    if pd.isna(valor): return "N/A"
    return f"{valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

# --- FUNÇÃO PARA CARREGAR OS DADOS ---
@st.cache_data
def carregar_dados():
    arquivo_export = "EXPORTACOES_CONSOLIDADAS_PR.csv"
    arquivo_import = "IMPORTACOES_CONSOLIDADAS_PR.csv"
    try:
        df_export = pd.read_csv(arquivo_export)
        df_import = pd.read_csv(arquivo_import)
        df_export['VL_FOB'] = pd.to_numeric(df_export['VL_FOB'], errors='coerce').fillna(0)
        df_import['VL_FOB'] = pd.to_numeric(df_import['VL_FOB'], errors='coerce').fillna(0)
        return df_export, df_import
    except FileNotFoundError:
        st.error(f"Erro: Arquivos não encontrados!")
        return None, None

# --- FUNÇÃO PARA CRIAR AS TABELAS DE RANKING ---
def criar_tabela_top10_com_totais(df_filtrado):
    if df_filtrado.empty:
        return pd.DataFrame()
    total_geral = df_filtrado['VL_FOB'].sum()
    produtos_agrupados = df_filtrado.groupby('NO_SH4_POR')['VL_FOB'].sum().sort_values(ascending=False).reset_index()
    produtos_agrupados.rename(columns={'VL_FOB': 'Valor (US$)', 'NO_SH4_POR': 'Produto'}, inplace=True)
    top_10 = produtos_agrupados.head(10).copy()
    soma_demais = produtos_agrupados.iloc[10:]['Valor (US$)'].sum()
    linha_demais = pd.DataFrame([{'Produto': 'Demais Produtos', 'Valor (US$)': soma_demais}])
    linha_total = pd.DataFrame([{'Produto': 'TOTAL', 'Valor (US$)': total_geral}])
    tabela_final = pd.concat([top_10, linha_demais, linha_total], ignore_index=True)
    tabela_final['Percentual (%)'] = (tabela_final['Valor (US$)'] / total_geral) * 100 if total_geral > 0 else 0
    tabela_final['#'] = [str(i+1) for i in range(len(top_10))] + ['', '']
    tabela_final = tabela_final[['#', 'Produto', 'Valor (US$)', 'Percentual (%)']]
    return tabela_final

# --- NOVA FUNÇÃO PARA GERAR O ARQUIVO EXCEL EM MEMÓRIA ---
def gerar_arquivo_excel(df_exp, df_imp, municipio, periodo):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # --- Cria o cabeçalho com as informações de filtro ---
        df_info = pd.DataFrame({
            'Filtro': ['Município', 'Período'],
            'Seleção': [municipio, periodo]
        })

        # --- Planilha de Exportação ---
        df_info.to_excel(writer, sheet_name='Exportações', index=False, startrow=0)
        df_exp.to_excel(writer, sheet_name='Exportações', index=False, startrow=4) # Deixa 3 linhas de espaço

        # --- Planilha de Importação ---
        df_info.to_excel(writer, sheet_name='Importações', index=False, startrow=0)
        df_imp.to_excel(writer, sheet_name='Importações', index=False, startrow=4)
        
    return output.getvalue()


# --- CARREGAMENTO DOS DADOS ---
df_export_original, df_import_original = carregar_dados()
if df_export_original is None or df_import_original is None:
    st.stop()

# --- TÍTULO DA APLICAÇÃO ---
st.title('📊 Análise de Comércio Exterior dos Municípios Paranaenses')
st.markdown("Utilize os filtros na barra lateral para detalhar sua análise.")

# --- BARRA LATERAL (SIDEBAR) COM FILTROS ---
st.sidebar.header("Filtros")
lista_municipios = sorted(df_export_original['NOME_MUN'].unique())
municipio_selecionado = st.sidebar.selectbox('Selecione o Município', options=lista_municipios)
anos_disponiveis = sorted(pd.concat([df_export_original['CO_ANO'], df_import_original['CO_ANO']]).unique())
opcoes_ano = ["Todos os anos"] + anos_disponiveis
ano_selecionado = st.sidebar.selectbox('Selecione o Ano', options=opcoes_ano)
mes_selecionado = "Todos os meses"
if ano_selecionado != "Todos os anos":
    opcoes_mes = ["Todos os meses"] + list(meses_map.values())
    mes_selecionado = st.sidebar.selectbox('Selecione o Mês', options=opcoes_mes)

# --- LÓGICA DE FILTRAGEM DOS DADOS ---
df_export = df_export_original[df_export_original['NOME_MUN'] == municipio_selecionado]
df_import = df_import_original[df_import_original['NOME_MUN'] == municipio_selecionado]
if ano_selecionado != "Todos os anos":
    df_export = df_export[df_export['CO_ANO'] == ano_selecionado]
    df_import = df_import[df_import['CO_ANO'] == ano_selecionado]
    if mes_selecionado != "Todos os meses":
        mes_numero = meses_map_rev[mes_selecionado]
        df_export = df_export[df_export['CO_MES'] == mes_numero]
        df_import = df_import[df_import['CO_MES'] == mes_numero]

# --- PAINEL PRINCIPAL ---
st.header(f"Análise para: **{municipio_selecionado}**")
periodo_str = f"{ano_selecionado}"
if ano_selecionado != "Todos os anos" and mes_selecionado != "Todos os meses":
    periodo_str += f" - {mes_selecionado}"
st.subheader(f"Período: {periodo_str}")

# --- 1. CÁLCULO DO SALDO COMERCIAL (LÓGICA APRIMORADA) ---
# (Esta seção continua idêntica)
st.markdown("---")
st.subheader("Balança Comercial (em US$)")
if ano_selecionado == "Todos os anos":
    if not df_export.empty or not df_import.empty:
        exp_anual = df_export.groupby('CO_ANO')['VL_FOB'].sum()
        imp_anual = df_import.groupby('CO_ANO')['VL_FOB'].sum()
        balanca = pd.concat([exp_anual, imp_anual], axis=1).fillna(0)
        balanca.columns = ['Total Exportado', 'Total Importado']
        balanca['Saldo Comercial'] = balanca['Total Exportado'] - balanca['Total Importado']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=balanca.index, y=balanca['Total Exportado'], name='Exportações'))
        fig.add_trace(go.Bar(x=balanca.index, y=balanca['Total Importado'], name='Importações'))
        fig.add_trace(go.Scatter(x=balanca.index, y=balanca['Saldo Comercial'], name='Saldo', mode='lines+markers'))
        fig.update_layout(title='Evolução Anual da Balança Comercial', barmode='group')
        st.plotly_chart(fig, use_container_width=True)
elif ano_selecionado != "Todos os anos" and mes_selecionado == "Todos os meses":
    if not df_export.empty or not df_import.empty:
        st.markdown(f"#### Resumo Consolidado de {ano_selecionado}")
        total_exportado_ano = df_export['VL_FOB'].sum()
        total_importado_ano = df_import['VL_FOB'].sum()
        saldo_comercial_ano = total_exportado_ano - total_importado_ano
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Exportado no Ano", f"US$ {formatar_brl(total_exportado_ano)}")
        col2.metric("Total Importado no Ano", f"US$ {formatar_brl(total_importado_ano)}")
        col3.metric("Saldo Comercial no Ano", f"US$ {formatar_brl(saldo_comercial_ano)}")
        st.markdown("---")
        exp_mensal = df_export.groupby('CO_MES')['VL_FOB'].sum()
        imp_mensal = df_import.groupby('CO_MES')['VL_FOB'].sum()
        balanca = pd.concat([exp_mensal, imp_mensal], axis=1).fillna(0)
        balanca.columns = ['Total Exportado', 'Total Importado']
        balanca = balanca.reindex(range(1, 13), fill_value=0)
        balanca['Saldo Comercial'] = balanca['Total Exportado'] - balanca['Total Importado']
        balanca.index = balanca.index.map(meses_map)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=balanca.index, y=balanca['Total Exportado'], name='Exportações'))
        fig.add_trace(go.Bar(x=balanca.index, y=balanca['Total Importado'], name='Importações'))
        fig.add_trace(go.Scatter(x=balanca.index, y=balanca['Saldo Comercial'], name='Saldo', mode='lines+markers'))
        fig.update_layout(title=f'Evolução Mensal da Balança Comercial em {ano_selecionado}', barmode='group')
        st.plotly_chart(fig, use_container_width=True)
else:
    total_exportado = df_export['VL_FOB'].sum()
    total_importado = df_import['VL_FOB'].sum()
    saldo_comercial = total_exportado - total_importado
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Exportado no Mês", f"US$ {formatar_brl(total_exportado)}")
    col2.metric("Total Importado no Mês", f"US$ {formatar_brl(total_importado)}")
    col3.metric("Saldo Comercial no Mês", f"US$ {formatar_brl(saldo_comercial)}")

# --- 2. CÁLCULO DOS PRODUTOS MAIS EXPORTADOS E IMPORTADOS ---
st.markdown("---")
col1, col2 = st.columns(2)

# Gerando as tabelas para exibição
tabela_exp = criar_tabela_top10_com_totais(df_export)
tabela_imp = criar_tabela_top10_com_totais(df_import)

with col1:
    st.subheader("Principais Produtos Exportados")
    if not tabela_exp.empty:
        st.dataframe(tabela_exp.style.format({
            'Valor (US$)': formatar_brl,
            'Percentual (%)': lambda x: f"{formatar_brl(x)}%"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("Não há dados de exportação para a seleção atual.")

with col2:
    st.subheader("Principais Produtos Importados")
    if not tabela_imp.empty:
        st.dataframe(tabela_imp.style.format({
            'Valor (US$)': formatar_brl,
            'Percentual (%)': lambda x: f"{formatar_brl(x)}%"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("Não há dados de importação para a seleção atual.")
        
# --- NOVO: SEÇÃO DE DOWNLOAD ---
st.markdown("---")
st.subheader("📥 Download do Relatório")

# Verifica se há dados para baixar antes de mostrar o botão
if not tabela_exp.empty or not tabela_imp.empty:
    # Gera o arquivo Excel em memória
    excel_bytes = gerar_arquivo_excel(
        df_exp=tabela_exp,
        df_imp=tabela_imp,
        municipio=municipio_selecionado,
        periodo=periodo_str
    )

    # Cria um nome de arquivo dinâmico
    nome_arquivo = f"Relatorio_Comex_{municipio_selecionado.replace(' ', '_')}_{periodo_str}.xlsx"

    # Cria o botão de download
    st.download_button(
        label="Clique aqui para baixar o relatório em Excel",
        data=excel_bytes,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("Não há dados para gerar o relatório com os filtros atuais.")