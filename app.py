# streamlit_app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup

def init_session_state():
    if 'debug' not in st.session_state:
        st.session_state.debug = []

def add_debug(message):
    st.session_state.debug.append(message)

class LBridgeLogin:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })

    def attempt_login(self, username, password):
        try:
            # Step 1: Get initial page and form tokens
            add_debug("Fetching initial page...")
            response = self.session.get('https://lbridge.com/Login.aspx')
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract form fields
            form_data = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': soup.find('input', {'name': '__VIEWSTATE'})['value'],
                '__VIEWSTATEGENERATOR': soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value'],
                '__EVENTVALIDATION': soup.find('input', {'name': '__EVENTVALIDATION'})['value'],
                'ctl00$MainContent$txtUserName': username,
                'ctl00$MainContent$txtPassword': password,
                'ctl00$MainContent$cmdSubmit': 'Submit'
            }

            add_debug("Form data prepared")

            # Step 2: Submit login form
            add_debug("Submitting login form...")
            login_response = self.session.post(
                'https://lbridge.com/Login.aspx',
                data=form_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://lbridge.com',
                    'Referer': 'https://lbridge.com/Login.aspx'
                }
            )

            # Check for success/error
            if login_response.status_code == 200:
                result_soup = BeautifulSoup(login_response.text, 'html.parser')
                error_elem = result_soup.find('span', {'id': 'MainContent_lblUserError'})
                
                if 'Logout.aspx' in login_response.text:
                    add_debug("Login successful!")
                    return True, "Success"
                elif error_elem and error_elem.text:
                    add_debug(f"Login error: {error_elem.text.strip()}")
                    return False, error_elem.text.strip()
                else:
                    add_debug("Login failed - still on login page")
                    return False, "Invalid credentials"
            else:
                add_debug(f"HTTP Error: {login_response.status_code}")
                return False, f"Server error: {login_response.status_code}"

        except Exception as e:
            add_debug(f"Exception: {str(e)}")
            return False, str(e)

def main():
    st.set_page_config(page_title="LBridge Login", layout="wide")
    init_session_state()

    st.title("LBridge Login")

    # Get credentials
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    # Debug expander
    with st.expander("Debug Info", expanded=True):
        for msg in st.session_state.debug:
            st.text(msg)

    if st.button("Login"):
        if username and password:
            login_handler = LBridgeLogin()
            success, message = login_handler.attempt_login(username, password)
            
            if success:
                st.success("Login successful! ✅")
            else:
                st.error(f"Login failed: {message} ❌")
        else:
            st.warning("Please enter both username and password")

if __name__ == "__main__":
    main()
