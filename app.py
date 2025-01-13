import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json
import os

# Configuration and Settings
class Config:
    LOGIN_URL = "https://lbridge.com/Login.aspx"
    ASSIGNMENTS_URL = "https://lbridge.com/Interpreters/open_assignments"
    DATA_FILE = "assignments_history.json"
    
    @staticmethod
    def load_credentials():
        return st.secrets["lbridge_credentials"] if "lbridge_credentials" in st.secrets else None

class LBridgeSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

    def login(self, username, password):
        try:
            # Get initial page for form tokens
            response = self.session.get(Config.LOGIN_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract ASP.NET form fields
            form_data = {
                '__VIEWSTATE': soup.find('input', {'name': '__VIEWSTATE'})['value'],
                '__VIEWSTATEGENERATOR': soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value'],
                '__EVENTVALIDATION': soup.find('input', {'name': '__EVENTVALIDATION'})['value'],
                'ctl00$MainContent$txtUserName': username,
                'ctl00$MainContent$txtPassword': password,
                'ctl00$MainContent$cmdSubmit': 'Submit'
            }
            
            # Submit login
            response = self.session.post(Config.LOGIN_URL, data=form_data)
            
            # Check if login was successful
            return 'Logout.aspx' in response.text
            
        except Exception as e:
            st.error(f"Login error: {str(e)}")
            return False

    def get_assignments(self):
        try:
            response = self.session.get(Config.ASSIGNMENTS_URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            assignments = []
            table = soup.find('table', {'class': 'grid_table'})
            
            if table:
                rows = table.find_all('tr', {'class': 'mouseover'})
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 6:
                        assignment = {
                            'customer': cells[0].text.strip(),
                            'datetime': cells[1].text.strip(),
                            'language': cells[2].text.strip(),
                            'service_type': cells[3].text.strip(),
                            'details': cells[4].text.strip(),
                            'comments': cells[5].text.strip(),
                            'timestamp': datetime.now().isoformat()
                        }
                        assignments.append(assignment)
            
            return assignments
            
        except Exception as e:
            st.error(f"Error fetching assignments: {str(e)}")
            return []

class AssignmentStore:
    def __init__(self):
        self.filename = Config.DATA_FILE
        self.assignments = self.load_assignments()

    def load_assignments(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
            return []
        except Exception:
            return []

    def save_assignments(self, assignments):
        try:
            with open(self.filename, 'w') as f:
                json.dump(assignments, f)
        except Exception as e:
            st.error(f"Error saving assignments: {str(e)}")

    def update_assignments(self, new_assignments):
        # Update with new assignments, avoiding duplicates
        existing_ids = {self.get_assignment_id(a) for a in self.assignments}
        
        for assignment in new_assignments:
            assignment_id = self.get_assignment_id(assignment)
            if assignment_id not in existing_ids:
                self.assignments.append(assignment)
                existing_ids.add(assignment_id)
        
        self.save_assignments(self.assignments)

    @staticmethod
    def get_assignment_id(assignment):
        # Create a unique identifier for an assignment
        return f"{assignment['customer']}_{assignment['datetime']}_{assignment['language']}"

def create_streamlit_ui():
    st.set_page_config(page_title="LBridge Assignments Monitor", layout="wide")
    
    st.title("LBridge Assignments Monitor")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Login section
        st.subheader("Login")
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
            
        if not st.session_state.logged_in:
            credentials = Config.load_credentials()
            if credentials:
                username = credentials["username"]
                password = credentials["password"]
            else:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                session = LBridgeSession()
                if session.login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.lbridge_session = session
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Login failed!")
        else:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.experimental_rerun()
        
        # Refresh control
        if st.session_state.get('logged_in', False):
            st.subheader("Update")
            auto_refresh = st.checkbox("Auto refresh")
            refresh_interval = st.slider("Refresh interval (minutes)", 1, 60, 15)
            
            if st.button("Refresh Now"):
                st.experimental_rerun()
            
            if auto_refresh:
                time.sleep(refresh_interval * 60)
                st.experimental_rerun()

    # Main content area
    if st.session_state.get('logged_in', False):
        # Fetch and display assignments
        assignments = st.session_state.lbridge_session.get_assignments()
        
        # Update stored assignments
        store = AssignmentStore()
        store.update_assignments(assignments)
        
        # Display current assignments
        st.header("Current Available Assignments")
        if assignments:
            df = pd.DataFrame(assignments)
            st.dataframe(df)
        else:
            st.info("No assignments currently available")
        
        # Display historical data
        st.header("Assignment History")
        if store.assignments:
            hist_df = pd.DataFrame(store.assignments)
            hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])
            hist_df = hist_df.sort_values('timestamp', ascending=False)
            st.dataframe(hist_df)
            
            # Analytics
            st.header("Analytics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Assignments by Language")
                language_counts = hist_df['language'].value_counts()
                st.bar_chart(language_counts)
            
            with col2:
                st.subheader("Assignments by Customer")
                customer_counts = hist_df['customer'].value_counts().head(10)
                st.bar_chart(customer_counts)

if __name__ == "__main__":
    create_streamlit_ui()
