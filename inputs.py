import streamlit as st
import pandas as pd
import yfinance as yf

st.write('# Solution using a dataframe')

if 'data' not in st.session_state:
    data = pd.DataFrame({'Stock':[],'Name':[],'colC':[],'colD':[]})
    st.session_state.data = data

data = st.session_state.data


#Opening CSV file with tickers info
with open("nasdaq_screener.csv") as f:
    ticker_names_bd = [row.split(',')[0] for row in f]

#st.write(ticker_names_bd[0:10])
#st.dataframe(data)

def add_dfForm():
    row = pd.DataFrame({'Stock':[st.session_state.input_colA],
            'Name':[st.session_state.input_colB],
            'colC':[st.session_state.input_colC],
            'colD':[st.session_state.input_colD]})
    st.session_state.data = pd.concat([st.session_state.data, row])


dfForm = st.form(key='dfForm')
with dfForm:
    dfColumns = st.columns(4)
    with dfColumns[0]:
        #st.text_input('colA', key='input_colA')
        st.selectbox(
        "Selecione um ativo",
        ticker_names_bd[1:],
        #("IWDA.L", "EIMI.L", "EMVL.L", "USSC.L", "IWVL.L"),
        #label_visibility=st.session_state.visibility,
        #disabled=st.session_state.disabled,
        #index=None,
        placeholder="IWDA.L ou EMVL.L ...",
        key='input_colA'
        )
    with dfColumns[1]:
        st.text_input('colB', key='input_colB')
    with dfColumns[2]:
        st.text_input('colC', key='input_colC')
    with dfColumns[3]:
        st.text_input('colD', key='input_colD')
    st.form_submit_button(
        on_click=add_dfForm,
        label="Add stock")

tickers = data['Stock'].values.tolist()

# Verifica se tickers foram preenchidos
if len(data['Stock'].index) != 0:
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        stock_name = stock.info['shortName']
        print(stock_name)
        data.loc[data['Stock']==ticker, ['Name']] = stock_name

    ohlc = yf.download(tickers, period="max")
    prices = ohlc["Adj Close"].dropna(how="all")

    st.dataframe(data)
    st.line_chart(pd.DataFrame(prices))

