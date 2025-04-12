import streamlit as st
import streamlit.components.v1 as stc
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta


# functions
HTML_FUNCTION = f"""
<div style="padding: 20px;
            background-color: #0D47A1;
            color: white;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            text-align: Center;
            font-weight: bold;
            font-size: 26px;">
    {"Análise de Ações"}
</div>
"""
@st.cache_data()
def get_acao(mercado,acao,inicio,final):
    if mercado == 'Brasil':
        acao = acao +'.SA'
    else:
        acao = acao
    dat = yf.Ticker(acao)
    data = dat.history(start=inicio,end=final)
    data = data.reset_index()
    data = data[['Date','Close']]
    return data

@st.cache_data()
def get_info_acao(mercado,acao):
    if mercado == 'Brasil':
        acao = acao +'.SA'
    else:
        acao = acao
    dat = yf.Ticker(acao)
    dict_info = dat.info
    chaves_desejadas = ['address1','city', 'country','state','website','industry',
        'industryKey','sectorKey','longBusinessSummary','fullTimeEmployees','overallRisk']

    novo_dict = {chave: dict_info[chave] for chave in chaves_desejadas}
    return novo_dict

@st.cache_data()
def get_bench(bench,inicio,final):
    dat = yf.Ticker(bench)
    data = dat.history(start=inicio,end=final)
    data = data.reset_index()
    data['ativo'] = bench
    data = data[['Date','ativo','Close']]
    return data

def calcula_volatilidade(df):
    df['retorno_diario'] = df['Close'].pct_change()
    vol = np.std(df['retorno_diario']) * np.sqrt(252)
    return vol

def calcula_beta(df,bench_name):
    df_pivot = df.pivot(index='Date', columns='ativo', values='Close')
    returns = df_pivot.pct_change().dropna()
    benchmark_name = bench_name

    ret_benchmark = returns[benchmark_name]

    betas = {}

    for ativo in returns.columns:
        if ativo != benchmark_name:
            cov = np.cov(returns[ativo], ret_benchmark)[0][1]
            var = np.var(ret_benchmark)
            beta = cov / var
            betas[ativo] = beta
    df_betas = pd.DataFrame.from_dict(betas, orient='index', columns=['Beta'])
    df_betas = df_betas.reset_index()
    df_betas.columns = ['ativo','beta']
    return df_betas

def calcula_retorno(df,data_fim,mercado):
    n_acoes = df['ativo'].unique().tolist()
    df_retornos = pd.DataFrame()
    for ativo in n_acoes:
        df_copy = df[df['ativo'] == ativo]
        for dias_atras in range(4):
            if mercado == 'Brasil':
                data_busca = pd.to_datetime(data_fim - relativedelta(days=dias_atras)).tz_localize('America/Sao_Paulo')
            else:
                data_busca = pd.to_datetime(data_fim - relativedelta(days=dias_atras)).tz_localize('America/New_York')
            filtro = df_copy.loc[df_copy['Date'] == data_busca]

            if not filtro.empty:
                preco_inicial = filtro['Close'].iloc[0]
                preco_final = df_copy['Close'].iloc[-1]
                retorno = (preco_final / preco_inicial) - 1

        df_nova = pd.DataFrame({'ativo':[ativo],'retorno':[retorno]})
        if len(df_retornos)>= 1:
            df_retornos = pd.concat([df_retornos,df_nova])
        else:
            df_retornos = df_nova
    return df_retornos

def matriz_correlacao(df):
    df_pivot = df.pivot(index='Date', columns='ativo', values='Close')
    df_returns = df_pivot.pct_change().dropna()
    correlation_matrix = df_returns.corr()
    return correlation_matrix

def formata_html_correlacao(df):
    # Montar HTML da tabela
    html = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th {
            color: black;
            border: 1px solid blue;
            padding: 8px;
            background-color: #f0f0f0;
        }
        td {
            border: 1px solid blue;
            padding: 8px;
            text-align: center;
        }
    </style>
    <table>
        <tr>
            <th></th>
    """

    # Cabeçalho
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr>"

    # Linhas com destaque na diagonal
    for i, row in enumerate(df.index):
        html += f"<tr><th>{row}</th>"
        for j, val in enumerate(df.loc[row]):
            color = 'blue' if i == j else 'black'
            html += f"<td style='color:{color}'>{val:.2f}</td>"
        html += "</tr>"
    html += "</table>"
    return html

# main (pages)
def main():
    st.set_page_config(page_title="Análise de ações")
    stc.html(HTML_FUNCTION)
    home = st.Page(home_func,title="Informações")
    individual = st.Page(ind_func,title="Análise Individual")
    indicadores = st.Page(indicadores_func,title="Indicadores")
    about = st.Page(about_func,title="Sobre")

    pg = st.navigation({"Home":[home],"Análises":[individual,indicadores,about]})
    pg.run()
    


def home_func():
    st.markdown("## Funcionalidades")
    st.text("Análise individual de ações. Informações sobre a empresa 📈")
    st.text("Análise de alguns indicadores da empresa. Retorno, betas e demais... 📊")

def ind_func():
    st.subheader("Informações sobre a ação / Empresa")
    mercado = st.sidebar.selectbox("Escolha o mercado que deseja verificar:",['Brasil','EUA'])
    data_inicio = st.sidebar.date_input("Data Inicial da Análise",format="DD/MM/YYYY")
    data_final = st.sidebar.date_input("Data Final da Análise",format="DD/MM/YYYY")
    acao = st.text_input("Ação a verificar",placeholder="Escreva aqui o nome da ação")
    #acao = st.text_input("Ação a verificar")
    if len(acao) >=1:
        infos = get_info_acao(mercado,acao)
        with st.expander("Informações da empresa"):
            
            st.text(f"Resumo da empresa: ")
            st.markdown(f"*{infos['longBusinessSummary']}*")
            st.markdown("")
            col1,col2 = st.columns(2)
            with col1:
                st.markdown(f"###### País : *{infos['country']}*")
                st.markdown(f"###### Estado : *{infos['state']}*")
                st.markdown(f"###### Cidade : *{infos['city']}*")
                st.markdown(f"###### Endereço : *{infos['address1']}*")
                st.markdown(f"###### Site : *{infos['website']}*")
            
            with col2:
                st.markdown(f"###### Indústria : *{infos['industry']}*")
                st.markdown(f"###### Indústria chave : *{infos['industryKey']}*")
                st.markdown(f"###### Setor : *{infos['sectorKey']}*")  
                st.markdown(f"###### Número de Empregados : *{infos['fullTimeEmployees']}*")
                st.markdown(f"###### Risco : *{infos['overallRisk']}*")

        with st.expander("Histórico de Preços"):
            df_precos = get_acao(mercado,acao,data_inicio,data_final)
            df_precos['Date'] = pd.to_datetime(df_precos['Date']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_precos,hide_index=True,use_container_width=True)
            df_csv = df_precos.to_csv()
            st.download_button("Baixar histórico de preços",data=df_csv,file_name=f'historico_{acao}.csv')

        with st.expander("Rentabilidade no período"):
            rentabilidade = ((df_precos['Close'].iloc[-1]/ df_precos['Close'].iloc[0])-1) * 100
            st.markdown(f"**Rentabilidade**: {round(rentabilidade,4)}%")
            volatilidade = calcula_volatilidade(df_precos) * 100
            st.markdown(f"**Volatilidade Anualizada**: {round(volatilidade,4)}%")

        with st.expander("Gráfico de Preços"):
            fig = px.line(df_precos,x='Date', y='Close', title='Preço de Fechamento')
            st.plotly_chart(fig)

def indicadores_func():
    st.subheader("Indicadores de Mercado")
    mercado = st.sidebar.selectbox("Escolha o mercado que deseja verificar:",['Brasil','EUA'])
    data_inicio = st.sidebar.date_input("Data Inicial da Análise",format="DD/MM/YYYY")
    data_final = st.sidebar.date_input("Data Final da Análise",format="DD/MM/YYYY")
    if mercado == 'Brasil':
        lista_acoes = ['PETR4','VALE3','WEGE3','BBSA3','ITUB4','B3SA3','BPAC11','LREN3','GGBR4','CSAN3']
        bench = get_bench('^BVSP',data_inicio,data_final)
        bench['Date'] = pd.to_datetime(bench['Date']).dt.strftime('%d/%m/%Y')
        bench_name = '^BVSP'
    else:
        lista_acoes = ['MSFT','META','TSLA','AAPL','GOOGL','AMZN','NFLX']
        bench = get_bench('^GSPC',data_inicio,data_final)
        bench['Date'] = pd.to_datetime(bench['Date']).dt.strftime('%d/%m/%Y')
        bench_name = '^GSPC'
    
    lista_acao = st.multiselect("Selecione as ações para verificar informações",options=lista_acoes,placeholder="Escolha as ações")
    df_acoes = pd.DataFrame()
    if len(lista_acao)>=1:
        for acao in lista_acao:
            df_precos = get_acao(mercado,acao,data_inicio,data_final)
            df_precos['ativo'] = acao
            df_precos['Date'] = pd.to_datetime(df_precos['Date']).dt.strftime('%d/%m/%Y')
            df_acoes = pd.concat([df_acoes,df_precos])

        with st.expander("Histórico de Preços"):
            df_acoes = df_acoes[['Date','ativo','Close']]
            st.dataframe(df_acoes,hide_index=True,use_container_width=True)
            df_csv = df_acoes.to_csv()
            st.download_button("Baixar histórico de preços",data=df_csv,file_name=f'historico_multiacoes.csv')

        with st.expander("Betas (Com índice de bolsa)"):
            df_junto = pd.concat([df_acoes,bench])
            #st.dataframe(df_junto)
            betas = calcula_beta(df_junto,bench_name)
            for index,ativo in betas.iterrows():
                st.markdown(f"**{ativo['ativo']}** = {round(ativo['beta'],3)}")
            #st.write(betas)

        with st.expander("Rentabilidades"):
            tab1,tab2,tab3,tab4 = st.tabs(["1 semana","1 mês","No ano","No período"])
            date1w = data_final - relativedelta(days=7)
            date1m = data_final - relativedelta(months=1)
            ano_final = data_final.year
            date1y = datetime(ano_final - 1,12,31)
            data_periodo = data_final - relativedelta(years=1)

            df_acoes2 = pd.DataFrame()
            for acao in lista_acao:
                df_precos2 = get_acao(mercado,acao,data_periodo,data_final)
                df_precos2['ativo'] = acao
                df_acoes2 = pd.concat([df_acoes2,df_precos2])
            
            df_acoes2['Date'] = pd.to_datetime(df_acoes2['Date'])
            
            rent1w = calcula_retorno(df_acoes2,date1w,mercado)
            #st.dataframe(rent1w)
            with tab1:
                for index,value in rent1w.iterrows():
                    ativo = value['ativo']
                    retorno = round(value['retorno'] * 100,4)
                    st.markdown(f"**{ativo}** : {retorno}%")

            rent1m = calcula_retorno(df_acoes2,date1m,mercado)
            with tab2:
                for index,value in rent1m.iterrows():
                    ativo = value['ativo']
                    retorno = round(value['retorno'] * 100,4)
                    st.markdown(f"**{ativo}** : {retorno}%")
            
            rent1y = calcula_retorno(df_acoes2,date1y,mercado)
            with tab3:
                for index,value in rent1y.iterrows():
                    ativo = value['ativo']
                    retorno = round(value['retorno'] * 100,4)
                    st.markdown(f"**{ativo}** : {retorno}%")
            
            rentper = calcula_retorno(df_acoes2,data_inicio,mercado)
            with tab4:
                for index,value in rentper.iterrows():
                    ativo = value['ativo']
                    retorno = round(value['retorno'] * 100,4)
                    st.markdown(f"**{ativo}** : {retorno}%")
        

        with st.expander("Correlação"):
            matriz_correl = matriz_correlacao(df_acoes)
            html = formata_html_correlacao(matriz_correl)
            st.markdown(formata_html_correlacao(matriz_correl), unsafe_allow_html=True)

def about_func():
    st.subheader("Sobre")
    st.text("Construído com Streamlit")
    st.text("Pedro Cervo / 2025")
    st.text("Contato: phcervo@gmail.com")



if __name__ == '__main__':
    main()