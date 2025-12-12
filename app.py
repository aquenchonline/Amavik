import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
# REPLACE THIS WITH YOUR GOOGLE SHEET LINK 👇
SHEET_URL = "https://docs.google.com/spreadsheets/d/1xXXXX-YOUR-SHEET-ID-XXXXX/edit"

st.title("📝 My Google Sheets App")

# ------------------------------------------------------------------
# 1. ESTABLISH CONNECTION
# ------------------------------------------------------------------
# This looks for [connections.gsheets] in your secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# ------------------------------------------------------------------
# 2. READ DATA
# ------------------------------------------------------------------
# We explicitly pass the spreadsheet URL here to fix your error
try:
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
    st.write("### Current Data:")
    st.dataframe(data)
except Exception as e:
    st.error(f"Error reading data: {e}")
    st.stop()

# ------------------------------------------------------------------
# 3. WRITE DATA (FORM)
# ------------------------------------------------------------------
with st.form(key="entry_form"):
    st.write("### Add New Entry")
    name = st.text_input("Your Name")
    message = st.text_area("Your Message")
    submit_button = st.form_submit_button(label="Submit Data")

    if submit_button:
        try:
            # Create a new row of data as a DataFrame
            new_row = pd.DataFrame([{"Name": name, "Message": message}])
            
            # Combine the old data with the new row
            # ensure_dataframe checks if data is empty or valid
            updated_df = pd.concat([data, new_row], ignore_index=True)
            
            # Update the Google Sheet
            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)
            
            st.success("✅ Data updated successfully!")
            
            # Wait 2 seconds then rerun to show new data
            import time
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"Error updating data: {e}")
