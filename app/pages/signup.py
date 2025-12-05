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
    
    # Check if user is pre-authorized
    if email:  # Only check if email is entered
        authorized_record = supabase.check_user_authorized_any_org(email)
        
        if authorized_record:
            # User is pre-authorized - show their organization
            auth_org = supabase.get_organization(authorized_record['organization_id'])
            
            st.success(f"✅ You are pre-authorized to join **{auth_org['name']}**")
            st.info(f"📋 Your assigned role will be: **{authorized_record['assigned_role']}**")
            
            if authorized_record.get('authorization_note'):
                st.info(f"📝 Note: {authorized_record['authorization_note']}")
            
            # Store for later use
            org_dict = {auth_org['name']: auth_org['id']}
            selected_org_name = auth_org['name']
            pre_authorized = True
            assigned_role = authorized_record['assigned_role']
            auth_record_id = authorized_record['id']
        else:
            # User not pre-authorized - allow selection from available orgs
            pre_authorized = False
            assigned_role = 'player'
            auth_record_id = None
            
            if not active_orgs:
                st.error("⚠️ No organizations available.")
                st.info("Please contact a system administrator to authorize you for an organization.")
                st.stop()
            else:
                org_dict = {org['name']: org['id'] for org in active_orgs}
                selected_org_name = st.selectbox(
                    "Select Your Team/Organization *",
                    options=list(org_dict.keys()),
                    help="Choose the organization you belong to"
                )
                
                st.info("💡 **Pre-authorized users:** Enter your email above to see your assigned organization.")
    else:
        # Email not entered yet
        pre_authorized = False
        assigned_role = 'player'
        auth_record_id = None
        
        if not active_orgs:
            st.error("⚠️ No organizations available.")
            st.info("Please contact a system administrator to authorize you for an organization.")
            st.stop()
        else:
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
        
        # Validate organization selection
        if 'selected_org_name' not in locals():
            errors.append("❌ Please select an organization")
        
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
                    # Use selected organization
                    org_id = org_dict[selected_org_name]
                    
                    # Create the user with assigned role (either from authorization or default 'player')
                    new_user = password_auth.create_user_with_password(
                        email=email,
                        password=password,
                        full_name=full_name,
                        organization_id=org_id,
                        role=assigned_role
                    )
                    
                    if new_user:
                        # If user was pre-authorized, mark them as signed up
                        if pre_authorized and auth_record_id:
                            supabase.mark_authorized_user_signed_up(email, org_id, new_user['id'])
                        
                        st.success("✅ Account created successfully!")
                        
                        if assigned_role != 'player':
                            st.success(f"🎉 You have been assigned the '{assigned_role}' role!")
                        
                        st.balloons()
                        st.info("🎉 Redirecting to login page...")
                        
                        # Auto-redirect to login page
                        import time
                        time.sleep(2)  # Give user time to see the success message
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

