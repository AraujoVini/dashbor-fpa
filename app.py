import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard FP&A — VS Consultoria Financeira", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

@st.cache_data
def carregar_dados(arquivo):
    """Carrega todas as abas do arquivo Excel"""
    xls = pd.ExcelFile(arquivo)
    
    # Lê cada aba
    df_resumo = pd.read_excel(xls, "Resumo Financeiro")
    df_resumo.columns = df_resumo.columns.str.strip()
    
    df_receitas = pd.read_excel(xls, "Receitas")
    df_receitas.columns = df_receitas.columns.str.strip()
    
    df_despesas = pd.read_excel(xls, "Despesas Operacionais")
    df_despesas.columns = df_despesas.columns.str.strip()
    
    df_fluxo = pd.read_excel(xls, "Fluxo de Caixa")
    df_fluxo.columns = df_fluxo.columns.str.strip()
    
    df_indicadores = pd.read_excel(xls, "Indicadores")
    df_indicadores.columns = df_indicadores.columns.str.strip()
    
    return df_resumo, df_receitas, df_despesas, df_fluxo, df_indicadores

def gerar_kpis(df_resumo, df_fluxo, df_indicadores, mes_selecionado, coluna_mes_resumo, coluna_mes_fluxo):
    """Gera os KPIs principais do dashboard"""
    try:
        # Receita Total
        receita_total = df_resumo.loc[df_resumo[coluna_mes_resumo] == mes_selecionado, 'Receita Total'].values[0]
        
        # Crescimento MoM
        idx_mes = df_resumo.index[df_resumo[coluna_mes_resumo] == mes_selecionado][0]
        if idx_mes == 0:
            crescimento_mom = 0
        else:
            receita_anterior = df_resumo.loc[idx_mes - 1, 'Receita Total']
            crescimento_mom = ((receita_total - receita_anterior) / receita_anterior) * 100
        
        # Margem Líquida Média - tenta várias possibilidades de nome
        margem_col = None
        for col in df_resumo.columns:
            if 'margem' in col.lower() and 'liquida' in col.lower():
                margem_col = col
                break
        
        if margem_col:
            margem_liquida_media = df_resumo[margem_col].mean()
        else:
            margem_liquida_media = 0
        
        # Saldo de Caixa
        saldo_caixa = df_fluxo.loc[df_fluxo[coluna_mes_fluxo] == mes_selecionado, 'Saldo Acumulado'].values[0]
        
        return receita_total, crescimento_mom, margem_liquida_media, saldo_caixa
    
    except Exception as e:
        st.error(f"Erro ao calcular KPIs: {e}")
        st.write("DataFrame Resumo:", df_resumo.head())
        return 0, 0, 0, 0

def gerar_graficos(df_resumo, df_receitas, df_fluxo, mes_selecionado, segmentos_selecionados, coluna_mes_resumo, coluna_mes_receitas, coluna_mes_fluxo):
    """Gera os gráficos do dashboard"""
    
    try:
        # 1. Gráfico de Linha - Evolução da Receita
        fig_receita_linha = px.line(
            df_resumo, 
            x=coluna_mes_resumo, 
            y='Receita Total',
            title='Evolução da Receita Total',
            markers=True
        )
        fig_receita_linha.update_layout(
            xaxis_title="Mês",
            yaxis_title="Receita (R$)",
            hovermode='x unified'
        )
    except Exception as e:
        st.error(f"Erro no gráfico de receita: {e}")
        fig_receita_linha = go.Figure()
    
    try:
        # 2. Gráfico de Barras - Receitas por Segmento
        # Detecta coluna de valor
        coluna_valor = None
        for col in df_receitas.columns:
            if 'valor' in col.lower() or col in ['Consultoria PJ', 'Consultoria PI', 'Treinamentos', 'Projetos Especiais', 'Receita Total']:
                coluna_valor = col
                break
        
        if not coluna_valor:
            # Se não encontrar, pega a primeira coluna numérica que não é o mês
            colunas_numericas = df_receitas.select_dtypes(include=['float64', 'int64']).columns
            colunas_numericas = [c for c in colunas_numericas if c != coluna_mes_receitas]
            if len(colunas_numericas) > 0:
                coluna_valor = colunas_numericas[0]
        
        if coluna_valor and 'Segmento' in df_receitas.columns:
            if segmentos_selecionados:
                df_receitas_filtrado = df_receitas[df_receitas['Segmento'].isin(segmentos_selecionados)]
            else:
                df_receitas_filtrado = df_receitas
            
            fig_receita_segmento = px.bar(
                df_receitas_filtrado,
                x=coluna_mes_receitas,
                y=coluna_valor,
                color='Segmento',
                title='Receitas por Segmento',
                barmode='group'
            )
        else:
            # Plano B: gráfico com todas as colunas numéricas
            colunas_numericas = [col for col in df_receitas.columns if col != coluna_mes_receitas and df_receitas[col].dtype in ['float64', 'int64']]
            if colunas_numericas:
                fig_receita_segmento = px.bar(
                    df_receitas,
                    x=coluna_mes_receitas,
                    y=colunas_numericas,
                    title='Receitas Detalhadas',
                    barmode='group'
                )
            else:
                fig_receita_segmento = go.Figure()
                st.warning("Não foi possível gerar o gráfico de receitas por segmento. Verifique as colunas da aba 'Receitas'.")
    
    except Exception as e:
        st.error(f"Erro no gráfico de receitas por segmento: {e}")
        st.write("Colunas disponíveis:", list(df_receitas.columns))
        fig_receita_segmento = go.Figure()
    
    try:
        # 3. Gráfico de Fluxo de Caixa
        fig_fluxo = go.Figure()
        fig_fluxo.add_trace(go.Scatter(
            x=df_fluxo[coluna_mes_fluxo], 
            y=df_fluxo['Saldo Acumulado'],
            mode='lines+markers',
            name='Saldo Acumulado',
            line=dict(color='green', width=3)
        ))
        fig_fluxo.update_layout(
            title='Fluxo de Caixa Acumulado',
            xaxis_title='Mês',
            yaxis_title='Saldo (R$)'
        )
    except Exception as e:
        st.error(f"Erro no gráfico de fluxo de caixa: {e}")
        fig_fluxo = go.Figure()
    
    return fig_receita_linha, fig_receita_segmento, fig_fluxo

# ============= INTERFACE PRINCIPAL =============

st.title("📊 Dashboard FP&A — VS Consultoria Financeira")
st.markdown("---")

# Sidebar - Upload de arquivo
with st.sidebar:
    st.header("⚙️ Configurações")
    arquivo_upload = st.file_uploader(
        "Faça upload do arquivo Excel", 
        type=['xlsx', 'xls']
    )

# Verifica se há arquivo carregado
if arquivo_upload is not None:
    try:
        # Carrega os dados
        df_resumo, df_receitas, df_despesas, df_fluxo, df_indicadores = carregar_dados(arquivo_upload)
        
        # Debug: Mostra as colunas carregadas E IDENTIFICA O NOME CORRETO DA COLUNA DE MÊS
        with st.expander("🔍 Ver colunas carregadas"):
            st.write("**Resumo Financeiro:**", list(df_resumo.columns))
            st.write("**Receitas:**", list(df_receitas.columns))
            st.write("**Despesas:**", list(df_despesas.columns))
            st.write("**Fluxo de Caixa:**", list(df_fluxo.columns))
            st.write("**Indicadores:**", list(df_indicadores.columns))
        
        # Identifica automaticamente a coluna de mês
        possíveis_nomes_mes = ['Ms', 'Mês', 'Mes', 'mês', 'mes', 'MÊS', 'MES', 'Month', 'Data', 'Período']
        coluna_mes_resumo = None
        coluna_mes_receitas = None
        coluna_mes_fluxo = None
        
        for col in df_resumo.columns:
            if col in possíveis_nomes_mes or 'mes' in col.lower() or 'mês' in col.lower():
                coluna_mes_resumo = col
                break
        
        for col in df_receitas.columns:
            if col in possíveis_nomes_mes or 'mes' in col.lower() or 'mês' in col.lower():
                coluna_mes_receitas = col
                break
                
        for col in df_fluxo.columns:
            if col in possíveis_nomes_mes or 'mes' in col.lower() or 'mês' in col.lower():
                coluna_mes_fluxo = col
                break
        
        if not coluna_mes_resumo:
            st.error("❌ Coluna de mês não encontrada na aba 'Resumo Financeiro'. Colunas disponíveis: " + str(list(df_resumo.columns)))
            st.stop()
        
        if not coluna_mes_receitas:
            st.error("❌ Coluna de mês não encontrada na aba 'Receitas'. Colunas disponíveis: " + str(list(df_receitas.columns)))
            st.stop()
            
        if not coluna_mes_fluxo:
            st.error("❌ Coluna de mês não encontrada na aba 'Fluxo de Caixa'. Colunas disponíveis: " + str(list(df_fluxo.columns)))
            st.stop()
        
        # Filtros na Sidebar
        with st.sidebar:
            st.markdown("---")
            st.subheader("Filtros")
            
            # Filtro de Mês
            meses_disponiveis = df_resumo[coluna_mes_resumo].unique().tolist()
            mes_selecionado = st.selectbox("Selecione o Mês", meses_disponiveis)
            
            # Filtro de Segmento
            if 'Segmento' in df_receitas.columns:
                segmentos_disponiveis = df_receitas['Segmento'].unique().tolist()
                segmentos_selecionados = st.multiselect(
                    "Selecione os Segmentos",
                    segmentos_disponiveis,
                    default=segmentos_disponiveis
                )
            else:
                segmentos_selecionados = []
        
        # Gera KPIs
        receita_total, crescimento_mom, margem_liquida_media, saldo_caixa = gerar_kpis(
            df_resumo, df_fluxo, df_indicadores, mes_selecionado, coluna_mes_resumo, coluna_mes_fluxo
        )
        
        # Exibe KPIs
        st.subheader(f"📈 Indicadores do Mês: {mes_selecionado}")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Receita Total", f"R$ {receita_total:,.2f}")
        
        with col2:
            st.metric("Crescimento MoM", f"{crescimento_mom:.1f}%", 
                     delta=f"{crescimento_mom:.1f}%")
        
        with col3:
            st.metric("Margem Líquida Média", f"{margem_liquida_media:.1f}%")
        
        with col4:
            st.metric("Saldo de Caixa", f"R$ {saldo_caixa:,.2f}")
        
        st.markdown("---")
        
        # Gera e exibe gráficos
        fig_receita_linha, fig_receita_segmento, fig_fluxo = gerar_graficos(
            df_resumo, df_receitas, df_fluxo, mes_selecionado, segmentos_selecionados,
            coluna_mes_resumo, coluna_mes_receitas, coluna_mes_fluxo
        )
        
        # Layout dos gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig_receita_linha, use_container_width=True)
        
        with col2:
            st.plotly_chart(fig_fluxo, use_container_width=True)
        
        st.plotly_chart(fig_receita_segmento, use_container_width=True)
        
        # Tabelas de dados
        st.markdown("---")
        st.subheader("📋 Dados Detalhados")
        
        tab1, tab2, tab3 = st.tabs(["Resumo Financeiro", "Receitas", "Fluxo de Caixa"])
        
        with tab1:
            st.dataframe(df_resumo, use_container_width=True)
        
        with tab2:
            st.dataframe(df_receitas, use_container_width=True)
        
        with tab3:
            st.dataframe(df_fluxo, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
        st.info("Verifique se o arquivo Excel possui as abas corretas e os dados no formato esperado.")

else:
    st.info("👆 Faça upload de um arquivo Excel na barra lateral para começar.")
    st.markdown("""
    ### 📝 Instruções:
    O arquivo Excel deve conter as seguintes abas:
    - **Resumo Financeiro**: com colunas 'Ms', 'Receita Total', 'Margem Lquida'
    - **Receitas**: com colunas 'Ms', 'Segmento', 'Valor'
    - **Despesas Operacionais**
    - **Fluxo de Caixa**: com colunas 'Ms', 'Saldo Acumulado'
    - **Indicadores**
    """)
