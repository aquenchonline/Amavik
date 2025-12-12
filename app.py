import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
# 👇 REPLACE THIS WITH YOUR ACTUAL GOOGLE SHEET URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1S6xS6hcdKSPtzKxCL005GwvNWQNspNffNveI3P9zCgw/edit?gid=0#gid=0/edit"

st.set_page_config(page_title="Google Sheets App", page_icon="📝")
st.title("📝 My Google Sheets App")

# ------------------------------------------------------------------
# 1. ESTABLISH CONNECTION
# ------------------------------------------------------------------
# The error you saw usually happens if the secrets are formatted wrong.
# We use a try-except block to catch it and give you a helpful hint.
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("🚨 Connection Error!")
    st.error(f"Detailed Error: {e}")
    st.info("💡 Hint: Check your secrets.toml. Ensure 'private_key' handles newlines (\\n) correctly.")
    st.stop()

# ------------------------------------------------------------------
# 2. READ DATA
# ------------------------------------------------------------------
try:
    # We use valid_worksheet checks to avoid reading empty sheets erroneously
    data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
    
    st.write("### 📊 Current Data")
    # If data is empty, create a default dataframe
    if data.empty:
        data = pd.DataFrame(columns=["Name", "Message"])
        st.warning("Sheet is empty. Add data below!")
    
    st.dataframe(data, use_container_width=True)

except Exception as e:
    st.error(f"Error reading data: {e}")
    st.stop()

# ------------------------------------------------------------------
# 3. WRITE DATA (FORM)
# ------------------------------------------------------------------
st.divider()
st.write("### ➕ Add New Entry")

with st.form(key="entry_form"):
    name = st.text_input("Your Name")
    message = st.text_area("Your Message")
    submit_button = st.form_submit_button(label="Submit Data")

    if submit_button:
        if not name or not message:
            st.warning("⚠️ Please fill in both fields.")
        else:
            try:
                # Create a new row
                new_row = pd.DataFrame([{"Name": name, "Message": message}])
                
                # Combine old data with new data
                updated_df = pd.concat([data, new_row], ignore_index=True)
                
                # Update Google Sheets
                conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=updated_df)
                
                st.success("✅ Data saved! Refreshing...")
                
                # Wait 1 second then reload to show new data
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error updating data: {e}")
