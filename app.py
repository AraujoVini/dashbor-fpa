# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard FP&A — VS Consultoria Financeira", layout="wide", initial_sidebar_state="expanded")

# =========================
# Funções de leitura e cálculo
# =========================
@st.cache_data
def carregar_dados(arquivo):
    xls = pd.ExcelFile(arquivo)
    df_resumo = pd.read_excel(xls, "Resumo Financeiro")
    df_receitas = pd.read_excel(xls, "Receitas")
    df_despesas = pd.read_excel(xls, "Despesas Operacionais")
    df_fluxo = pd.read_excel(xls, "Fluxo de Caixa")
    df_indicadores = pd.read_excel(xls, "Indicadores")
    return df_resumo, df_receitas, df_despesas, df_fluxo, df_indicadores

def gerar_kpis(df_resumo, df_fluxo, df_indicadores, mes_selecionado):
    receita_total = df_resumo.loc[df_resumo['Ms'] == mes_selecionado, 'Receita Total'].values[0]
    idx_mes = df_resumo.index[df_resumo['Ms'] == mes_selecionado][0]
    # Crescimento MoM
    if idx_mes == 0:
        crescimento_mom = 0
    else:
        receita_anterior = df_resumo.loc[idx_mes - 1, 'Receita Total']
        crescimento_mom = (receita_total - receita_anterior) / receita_anterior * 100
    # Margem líquida média
    margem_liquida_media = df_resumo['Margem Lquida'].mean()
    # Saldo de caixa acumulado
    saldo_caixa = df_fluxo.loc[df_fluxo['Ms'] == mes_selecionado, 'Saldo Acumulado'].values[0]
    return receita_total, crescimento_mom, margem_liquida_media, saldo_caixa

def gerar_graficos(df_resumo, df_receitas, df_fluxo, mes_selecionado, segmentos_selecionados):
    # Gráfico de linha — Receita total por mês
    fig_receita_linha = px.line(df_resumo, x="Ms", y="Receita Total", markers=True,
                                title="Receita Total por Mês")
    # Gráfico de barras empilhadas — Receita por segmento
    df_receitas_segmentos = df_receitas[["Ms"] + segmentos_selecionados]
    fig_receita_segmento = px.bar(
        df_receitas_segmentos, x="Ms", y=segmentos_selecionados,
        title="Receita por Segmento", labels={'value': 'Receita', 'variable': 'Segmento'},
        barmode='stack'
    )
    # Gráfico waterfall — DRE simplificada
    valores_waterfall = [
        df_resumo.loc[df_resumo['Ms'] == mes_selecionado, 'Receita Total'].values[0],
        -df_resumo.loc[df_resumo['Ms'] == mes_selecionado, 'Custo dos Servios CS'].values[0],
        -df_resumo.loc[df_resumo['Ms'] == mes_selecionado, 'Despesas Operacionais'].values[0]
    ]
    texto_waterfall = ['Receita Total', 'Custos dos Serviços', 'Despesas Operacionais']
    waterfall = go.Figure(go.Waterfall(
        name = "DRE Simplificada",
        orientation = "v",
        measure = ["absolute", "relative", "relative"],
        x = texto_waterfall,
        textposition = "outside",
        y = valores_waterfall,
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    waterfall.update_layout(title="DRE Simplificada — {}".format(mes_selecionado))
    # Gráfico combinado: Entradas/Saídas/Saldo
    fig_fluxo = go.Figure()
    fig_fluxo.add_trace(go.Bar(
        x=df_fluxo['Ms'], y=df_fluxo['Entradas'], name='Entradas', marker_color='rgb(24,149,202)'
    ))
    fig_fluxo.add_trace(go.Bar(
        x=df_fluxo['Ms'], y=df_fluxo['Sadas'], name='Saídas', marker_color='rgb(255,110,110)'
    ))
    fig_fluxo.add_trace(go.Scatter(
        x=df_fluxo['Ms'], y=df_fluxo['Saldo Acumulado'], name='Saldo Acumulado',
        mode='lines+markers', marker_color='rgb(51,170,51)'
    ))
    fig_fluxo.update_layout(barmode='group', title="Fluxo de Caixa — Entradas, Saídas e Saldo")
    return fig_receita_linha, fig_receita_segmento, waterfall, fig_fluxo

# =========================
# Interface Streamlit
# =========================
st.markdown("<h1 style='text-align: left; color: #256199;'>Dashboard FP&A — VS Consultoria Financeira</h1>", unsafe_allow_html=True)
st.write("Painel interativo de análises financeiras com foco em FP&A.")

# Sidebar: upload, filtros
st.sidebar.header("Opções de Dados e Filtros")
arquivo = st.sidebar.file_uploader("Fazer upload de arquivo Excel atualizado:", type=['xlsx'])
if arquivo is None:
    arquivo = "Planilha_FP&A_Fake.xlsx"
df_resumo, df_receitas, df_despesas, df_fluxo, df_indicadores = carregar_dados(arquivo)

meses = df_resumo['Ms'].tolist()
segmentos = ['Consultoria PJ', 'Consultoria PF', 'Treinamentos', 'Projetos Especiais']
mes_selecionado = st.sidebar.selectbox("Mês de análise:", meses, index=len(meses)-1)
segmentos_selecionados = st.sidebar.multiselect("Segmentos de receita:", segmentos, default=segmentos)

# KPIs
receita_total, crescimento_mom, margem_liquida_media, saldo_caixa = gerar_kpis(df_resumo, df_fluxo, df_indicadores, mes_selecionado)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita Total", f"R$ {receita_total:,.0f}", f"{crescimento_mom:.1f}%", delta_color="inverse" if crescimento_mom < 0 else "normal")
col2.metric("Crescimento MoM", f"{crescimento_mom:.2f}%", f"vs mês anterior", delta_color="normal" if crescimento_mom >= 0 else "inverse")
col3.metric("Margem Líquida Média", f"{margem_liquida_media:.2f}%", "")
col4.metric("Saldo de Caixa", f"R$ {saldo_caixa:,.0f}", "")

# =========================
# Exibição dos Gráficos
# =========================
fig_receita_linha, fig_receita_segmento, fig_waterfall, fig_fluxo = gerar_graficos(
    df_resumo, df_receitas, df_fluxo, mes_selecionado, segmentos_selecionados
)
st.plotly_chart(fig_receita_linha, use_container_width=True)
st.plotly_chart(fig_receita_segmento, use_container_width=True)
st.plotly_chart(fig_waterfall, use_container_width=True)
st.plotly_chart(fig_fluxo, use_container_width=True)

# =========================
# Tabela final: Resumo Financeiro filtrado + download
# =========================
st.subheader("Resumo Financeiro — dados filtrados")
df_filtro = df_resumo[df_resumo["Ms"] == mes_selecionado]
st.dataframe(df_filtro)

def baixar_excel(df):
    return df.to_excel(index=False, engine='openpyxl')

st.download_button(
    label="Baixar dados filtrados em Excel",
    data=baixar_excel(df_filtro),
    file_name=f"Resumo_Financeiro_{mes_selecionado}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Código comentado para facilitar manutenção e extensões.
# Requisitos extras: layout clean, cores suaves, cards de métricas, filtros, upload e download. [file:1]
