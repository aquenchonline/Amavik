import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("📝 My Google Sheets App")

# 1. Establish the connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. READ: Fetch existing data
data = conn.read(worksheet="Sheet1") # 'Sheet1' is default
st.write("### Current Data:")
st.dataframe(data)

# 3. WRITE: Add new data via a form
with st.form(key="entry_form"):
    name = st.text_input("Your Name")
    message = st.text_area("Your Message")
    submit_button = st.form_submit_button(label="Submit Data")

    if submit_button:
        # Create a new row of data
        new_row = pd.DataFrame([{"Name": name, "Message": message}])
        
        # Combine old data with new data
        updated_df = pd.concat([data, new_row], ignore_index=True)
        
        # Update Google Sheets
        conn.update(worksheet="Sheet1", data=updated_df)
        
        st.success("Data updated successfully!")
        st.rerun()
