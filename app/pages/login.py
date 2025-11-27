#%% Imports

import streamlit as st
import sys
sys.path.append('..')
from utils import get_auth_manager

#%% Page Configuration

st.set_page_config(page_title="Login - BandBox", page_icon="⚾", layout="centered")

#%% Check if already logged in

auth = get_auth_manager()

if auth.check_authentication():
    st.success("✅ You're already logged in!")
    st.info("Redirecting to main app...")
    if st.button("Go to Dashboard"):
        st.switch_page("baseball-team-app.py")
    st.stop()

#%% Main Content

# Logo and title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("⚾ BandBox Login")
    st.markdown("**Track Your Baseball Performance**")

st.markdown("---")

#%% Login Options

# Create tabs for different login methods
tab1, tab2 = st.tabs(["📧 Email/Password", "🔐 Google Login"])

#%% Tab 1: Email/Password Login

with tab1:
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
                st.error("❌ Please enter both email and password")
            else:
                with st.spinner("Authenticating..."):
                    success = auth.login_with_password(email, password)
                    
                    if success:
                        st.success("✅ Login successful!")
                        st.balloons()
                        st.info("Redirecting to dashboard...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password. Please try again.")
                        st.warning("""
                        **Possible reasons:**
                        - Incorrect email or password
                        - Account is not active
                        - No password set (try logging in with Google)
                        - Organization is inactive
                        
                        Contact your team administrator if you need help.
                        """)

#%% Tab 2: Google Login

with tab2:
    st.subheader("Login with Google")
    
    st.markdown("""
    Sign in with your Google account for quick and secure access.
    
    **Benefits:**
    - ✅ No password to remember
    - ✅ Secure OAuth 2.0 authentication
    - ✅ Single sign-on across devices
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Sign in with Google", use_container_width=True, type="primary"):
            # Check if Google OAuth is configured
            try:
                st.login()  # This will redirect to Google OAuth
            except Exception as e:
                st.error(f"❌ Google login not configured properly. Error: {e}")
                st.info("Please contact your administrator to set up Google authentication.")

#%% Divider

st.markdown("---")

#%% Sign Up Section

st.markdown("### Don't have an account?")

col1, col2 = st.columns(2)

with col1:
    if st.button("📝 Create New Account", use_container_width=True):
        st.switch_page("pages/signup.py")

with col2:
    st.markdown("**or**")
    st.markdown("Contact your team administrator to get added")

#%% Footer

st.markdown("---")

with st.expander("ℹ️ Need Help?"):
    st.markdown("""
    **Login Issues?**
    
    1. **Forgot your password?**
       - Contact your team administrator to reset it
       - Or try logging in with Google if your account is linked
    
    2. **Account not found?**
       - Make sure you're registered in the system
       - Contact your team administrator to create an account
    
    3. **Google login not working?**
       - Make sure you're using the correct Google account
       - Your Google email must match your registered email
       - Contact administrator if you need to link your Google account
    
    4. **Organization inactive?**
       - Contact your organization administrator
    
    **For technical support, contact:** support@bandbox.com
    """)

st.caption("🔒 Secure authentication powered by BandBox")

