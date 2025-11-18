import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard FP&A — VS Consultoria Financeira", layout="wide", initial_sidebar_state="expanded")

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
    idx_mes = df_resumo.index
