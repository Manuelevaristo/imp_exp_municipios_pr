import streamlit as st
import pandas as pd
import plotly.graph_objects as go # Importando a biblioteca Plotly

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Comércio Exterior do Paraná",
    page_icon="📊",
    layout="wide"
)

# --- FUNÇÃO PARA CARREGAR OS DADOS (com cache para performance) ---
@st.cache_data
def carregar_dados():
    try:
        df_export = pd.read_csv("EXPORTACOES_PARANA.csv")
        df_import = pd.read_csv("IMPORTACOES_PARANA.csv")
        return df_export, df_import
    except FileNotFoundError:
        st.error("Erro: Verifique se os arquivos 'EXPORTACOES_PARANA.csv' e 'IMPORTACOES_PARANA.csv' estão na mesma pasta que o script.")
        return None, None

# --- CARREGAMENTO DOS DADOS ---
df_export, df_import = carregar_dados()

if df_export is None or df_import is None:
    st.stop()

# --- TÍTULO DA APLICAÇÃO ---
st.title('📊 Análise de Comércio Exterior dos Municípios Paranaenses')
st.markdown("Utilize o filtro na barra lateral para selecionar um município e visualizar seus dados de exportação e importação.")

# --- BARRA LATERAL (SIDEBAR) COM FILTROS ---
st.sidebar.header("Filtros")

lista_municipios = sorted(df_export['NOME_MUN'].unique())
municipio_selecionado = st.sidebar.selectbox(
    'Selecione o Município',
    options=lista_municipios
)

# --- FILTRANDO OS DADOS PELO MUNICÍPIO SELECIONADO ---
exp_mun = df_export[df_export['NOME_MUN'] == municipio_selecionado]
imp_mun = df_import[df_import['NOME_MUN'] == municipio_selecionado]

# --- PAINEL PRINCIPAL ---
st.header(f"Análise para o Município de: **{municipio_selecionado}**")

# --- 1. CÁLCULO DO SALDO COMERCIAL POR ANO ---
st.subheader("Balança Comercial Anual (em US$)")

if not exp_mun.empty or not imp_mun.empty:
    exp_anual = exp_mun.groupby('CO_ANO')['VL_FOB'].sum().reset_index().rename(columns={'VL_FOB': 'Total Exportado'})
    imp_anual = imp_mun.groupby('CO_ANO')['VL_FOB'].sum().reset_index().rename(columns={'VL_FOB': 'Total Importado'})

    balanca_anual = pd.merge(exp_anual, imp_anual, on='CO_ANO', how='outer').fillna(0)
    balanca_anual['Saldo Comercial'] = balanca_anual['Total Exportado'] - balanca_anual['Total Importado']
    balanca_anual = balanca_anual.sort_values(by='CO_ANO').set_index('CO_ANO')

    # --- GRÁFICOS MELHORADOS COM PLOTLY ---
    
    # Gráfico 1: Combinado de Barras (Exportação/Importação) e Linha (Saldo)
    fig_combo = go.Figure()

    # Adiciona barra de Exportação
    fig_combo.add_trace(go.Bar(
        x=balanca_anual.index,
        y=balanca_anual['Total Exportado'],
        name='Exportações',
        marker_color='#0068C9' # Azul
    ))
    # Adiciona barra de Importação
    fig_combo.add_trace(go.Bar(
        x=balanca_anual.index,
        y=balanca_anual['Total Importado'],
        name='Importações',
        marker_color='#FF8700' # Laranja
    ))
    # Adiciona linha do Saldo Comercial
    fig_combo.add_trace(go.Scatter(
        x=balanca_anual.index,
        y=balanca_anual['Saldo Comercial'],
        name='Saldo Comercial',
        mode='lines+markers',
        line=dict(color='gray', width=3, dash='dot')
    ))
    fig_combo.update_layout(
        title='Exportações, Importações e Saldo Comercial por Ano',
        xaxis_title='Ano',
        yaxis_title='Valor (US$)',
        barmode='group',
        legend_title_text='Legenda'
    )
    st.plotly_chart(fig_combo, use_container_width=True)


    # Gráfico 2: Focado no Saldo Comercial com cores para superávit/déficit
    st.markdown("---") # Adiciona uma linha divisória
    
    cores = ['#29AB87' if saldo >= 0 else '#E15759' for saldo in balanca_anual['Saldo Comercial']] # Verde ou Vermelho
    fig_saldo = go.Figure()
    fig_saldo.add_trace(go.Bar(
        x=balanca_anual.index,
        y=balanca_anual['Saldo Comercial'],
        name='Saldo',
        marker_color=cores
    ))
    fig_saldo.update_layout(
        title='Resultado da Balança Comercial por Ano (Superávit/Déficit)',
        xaxis_title='Ano',
        yaxis_title='Saldo (US$)'
    )
    st.plotly_chart(fig_saldo, use_container_width=True)


    # Exibindo a tabela com os valores formatados
    st.markdown("### Tabela de Dados da Balança Comercial")
    st.dataframe(balanca_anual.style.format({
        'Total Exportado': 'US$ {:,.2f}',
        'Total Importado': 'US$ {:,.2f}',
        'Saldo Comercial': 'US$ {:,.2f}'
    }))

else:
    st.warning(f"Não foram encontrados registros de comércio exterior para {municipio_selecionado}.")

# O restante do código para Top 10 produtos continua o mesmo
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Produtos Mais Exportados")
    if not exp_mun.empty:
        top_10_exp = exp_mun.groupby('NO_SH4_POR')['VL_FOB'].sum().nlargest(10).reset_index()
        top_10_exp.rename(columns={'VL_FOB': 'Valor (US$)', 'NO_SH4_POR': 'Produto'}, inplace=True)
        top_10_exp.index = top_10_exp.index + 1
        st.dataframe(top_10_exp.style.format({'Valor (US$)': '{:,.2f}'}))
    else:
        st.info("Não há dados de exportação para este município.")

with col2:
    st.subheader("Top 10 Produtos Mais Importados")
    if not imp_mun.empty:
        top_10_imp = imp_mun.groupby('NO_SH4_POR')['VL_FOB'].sum().nlargest(10).reset_index()
        top_10_imp.rename(columns={'VL_FOB': 'Valor (US$)', 'NO_SH4_POR': 'Produto'}, inplace=True)
        top_10_imp.index = top_10_imp.index + 1
        st.dataframe(top_10_imp.style.format({'Valor (US$)': '{:,.2f}'}))
    else:
        st.info("Não há dados de importação para este município.")