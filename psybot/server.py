import streamlit as st
import requests
import json

# Backend API URL
BACKEND_URL = "http://127.0.0.1:8000"

def fetch_users():
    response = requests.get(f"{BACKEND_URL}/total-users/")
    if response.status_code == 200:
        return response.json().get("users", [])
    return []

def fetch_user_files(username):
    response = requests.get(f"{BACKEND_URL}/list-files/?username={username}")
    if response.status_code == 200:
        return response.json().get("files", [])
    return []


def download_file(file_id, filename):
    response = requests.get(f"{BACKEND_URL}/download/?file_id={file_id}", stream=True)
    if response.status_code == 200:
        return response.content
    return None

def server_ui():
    st.title("Federated Learning Server Dashboard")
    
    # Fetch users from the backend
    users = fetch_users()
    if not users:
        st.warning("No users found.")
        return
    
    selected_user = st.selectbox("Select User", users)
    if selected_user:
        files = fetch_user_files(selected_user)
        
        if files:
            selected_file = st.selectbox("Select File", [f"{f['filename']} (ID: {f['_id']})" for f in files])
            
            # Extract file ID
            file_id = None
            for file in files:
                if f"{file['filename']} (ID: {file['_id']})" == selected_file:
                    file_id = file['_id']
                    file_metadata = json.dumps(file, indent=4)
                    break
            
            if file_id:
                if st.button("Fetch File"):
                    file_content = download_file(file_id, selected_file)
                    if file_content:
                        st.download_button(
                            label="Download Model",
                            data=file_content,
                            file_name=selected_file.split(" (")[0],
                            mime="application/octet-stream",
                        )
                    else:
                        st.error("Failed to download file.")
                
                st.write("### File Metadata")
                st.code(file_metadata)
        else:
            st.warning("No files found for this user.")

if __name__ == "__main__":
    server_ui()