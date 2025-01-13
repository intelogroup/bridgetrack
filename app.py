# streamlit_app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging

# Basic page config
st.set_page_config(page_title="LBridge Login", page_icon="🔒", layout="wide")

# Initialize session state
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []

def log_debug(message):
    """Add debug message to session state"""
    st.session_state.debug_logs.append(message)
    if len(st.session_state.debug_logs) > 100:  # Keep only last 100 messages
        st.session_state.debug_logs = st.session_state.debug_logs[-100:]

class LBridgeSession:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://lbridge.com"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })

    def login(self, username, password):
        try:
            # Get login page
            log_debug("Fetching login page...")
            response = self.session.get(f"{self.base_url}/Login.aspx")
            log_debug(f"Login page status: {response.status_code}")
            
            if response.status_code != 200:
                return False, "Could not load login page"

            # Parse form
            soup = BeautifulSoup(response.text, 'html.parser')
            form_data = {
                '__VIEWSTATE': '',
                '__VIEWSTATEGENERATOR': '',
                '__EVENTVALIDATION': '',
                'ctl00$MainContent$txtUserName': username,
                'ctl00$MainContent$txtPassword': password,
                'ctl00$MainContent$cmdSubmit': 'Submit'
            }

            # Get form fields
            for field in form_data.keys():
                input_elem = soup.find('input', {'name': field})
                if input_elem and 'value' in input_elem.attrs:
                    form_data[field] = input_elem['value']
                    log_debug(f"Found field: {field}")

            # Submit login
            log_debug("Submitting login form...")
            response = self.session.post(
                f"{self.base_url}/Login.aspx",
                data=form_data,
                allow_redirects=True
            )
            
            log_debug(f"Login response status: {response.status_code}")

            # Check result
            if 'Logout.aspx' in response.text or 'Welcome' in response.text:
                log_debug("Login successful!")
                return True, "Success"
            else:
                # Check for error message
                error_elem = BeautifulSoup(response.text, 'html.parser').find(
                    'span', {'id': 'MainContent_lblUserError'}
                )
                error_msg = error_elem.text.strip() if error_elem else "Login failed"
                log_debug(f"Login failed: {error_msg}")
                return False, error_msg

        except Exception as e:
            log_debug(f"Error during login: {str(e)}")
            return False, str(e)

def main():
    st.title("LBridge Login Test")

    # Sidebar with debug info
    with st.sidebar:
        st.title("Debug Panel")
        if st.button("Clear Debug Logs"):
            st.session_state.debug_logs = []
        
        if st.session_state.debug_logs:
            st.text_area("Debug Logs", 
                        value="\n".join(st.session_state.debug_logs),
                        height=400)

    # Main login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted and username and password:
            with st.spinner("Attempting login..."):
                session = LBridgeSession()
                success, message = session.login(username, password)
                
                if success:
                    st.success("Login successful! ✅")
                else:
                    st.error(f"Login failed: {message} ❌")

if __name__ == "__main__":
    main()
