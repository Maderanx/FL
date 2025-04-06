import streamlit as st
import requests
import io
import numpy as np

# Backend API URL for the local server
BACKEND_URL = "http://127.0.0.1:8000"

users = ["local_user1", "local_user2", "local_user3"]
model_states = {user: f"Trained {np.random.randint(50, 100)}%" for user in users}
user_data = {user: f"Data Samples: {np.random.randint(1000, 5000)}" for user in users}

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "file_id" not in st.session_state:
    st.session_state.file_id = None

def login():
    st.title("Local Server Client Dashboard")
    
    username = st.text_input("Username", key="username_input")
    password = st.text_input("Password", type="password", key="password_input")
    
    if st.button("Login"):
        if username in users and password == "1234":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Logged in as {username}")
            st.rerun()  # Refresh UI after login
        else:
            st.error("Invalid credentials")

def main_dashboard():
    st.title(f"Welcome, {st.session_state.username}")
    
    st.write("### Model Details")
    st.write(f"Model State: {model_states[st.session_state.username]}")
    st.write(f"User Data: {user_data[st.session_state.username]}")

    # File Upload Section
    st.write("### Upload Model File (.keras)")
    uploaded_file = st.file_uploader("Upload your trained model", type=["keras"], key="file_uploader")
    
    if uploaded_file and st.button("Upload to Local Server"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
        response = requests.post(f"{BACKEND_URL}/upload/?username={st.session_state.username}", files=files)

        if response.status_code == 200:
            st.session_state.file_id = response.json().get("file_id")
            st.success(f"File uploaded successfully! File ID: {st.session_state.file_id}")
        else:
            st.error("Upload failed.")

    # Global Model Download Section
    st.write("### Fetch Global Model")
    if st.button("Fetch Global Model"):
        response = requests.get(f"{BACKEND_URL}/download-global/", stream=True)

        if response.status_code == 200:
            downloaded_file = io.BytesIO(response.content)
            st.download_button(
                label="Download Global Model",
                data=downloaded_file,
                file_name="global_model.keras",
                mime="application/octet-stream",
            )
        else:
            st.error("Download failed. Global model not found.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.file_id = None
        st.rerun()

if __name__ == "__main__":
    if st.session_state.logged_in:
        main_dashboard()
    else:
        login()