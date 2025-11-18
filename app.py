import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard FP&A — VS Consultoria Financeira", layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def carregar_dados(arquivo):
    xls = pd.ExcelFile(arquivo)
    df_resumo = pd.read_excel(xls, "Resumo Financeiro")
    df_resumo.columns = df_resumo.columns.str.strip()  # Limpa espaços antes e depois
    st.write('Colunas carregadas:', list(df_resumo.columns))  # MOSTRA NA TELA OS NOMES REAIS
    df_receitas = pd.read_excel(xls, "Receitas")
    df_despesas = pd.read_excel(xls, "Despesas Operacionais")
    df_fluxo = pd.read_excel(xls, "Fluxo de Caixa")
    df_indicadores = pd.read_excel(xls, "Indicadores")
    return df_resumo, df_receitas, df_despesas, df_fluxo, df_indicadores

def gerar_kpis(df_resumo, df_fluxo, df_indicadores, mes_selecionado):
    receita_total = df_resumo.loc[df_resumo['Ms'] == mes_selecionado, 'Receita Total'].values[0]
    idx_mes = df_resumo.index[df_resumo['Ms'] == mes_selecionado][0]
    if idx_mes == 0:
        crescimento_mom = 0
    else:
        receita_anterior = df_resumo.loc[idx_mes - 1, 'Receita Total']
        crescimento_mom = (receita_total - receita_anterior) / receita_anterior * 100
    margem_liquida_media = df_resumo['Margem Lquida'].mean()
    saldo_caixa = df_fluxo.loc[df_fluxo['Ms'] == mes_selecionado, 'Saldo Acumulado'].values[0]
    return receita_total, crescimento_mom, margem_liquida_media, saldo_caixa

def gerar_graficos(df_resumo, df_receitas, df_fluxo, mes_selecionado, segmentos_selecionados):
    fig_receita_linha = px.line
