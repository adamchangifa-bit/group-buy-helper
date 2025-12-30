import streamlit as st
import pandas as pd

st.set_page_config(page_title="Group Buy Helper")
st.title("Group Buy Helper")
st.write("Deployment Test - Working!")

df = pd.DataFrame({
    "Product": ["Item 1", "Item 2"],
    "Price": [100, 200]
})
st.dataframe(df)
