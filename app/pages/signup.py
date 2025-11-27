#%% Imports

import streamlit as st
import sys
sys.path.append('..')
from utils import get_password_auth, get_supabase_client

#%% Page Configuration

st.set_page_config(page_title="Sign Up - BandBox", page_icon="⚾", layout="centered")

#%% Main Content

st.title("⚾ Create Your Account")
st.markdown("Join BandBox to track your baseball performance")

# Initialize services
password_auth = get_password_auth()
supabase = get_supabase_client()

# Get available organizations
organizations = supabase.get_all_organizations()
active_orgs = [org for org in organizations if org.get('is_active', False)]

if not active_orgs:
    st.error("❌ No active organizations available. Please contact an administrator.")
    st.stop()

st.markdown("---")

#%% Signup Form

with st.form("signup_form"):
    st.subheader("Account Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name *", placeholder="John Doe")
        email = st.text_input("Email Address *", placeholder="your.email@example.com")
    
    with col2:
        password = st.text_input("Password *", type="password", placeholder="Min. 8 characters")
        confirm_password = st.text_input("Confirm Password *", type="password")
    
    st.divider()
    
    st.subheader("Organization")
    
    # Organization selection
    org_dict = {org['name']: org['id'] for org in active_orgs}
    selected_org_name = st.selectbox(
        "Select Your Team/Organization *",
        options=list(org_dict.keys()),
        help="Choose the organization you belong to"
    )
    
    st.divider()
    
    # Password requirements
    with st.expander("📋 Password Requirements"):
        st.markdown("""
        Your password must:
        - Be at least 8 characters long
        - Contain at least one uppercase letter (A-Z)
        - Contain at least one lowercase letter (a-z)
        - Contain at least one number (0-9)
        """)
    
    # Terms checkbox
    agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
    
    # Submit button
    submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
    
    if submitted:
        # Validation
        errors = []
        
        if not full_name or not email or not password or not confirm_password:
            errors.append("❌ All fields are required")
        
        if password != confirm_password:
            errors.append("❌ Passwords do not match")
        
        # Validate password strength
        is_valid, password_error = password_auth.validate_password_strength(password)
        if not is_valid:
            errors.append(f"❌ {password_error}")
        
        # Check email format
        if email and '@' not in email:
            errors.append("❌ Invalid email format")
        
        if not agree_terms:
            errors.append("❌ You must agree to the Terms of Service")
        
        # Display errors or create account
        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner("Creating your account..."):
                # Check if user already exists
                existing_user = supabase.get_user_by_email(email)
                
                if existing_user:
                    st.error("❌ An account with this email already exists. Please login instead.")
                else:
                    # Create the user
                    org_id = org_dict[selected_org_name]
                    
                    new_user = password_auth.create_user_with_password(
                        email=email,
                        password=password,
                        full_name=full_name,
                        organization_id=org_id,
                        role='player'  # Default role for new signups
                    )
                    
                    if new_user:
                        st.success("✅ Account created successfully!")
                        st.balloons()
                        st.info("🎉 You can now log in with your email and password")
                        
                        # Add a link to login
                        st.markdown("---")
                        if st.button("Go to Login", use_container_width=True):
                            st.switch_page("pages/login.py")
                    else:
                        st.error("❌ Failed to create account. Please try again or contact support.")

#%% Footer

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("Already have an account?")
    if st.button("Login Here", use_container_width=True):
        st.switch_page("pages/login.py")

with col2:
    st.markdown("Or sign in with:")
    if st.button("🔐 Google Account", use_container_width=True):
        # This will redirect to Google OAuth
        st.login()

st.markdown("---")
st.caption("🔒 Your information is secure and encrypted")

