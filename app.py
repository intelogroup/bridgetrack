# app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LBridgeLogin")

class LBridgeSession:
    def __init__(self):
        """Initialize session with optimized headers"""
        self.session = requests.Session()
        self.base_url = "https://lbridge.com"
        
        # Optimized headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'DNT': '1'
        })
        self.login_status = False
        self.last_error = None

    def debug_response(self, response, context=""):
        """Log response details for debugging"""
        logger.debug(f"\n=== {context} ===")
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"URL: {response.url}")
        logger.debug("Headers:")
        for key, value in response.headers.items():
            logger.debug(f"  {key}: {value}")
        logger.debug("Cookies:")
        for cookie in response.cookies:
            logger.debug(f"  {cookie.name}: {cookie.value}")

    def get_form_fields(self, username, password):
        """Get login page and extract form fields"""
        try:
            url = f"{self.base_url}/Login.aspx"
            response = self.session.get(url, timeout=10)
            self.debug_response(response, "Initial Page Load")
            
            if response.status_code != 200:
                raise Exception(f"Failed to load login page: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all form fields
            form_fields = {
                '__VIEWSTATE': '',
                '__VIEWSTATEGENERATOR': '',
                '__EVENTVALIDATION': '',
                'ctl00$MainContent$txtUserName': username,
                'ctl00$MainContent$txtPassword': password,
                'ctl00$MainContent$cmdSubmit': 'Submit'
            }
            
            # Update form fields with actual values
            for field in form_fields.keys():
                input_elem = soup.find('input', {'name': field})
                if input_elem and 'value' in input_elem.attrs:
                    form_fields[field] = input_elem['value']
                    logger.debug(f"Found field {field}: {form_fields[field][:20]}...")
            
            return form_fields
            
        except Exception as e:
            logger.error(f"Error getting form fields: {str(e)}")
            raise

    def login(self, username, password):
        """Attempt login with proper error handling"""
        try:
            # Reset session state
            self.login_status = False
            self.last_error = None
            
            # Get form fields
            logger.info("Getting login form fields...")
            form_data = self.get_form_fields(username, password)
            
            # Attempt login
            logger.info("Submitting login form...")
            response = self.session.post(
                f"{self.base_url}/Login.aspx",
                data=form_data,
                timeout=10,
                allow_redirects=True
            )
            
            self.debug_response(response, "Login Response")
            
            # Check for successful login
            if response.status_code == 200:
                if 'Logout.aspx' in response.text or 'Welcome' in response.text:
                    logger.info("Login successful!")
                    self.login_status = True
                    return True
                else:
                    # Check for error message
                    soup = BeautifulSoup(response.text, 'html.parser')
                    error_elem = soup.find('span', {'id': 'MainContent_lblUserError'})
                    if error_elem:
                        self.last_error = error_elem.text.strip()
                    else:
                        self.last_error = "Login failed - Invalid credentials"
                    logger.error(f"Login failed: {self.last_error}")
                    return False
            else:
                self.last_error = f"Server returned status code: {response.status_code}"
                logger.error(self.last_error)
                return False
                
        except requests.RequestException as e:
            self.last_error = f"Network error: {str(e)}"
            logger.error(self.last_error)
            return False
        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            logger.error(self.last_error)
            return False

def create_streamlit_ui():
    """Create Streamlit UI with proper state management"""
    st.set_page_config(
        page_title="LBridge Login",
        page_icon="🔒",
        layout="wide"
    )

    # Initialize session state
    if 'lbridge_session' not in st.session_state:
        st.session_state.lbridge_session = LBridgeSession()
    if 'login_status' not in st.session_state:
        st.session_state.login_status = False
    if 'debug_log' not in st.session_state:
        st.session_state.debug_log = []

    # Main UI
    st.title("LBridge Login System")
    
    # Debug sidebar
    with st.sidebar:
        st.title("Debug Options")
        show_debug = st.checkbox("Show Debug Information")
        if show_debug:
            st.text_area("Latest Debug Log", 
                        value="\n".join(st.session_state.debug_log),
                        height=400)
    
    # Login form
    if not st.session_state.login_status:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted and username and password:
                with st.spinner("Attempting login..."):
                    # Clear previous debug logs
                    st.session_state.debug_log = []
                    
                    # Attempt login
                    success = st.session_state.lbridge_session.login(username, password)
                    
                    if success:
                        st.session_state.login_status = True
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Login failed: {st.session_state.lbridge_session.last_error}")
                        
                    # Update debug log
                    if show_debug:
                        for handler in logger.handlers:
                            if hasattr(handler, 'stream'):
                                st.session_state.debug_log = handler.stream.getvalue().split('\n')
    else:
        st.success("Currently logged in!")
        if st.button("Logout"):
            st.session_state.login_status = False
            st.session_state.lbridge_session = LBridgeSession()
            st.rerun()

if __name__ == "__main__":
    create_streamlit_ui()
