import streamlit as st
import pandas as pd
import yfinance as yf
import time
import datetime
from datetime import datetime
from datetime import date, timedelta
import plotly.express as px

from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import CLA
from pypfopt import DiscreteAllocation
from pypfopt import EfficientFrontier


st.title('Diagnóstico de Carteira')
st.divider()


st.header("Monte sua Carteira")

if 'data' not in st.session_state:
    data = pd.DataFrame({'Stock':[],'Name':[],'%':[]})
    st.session_state.data = data

data = st.session_state.data


#Opening CSV file with tickers info
with open("nasdaq_screener.csv") as f:
    ticker_names_bd = [row.split(',')[0] for row in f]

#st.write(ticker_names_bd[0:10])
#st.dataframe(data)
tickers = data['Stock'].values.tolist()

def add_dfForm():
    row = pd.DataFrame({'Stock':[st.session_state.input_colA],
            #'Name':[st.session_state.input_colB],
            'Name':"",
            '%':[st.session_state.input_colC]})
    st.session_state.data = pd.concat([st.session_state.data, row])
    

def loading():
    with st.spinner("Carregando..."):
        time.sleep(3)

if data.empty:
    max_value_percentage = 100
    min_value_percentage = 1
else:
    max_value_percentage = 100 - int(data['%'].sum())
    min_value_percentage = 0

dfForm = st.form(key='dfForm')
with dfForm:
    dfColumns = st.columns(2)
    with dfColumns[0]:
        #st.text_input('colA', key='input_colA')
        st.selectbox(
        "Selecione um ativo",
        sorted(set(ticker_names_bd[1:]) - set(tickers)),
        #("IWDA.L", "EIMI.L", "EMVL.L", "USSC.L", "IWVL.L"),
        #label_visibility=st.session_state.visibility,
        #disabled=st.session_state.disabled,
        #index=None,
        placeholder="Entre um ticker do Yahoo Finance...",
        key='input_colA'
        )
    #with dfColumns[1]:
    #    st.text_input('colB', key='input_colB')
    with dfColumns[1]:
        #st.text_input('%', key='input_colC')
        st.number_input('%', 
                        min_value=min_value_percentage, 
                        max_value= max_value_percentage, 
                        value='min', 
                        key='input_colC')
    st.form_submit_button(
        on_click=add_dfForm,
        label="Adicionar Ativo")

# Verifica se tickers foram preenchidos
if len(data['Stock'].index) != 0:
    loading()
    msg = st.success("Download concluído com sucesso: Importando dados...")
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        stock_name = stock.info['shortName']
        print(stock_name)
        data.loc[data['Stock']==ticker, ['Name']] = stock_name

  

    ohlc = yf.download(tickers, period="max")
    prices = ohlc["Adj Close"].dropna(how="all")
    
    msg.empty() # Clear the alert
    st.subheader("Carteira")
    #col1, col2 = st.columns([3,1])
    #col1.st.dataframe(data)
    st.dataframe(data)

    fig_pie_carteira = px.pie(data, values='%', names='Stock')
    #col2.st.plotly_chart(fig_pie_carteira, use_container_width=True)
    st.plotly_chart(fig_pie_carteira, use_container_width=True)


    st.subheader("Histórico de Preços dos Ativos")
    st.line_chart(pd.DataFrame(prices))

    #Backtesting

    if len(data.index) > 1:
        st.divider()
        st.header('Backtesting')
        

        
        today = datetime.today()
        default_date = today - timedelta(days=365)

        col3, col4 = st.columns([1, 1])

        with col3:
            begin_date = st.date_input(
                "Início do Backtest", 
                value=default_date,
                format="DD/MM/YYYY",
                )
            
        with col4:
            init_investment = st.number_input("Investimento inicial", value=10000, placeholder="Digite um numero...")

        df_prices = prices.loc[begin_date:datetime.today()]
        cum_return  = df_prices.copy()


        # Calculate value of initial investment of 10K in the Portfolio
        

        # Index
        spy = yf.download("spy", start=begin_date, end=datetime.today())
        #st.line_chart(spy['Adj Close'])
        spy['cum_return'] = (1+spy['Adj Close'].pct_change()).cumprod()

        for column in prices:
            cum_return[column] = (1+ cum_return[column].pct_change()).cumprod()
        
        cum_return = cum_return.fillna(1)

        alloc = list(data['%']/100)
        value = init_investment*cum_return.mul(alloc, axis=1)
        value['total'] = value.sum(axis=1).round(2)

        spy_total = init_investment*spy['cum_return']
        
        value.iloc[[0],[len(tickers)]] = init_investment
        value['Cum Return'] = value['total']/value.iloc[0]['total']

        fig = px.line(value, x=value.index, y="total", title='Portfolio vs. Benchmark')
        fig.add_scatter(x=spy.index, y=spy_total, mode='lines',name="SPY")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.header('Análise Quantitativa')

        st.subheader("Martriz de Covariância")

        st.markdown("Por motivos discutidos nos documentos, a matriz de covariância de amostra não deve ser sua escolha padrão. Acho que uma opção melhor é o encolhimento de Ledoit-Wolf, que reduz os valores extremos na matriz de covariância. Na imagem abaixo, podemos ver que há menos pontos brilhantes fora da diagonal")
        sample_cov = risk_models.sample_cov(prices, frequency=252)
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()

        fig = px.imshow(S,text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Estimativa de Retorno")

        st.markdown("Neste modelo usaremos os retornos do CAPM, que pretende ser um pouco mais estável do que o retorno histórico médio padrão.")
        mu = expected_returns.capm_return(prices).round(2)
        mu.plot.barh(figsize=(10,6)).set_title('Retorno no Modelo CAPM')
        st.bar_chart(mu)

        st.subheader("Max Sharpe")
        col5, col6 = st.columns([1, 2])
        
        cla = CLA(mu, S)
        cla.max_sharpe()
        ef_text = cla.portfolio_performance(verbose=True)
        with col5:
            
            retorno_esperado = ef_text[0] 
            volatilidade = ef_text[1]
            sharpe_ratio = ef_text[2] 

            st.markdown(f"O portfólio que maximiza o índice Sharpe é mostrado ao lado:")
            st.markdown(f"| Retorno anual: {retorno_esperado:.2%}")
            st.markdown(f"| Volatilidade: {volatilidade:.2%}")
            st.markdown(f"| Sharpe Ratio: {sharpe_ratio:.2f}")
        
        ef = EfficientFrontier(mu, S)  # weight_bounds automatically set to (0, 1)
        ef.max_sharpe()
        weights = ef.clean_weights()
        weights_series = list(weights.items())

        df_sharpe_portfolio = pd.DataFrame(weights_series)
        df_sharpe_portfolio = df_sharpe_portfolio.rename(columns={0: 'Ativo', 1: 'Percentual'})
        with col6:
            fig_pie_sharpe = px.pie(df_sharpe_portfolio[df_sharpe_portfolio['Percentual']>0], values='Percentual', names='Ativo')
            st.plotly_chart(fig_pie_sharpe, use_container_width=True)

    else:
        st.divider()
        st.subheader('Backtesting')
        st.warning('Mínimo de dois ativos para Backtesting', icon="⚠️")

        
