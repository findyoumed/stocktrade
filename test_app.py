import streamlit as st
import pandas as pd

if 'target_ticker' not in st.session_state:
    st.session_state['target_ticker'] = ''

event = st.dataframe(
    pd.DataFrame({'티커': ['SPY', 'QQQ'], '이름': ['S&P 500', 'Nasdaq 100']}),
    on_select='rerun',
    selection_mode='single-row'
)

if len(event.selection.rows) > 0:
    selected = event.selection.rows[0]
    tkr = ['SPY', 'QQQ'][selected]
    if st.session_state['target_ticker'] != tkr:
        st.session_state['target_ticker'] = tkr
        st.rerun()

st.text_input('티커', key='target_ticker')

