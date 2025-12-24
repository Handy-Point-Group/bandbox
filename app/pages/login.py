#%% Imports

import streamlit as st
import sys
sys.path.append('..')
from utils import get_auth_manager

#%% Page Configuration

st.set_page_config(page_title="Login - Bandbox", page_icon=r"app/images/bandbox.png", layout="centered")

# Custom CSS for button styling
st.markdown("""
<style>
    /* Make primary button text black instead of white */
    .stButton > button[kind="primary"] {
        color: black !important;
    }
    /* Make yellow button text black */
    button[data-testid="baseButton-primary"] {
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

#%% Check if already logged in

auth = get_auth_manager()

if auth.check_authentication():
    st.success("You're already logged in!")
    st.info("Redirecting to main app...")
    if st.button("Go to Dashboard", type="primary"):
        st.switch_page("baseball-team-app.py")
    st.stop()

#%% Main Content

# Logo and title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("Bandbox Login")
    st.markdown("**Own Your Baseball Future**")

st.markdown("---")

#%% Email/Password Login

st.subheader("Login with Email")

with st.form("email_login_form"):
    email = st.text_input("Email Address", placeholder="your.email@example.com")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    remember_me = st.checkbox("Remember me")
    
    col1, col2 = st.columns(2)
    
    with col1:
        login_button = st.form_submit_button("Login", use_container_width=True, type="primary")
    
    with col2:
        if st.form_submit_button("Forgot Password?", use_container_width=True):
            st.info("Password reset feature coming soon! Please contact your administrator.")
    
    if login_button:
        if not email or not password:
            st.error("Please enter both email and password")
        else:
            with st.spinner("Authenticating..."):
                success = auth.login_with_password(email, password)
                
                if success:
                    st.success("Login successful!")
                    st.info("Redirecting to dashboard...")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")
                    st.warning("""
                    **Possible reasons:**
                    - Incorrect email or password
                    - Account is not active
                    - Organization is inactive (if you're assigned to one)
                    
                    Note: You can login even without being assigned to an organization.
                    Contact your team administrator if you need help.
                    """)

st.markdown("---")

#%% Sign Up Section

st.markdown("### Don't have an account?")

col1, col2 = st.columns(2)

with col1:
    if st.button("Create New Account", use_container_width=True):
        st.switch_page("pages/signup.py")

with col2:
    st.markdown("**or**")
    st.markdown("Contact your team administrator to get added")

#%% Footer

st.markdown("---")

with st.expander("Need Help?"):
    st.markdown("""
    **Login Issues?**
    
    1. **Forgot your password?**
       - Contact your team administrator to reset it
    
    2. **Account not found?**
       - Make sure you're registered in the system
       - You can create a new account by clicking "Create New Account" above
    
    3. **Don't have an organization?**
       - No problem! You can login and use your account without being assigned to an organization
       - You'll be able to join an organization later when invited by an administrator
    
    4. **Organization inactive?**
       - If you're assigned to an organization and it's inactive, contact your organization administrator
    
    **For technical support, contact:** support@bandbox.com
    """)

st.caption("Secure authentication powered by Bandbox")

