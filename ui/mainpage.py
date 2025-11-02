import streamlit as st
import pandas as pd
import numpy as np

st.title("Kdiff UI")

st.header("Sample DataFrame")

# Create a sample DataFrame
data = {
    'first_column': list(range(1, 11)),
    'second_column': np.arange(10)
}
df = pd.DataFrame(data)

st.dataframe(df)

