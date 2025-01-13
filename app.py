# streamlit_app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup

# Page config
st.set_page_config(page_title="LBridge Login", layout="wide")

# Initialize logging container at the top
log_container = st.empty()

def show_debug(message, response=None):
    """Display debug information in the UI"""
    st.write(message)
    if response:
        with st.expander("Response Details"):
            st.write(f"Status Code: {response.status_code}")
            st.write("Headers:")
            for key, value in response.headers.items():
                st.write(f"- {key}: {value}")

# Main UI
st.title("LBridge Login Test")

# Create login form
with st.form("login_form"):
    # Get credentials from secrets if available
    try:
        username = st.secrets["lbridge_credentials"]["username"]
        password = st.secrets["lbridge_credentials"]["password"]
        st.success("Loaded credentials from secrets")
    except Exception as e:
        st.warning("No secrets found, using manual input")
        username = "int-kalinov"
        password = "JimR_90%38"

    # Show the credentials in the form
    username_input = st.text_input("Username", value=username)
    password_input = st.text_input("Password", value=password, type="password")
    submit_button = st.form_submit_button("Login")

if submit_button:
    st.write("Starting login process...")
    
    try:
        # Create session with specific headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # Step 1: Get login page
        st.write("Fetching login page...")
        initial_response = session.get(
            'https://lbridge.com/Login.aspx',
            timeout=30
        )
        show_debug("Initial page response:", initial_response)

        if initial_response.status_code == 200:
            # Parse login page
            soup = BeautifulSoup(initial_response.text, 'html.parser')
            
            # Extract form fields
            form_data = {
                '__VIEWSTATE': '',
                '__VIEWSTATEGENERATOR': '',
                '__EVENTVALIDATION': '',
                'ctl00$MainContent$txtUserName': username_input,
                'ctl00$MainContent$txtPassword': password_input,
                'ctl00$MainContent$cmdSubmit': 'Submit'
            }

            # Get the actual values
            for field in form_data.keys():
                input_elem = soup.find('input', {'name': field})
                if input_elem and 'value' in input_elem.attrs:
                    form_data[field] = input_elem['value']
                    st.write(f"Found form field: {field}")

            # Show form data (excluding password)
            with st.expander("Form Data"):
                for key, value in form_data.items():
                    if 'password' not in key.lower():
                        st.write(f"{key}: {value[:50]}...")

            # Step 2: Submit login form
            st.write("Submitting login form...")
            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://lbridge.com',
                'Referer': 'https://lbridge.com/Login.aspx'
            }
            session.headers.update(login_headers)

            login_response = session.post(
                'https://lbridge.com/Login.aspx',
                data=form_data,
                timeout=30,
                allow_redirects=True
            )
            
            show_debug("Login response:", login_response)

            # Step 3: Check login result
            if login_response.status_code == 200:
                # Check for success indicators
                response_text = login_response.text
                if 'Logout.aspx' in response_text or 'Welcome' in response_text:
                    st.success("Login successful! ✅")
                else:
                    # Parse error message if any
                    error_soup = BeautifulSoup(response_text, 'html.parser')
                    error_elem = error_soup.find('span', {'id': 'MainContent_lblUserError'})
                    
                    if error_elem:
                        error_message = error_elem.text.strip()
                        st.error(f"Login failed: {error_message} ❌")
                    else:
                        # Check if still on login page
                        if 'MainContent_txtUserName' in response_text:
                            st.error("Login failed: Still on login page ❌")
                            # Show a bit of the response for debugging
                            with st.expander("Response Preview"):
                                st.code(response_text[:1000])
                        else:
                            st.error("Login failed: Unknown error ❌")
            else:
                st.error(f"Login failed: Server returned {login_response.status_code} ❌")
        else:
            st.error(f"Failed to load login page: {initial_response.status_code} ❌")

    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)} ❌")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)} ❌")
