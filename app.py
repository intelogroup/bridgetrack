# streamlit_app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Page config
st.set_page_config(page_title="LBridge Login", layout="wide")

# Debug messages
if 'debug_messages' not in st.session_state:
    st.session_state.debug_messages = []

def add_debug(message):
    st.session_state.debug_messages.append(message)
    st.write(message)

# Main login interface
st.title("LBridge Login Test")

# Check if credentials exist in secrets
try:
    username = st.secrets["lbridge_credentials"]["username"]
    password = st.secrets["lbridge_credentials"]["password"]
    add_debug("Successfully loaded credentials from secrets")
except Exception as e:
    add_debug(f"Error loading secrets: {str(e)}")
    username = ""
    password = ""

# Login form
with st.form(key='login_form'):
    # Show credentials from secrets if available
    input_username = st.text_input("Username", value=username)
    input_password = st.text_input("Password", value=password, type="password")
    
    # Option to use secrets or input credentials
    use_secrets = st.checkbox("Use stored credentials", value=bool(username))
    
    submit_button = st.form_submit_button(label='Login')

    if submit_button:
        # Use either secrets or input credentials
        final_username = username if use_secrets else input_username
        final_password = password if use_secrets else input_password
        
        add_debug(f"Attempting login with username: {final_username}")
        
        try:
            session = requests.Session()
            
            # First request - get login page
            add_debug("Fetching login page...")
            initial_response = session.get('https://lbridge.com/Login.aspx')
            add_debug(f"Login page status code: {initial_response.status_code}")
            
            if initial_response.status_code == 200:
                # Parse the login page
                soup = BeautifulSoup(initial_response.text, 'html.parser')
                
                # Get form fields
                viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
                viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
                eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
                
                add_debug("Got form fields")
                
                # Prepare login data
                login_data = {
                    '__VIEWSTATE': viewstate,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                    '__EVENTVALIDATION': eventvalidation,
                    'ctl00$MainContent$txtUserName': final_username,
                    'ctl00$MainContent$txtPassword': final_password,
                    'ctl00$MainContent$cmdSubmit': 'Submit'
                }
                
                # Set headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://lbridge.com',
                    'Referer': 'https://lbridge.com/Login.aspx'
                }
                
                add_debug("Attempting login...")
                
                # Submit login
                login_response = session.post(
                    'https://lbridge.com/Login.aspx',
                    data=login_data,
                    headers=headers,
                    allow_redirects=True
                )
                
                add_debug(f"Login response status: {login_response.status_code}")
                
                # Check response
                if login_response.status_code == 200:
                    if 'Logout.aspx' in login_response.text:
                        st.success("Login successful!")
                        add_debug("Login successful - found Logout.aspx")
                    else:
                        error_soup = BeautifulSoup(login_response.text, 'html.parser')
                        error_elem = error_soup.find('span', {'id': 'MainContent_lblUserError'})
                        if error_elem:
                            st.error(f"Login failed: {error_elem.text.strip()}")
                            add_debug(f"Login failed: {error_elem.text.strip()}")
                        else:
                            st.error("Login failed - please check your credentials")
                            add_debug("Login failed - no specific error message found")
                else:
                    st.error(f"Login failed with status code: {login_response.status_code}")
                    add_debug(f"Login failed - unexpected status code: {login_response.status_code}")
            else:
                st.error("Could not access login page")
                add_debug(f"Failed to access login page: {initial_response.status_code}")
                
        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
            add_debug(f"Exception: {str(e)}")

# Debug section
with st.expander("Debug Information"):
    for msg in st.session_state.debug_messages:
        st.text(msg)
