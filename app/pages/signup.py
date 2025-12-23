#%% Imports

import streamlit as st
import sys
from datetime import date
import time
sys.path.append('..')
from utils import get_password_auth, get_supabase_client, get_auth_manager

#%% Page Configuration

st.set_page_config(page_title="Sign Up - BandBox", page_icon="⚾", layout="centered")

#%% Main Content

st.title("⚾ Create Your Account")
st.markdown("Join BandBox to track your baseball performance")

# Initialize services
password_auth = get_password_auth()
supabase = get_supabase_client()

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
    
    #%% Account Type Selection
    st.subheader("Account Type")
    
    account_type = st.selectbox(
        "I am a... *",
        options=["Player", "Coach"],
        index=0,
        help="Select your role. Players can fill out additional profile information."
    )
    
    # Player Bio Form (shown when Player is selected)
    player_data = {}
    coach_data = {}
    
    if account_type == "Player":
        with st.expander("📋 Quick Player Info (Optional)", expanded=True):
            st.caption("Just the basics - you can add more details to your profile later.")
            
            p_col1, p_col2 = st.columns(2)
            
            with p_col1:
                player_data['primary_position'] = st.selectbox(
                    "Primary Position",
                    options=[None, "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "P", "DH", "UT"],
                    index=0
                )
                player_data['graduation_year'] = st.number_input(
                    "Graduation Year",
                    min_value=2020,
                    max_value=2035,
                    value=None,
                    placeholder="2026"
                )
            
            with p_col2:
                player_data['batting_hand'] = st.selectbox("Batting Hand", options=[None, "Right", "Left", "Switch"], index=0)
                player_data['throwing_hand'] = st.selectbox("Throwing Hand", options=[None, "Right", "Left"], index=0)
    
    # Coach Bio Form (shown when Coach is selected)
    elif account_type == "Coach":
        with st.expander("🧢 Quick Coach Info (Optional)", expanded=True):
            st.caption("Just the basics - you can add more details to your profile later.")
            
            c_col1, c_col2 = st.columns(2)
            
            with c_col1:
                coach_data['phone'] = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
                coach_data['role_type'] = st.selectbox(
                    "Coaching Role",
                    options=[None, "Head Coach", "Assistant Coach", "Pitching Coach", "Hitting Coach", 
                             "Catching Coach", "Infield Coach", "Outfield Coach", "Strength Coach", "Volunteer", "Other"],
                    index=0
                )
            
            with c_col2:
                coach_data['title'] = st.text_input(
                    "Title",
                    placeholder="e.g., Head Coach, Assistant Coach"
                )
                coach_data['preferred_contact_method'] = st.selectbox(
                    "Preferred Contact Method",
                    options=[None, "Email", "Phone", "Text", "Any"],
                    index=0
                )
    
    st.divider()
    
    st.subheader("Organization (Optional)")
    
    # Initialize variables
    pre_authorized = False
    assigned_role = 'player'  # Default role for non-authorized signups
    auth_record_id = None
    org_dict = {}
    selected_org_id = None
    
    # Check if user is pre-authorized (only if email is entered)
    if email:
        authorized_record = supabase.check_user_authorized_any_org(email)
        
        if authorized_record:
            # User is pre-authorized - automatically assign their organization
            auth_org = supabase.get_organization(authorized_record['organization_id'])
            
            st.success(f"✅ You are pre-authorized to join **{auth_org['name']}**")
            st.info(f"📋 Your assigned role will be: **{authorized_record['assigned_role']}**")
            
            if authorized_record.get('authorization_note'):
                st.info(f"📝 Note: {authorized_record['authorization_note']}")
            
            # Store for later use
            selected_org_id = auth_org['id']
            pre_authorized = True
            assigned_role = authorized_record['assigned_role']
            auth_record_id = authorized_record['id']
        else:
            # User NOT pre-authorized - allow signup without organization
            st.info("""
            💡 **No pre-authorization found**
            
            You can create an account now and join an organization later when invited by an administrator.
            """)
            selected_org_id = None
    else:
        # Email not entered yet
        st.info("👆 Enter your email address above. If you're pre-authorized, your organization will be automatically assigned.")
    
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
                    # Determine role based on account type (if not pre-authorized)
                    if not pre_authorized:
                        assigned_role = 'player' if account_type == "Player" else 'coach'
                    
                    # Create the user (with or without organization)
                    new_user = password_auth.create_user_with_password(
                        email=email,
                        password=password,
                        full_name=full_name,
                        organization_id=selected_org_id,  # Can be None
                        role=assigned_role
                    )
                    
                    if new_user:
                        # If user was pre-authorized, mark them as signed up
                        if pre_authorized and auth_record_id and selected_org_id:
                            supabase.mark_authorized_user_signed_up(email, selected_org_id, new_user['id'])
                        
                        profile_created = True  # Track if profile was created
                        
                        # Parse name into first/last (used by both player and coach)
                        name_parts = full_name.strip().split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(name_parts) > 1 else ''
                        
                        # If Player account type, create player2 profile
                        if account_type == "Player":
                            # Convert batting/throwing hand to single letter
                            batting_hand_map = {"Right": "R", "Left": "L", "Switch": "S"}
                            throwing_hand_map = {"Right": "R", "Left": "L"}
                            
                            # Build player profile data (minimal fields)
                            player_profile = {
                                'user_id': new_user['id'],
                                'organization_id': selected_org_id,
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                            }
                            
                            # Add optional fields if provided
                            if player_data.get('primary_position'):
                                player_profile['primary_position'] = player_data['primary_position']
                            if player_data.get('graduation_year'):
                                player_profile['graduation_year'] = player_data['graduation_year']
                            if player_data.get('batting_hand'):
                                player_profile['batting_hand'] = batting_hand_map.get(player_data['batting_hand'])
                            if player_data.get('throwing_hand'):
                                player_profile['throwing_hand'] = throwing_hand_map.get(player_data['throwing_hand'])
                            
                            # Insert player profile into players2 table
                            try:
                                result = supabase.client.table('players2').insert(player_profile).execute()
                                if result.data:
                                    profile_created = True
                                else:
                                    profile_created = False
                                    st.warning("⚠️ Player profile could not be saved. You can update it later.")
                            except Exception as e:
                                profile_created = False
                                st.warning(f"⚠️ Account created but player profile could not be saved: {str(e)}")
                        
                        # If Coach account type, create coaches profile
                        elif account_type == "Coach":
                            # Map role type to database enum
                            role_type_map = {
                                "Head Coach": "head_coach",
                                "Assistant Coach": "assistant_coach",
                                "Pitching Coach": "pitching_coach",
                                "Hitting Coach": "hitting_coach",
                                "Catching Coach": "catching_coach",
                                "Infield Coach": "infield_coach",
                                "Outfield Coach": "outfield_coach",
                                "Strength Coach": "strength_coach",
                                "Volunteer": "volunteer",
                                "Other": "other"
                            }
                            
                            # Map contact method
                            contact_method_map = {
                                "Email": "email",
                                "Phone": "phone",
                                "Text": "text",
                                "Any": "any"
                            }
                            
                            # Build coach profile data (minimal fields)
                            coach_profile = {
                                'user_id': new_user['id'],
                                'organization_id': selected_org_id,
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                            }
                            
                            # Add optional fields if provided
                            if coach_data.get('phone'):
                                coach_profile['phone'] = coach_data['phone']
                            if coach_data.get('role_type'):
                                coach_profile['role_type'] = role_type_map.get(coach_data['role_type'])
                            if coach_data.get('title'):
                                coach_profile['title'] = coach_data['title']
                            if coach_data.get('preferred_contact_method'):
                                coach_profile['preferred_contact_method'] = contact_method_map.get(coach_data['preferred_contact_method'])
                            
                            # Insert coach profile into coaches table
                            try:
                                result = supabase.client.table('coaches').insert(coach_profile).execute()
                                if result.data:
                                    profile_created = True
                                else:
                                    profile_created = False
                                    st.warning("⚠️ Coach profile could not be saved. You can update it later.")
                            except Exception as e:
                                profile_created = False
                                st.warning(f"⚠️ Account created but coach profile could not be saved: {str(e)}")
                        
                        st.success("✅ Account created successfully!")
                        
                        if pre_authorized:
                            if assigned_role != 'player':
                                st.success(f"🎉 You have been assigned the '{assigned_role}' role!")
                            st.info(f"🏢 You have been added to the organization.")
                        
                        st.balloons()
                        
                        # Automatically log the user in
                        auth = get_auth_manager()
                        login_success = auth.login_with_password(email, password)
                        
                        if login_success:
                            st.success("🎉 You're now logged in! Redirecting to dashboard...")
                            time.sleep(1)
                            st.switch_page("baseball-team-app.py")
                        else:
                            # Fallback - redirect to login page
                            st.info("💡 Please log in with your new credentials.")
                            time.sleep(2)
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

