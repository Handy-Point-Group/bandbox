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

# Get available organizations (for joining existing ones)
organizations = supabase.get_all_organizations()
active_orgs = [org for org in organizations if org.get('is_active', False)]

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
    
    # Organization selection or creation
    org_option = st.radio(
        "How would you like to join?",
        options=["Join existing organization", "Create new organization"],
        help="Choose whether to join an existing team or create your own"
    )
    
    if org_option == "Join existing organization":
        if not active_orgs:
            st.warning("⚠️ No organizations available. Please create a new one.")
            org_option = "Create new organization"  # Force creation
        else:
            org_dict = {org['name']: org['id'] for org in active_orgs}
            selected_org_name = st.selectbox(
                "Select Your Team/Organization *",
                options=list(org_dict.keys()),
                help="Choose the organization you belong to"
            )
    
    if org_option == "Create new organization":
        new_org_name = st.text_input(
            "Organization Name *",
            placeholder="e.g., Tigers Baseball Team",
            help="Enter the name for your new team/organization"
        )
        new_org_location = st.text_input(
            "Location (optional)",
            placeholder="e.g., New York, NY",
            help="Where is your organization based?"
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
        
        # Validate organization selection/creation
        if org_option == "Join existing organization" and 'selected_org_name' not in locals():
            errors.append("❌ Please select an organization")
        elif org_option == "Create new organization" and (not new_org_name or not new_org_name.strip()):
            errors.append("❌ Organization name is required")
        
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
                    # Determine organization ID
                    if org_option == "Create new organization":
                        # Create new organization
                        new_org_data = {
                            'name': new_org_name.strip(),
                            'location': new_org_location.strip() if new_org_location else None,
                            'is_active': True
                        }
                        
                        try:
                            result = supabase.client.table('organizations').insert(new_org_data).execute()
                            org_id = result.data[0]['id']
                            st.info(f"✨ Created new organization: {new_org_name}")
                        except Exception as e:
                            st.error(f"❌ Failed to create organization: {e}")
                            st.stop()
                    else:
                        # Use selected organization
                        org_id = org_dict[selected_org_name]
                    
                    # Create the user
                    new_user = password_auth.create_user_with_password(
                        email=email,
                        password=password,
                        full_name=full_name,
                        organization_id=org_id,
                        role='team_admin' if org_option == "Create new organization" else 'player'  # Make creator an admin
                    )
                    
                    if new_user:
                        st.success("✅ Account created successfully!")
                        st.balloons()
                        if org_option == "Create new organization":
                            st.success(f"🎉 You are now the admin of {new_org_name}!")
                        st.info("🎉 You can now log in with your email and password")
                        
                        # Add a link to login
                        st.markdown("---")
                        if st.button("Go to Login", use_container_width=True):
                            st.switch_page("pages/login.py")
                    else:
                        st.error("❌ Failed to create account. Please try again or contact support.")

#%% Footer

st.markdown("---")

st.markdown("Already have an account?")
if st.button("Login Here", use_container_width=True):
    st.switch_page("pages/login.py")

st.markdown("---")
st.caption("🔒 Your information is secure and encrypted")

