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
    if account_type == "Player":
        with st.expander("📋 Player Profile (Optional)", expanded=True):
            st.caption("Fill out as much or as little as you'd like. You can always update this later.")
            
            # Basic Baseball Info
            st.markdown("**Baseball Info**")
            p_col1, p_col2, p_col3 = st.columns(3)
            
            with p_col1:
                player_data['jersey_number'] = st.number_input("Jersey #", min_value=0, max_value=99, value=None, placeholder="00")
                player_data['batting_hand'] = st.selectbox("Batting Hand", options=[None, "Right", "Left", "Switch"], index=0)
            
            with p_col2:
                player_data['primary_position'] = st.selectbox(
                    "Primary Position",
                    options=[None, "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "P", "DH", "UT"],
                    index=0
                )
                player_data['throwing_hand'] = st.selectbox("Throwing Hand", options=[None, "Right", "Left"], index=0)
            
            with p_col3:
                player_data['secondary_position'] = st.selectbox(
                    "Secondary Position",
                    options=[None, "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "P", "DH", "UT"],
                    index=0
                )
                player_data['is_pitcher'] = st.checkbox("I am a pitcher")
            
            st.markdown("---")
            
            # Physical Info
            st.markdown("**Physical Info**")
            ph_col1, ph_col2 = st.columns(2)
            
            with ph_col1:
                height_feet = st.number_input("Height (feet)", min_value=4, max_value=7, value=None, placeholder="5")
                player_data['weight_lbs'] = st.number_input("Weight (lbs)", min_value=80, max_value=400, value=None, placeholder="180")
            
            with ph_col2:
                height_inches = st.number_input("Height (inches)", min_value=0, max_value=11, value=None, placeholder="10")
                player_data['birthdate'] = st.date_input("Birthdate", value=None)
            
            # Calculate total height in inches
            if height_feet is not None and height_inches is not None:
                player_data['height_inches'] = (height_feet * 12) + height_inches
            else:
                player_data['height_inches'] = None
            
            st.markdown("---")
            
            # Academic Info
            st.markdown("**Academic Info**")
            ac_col1, ac_col2 = st.columns(2)
            
            with ac_col1:
                player_data['graduation_year'] = st.number_input(
                    "Graduation Year",
                    min_value=2020,
                    max_value=2035,
                    value=None,
                    placeholder="2026"
                )
                player_data['high_school'] = st.text_input("High School", placeholder="Lincoln High School")
            
            with ac_col2:
                player_data['class_level'] = st.selectbox(
                    "Class Level",
                    options=[None, "Middle School", "Freshman", "Sophomore", "Junior", "Senior", "Grad", "Other"],
                    index=0
                )
                player_data['college'] = st.text_input("College (if applicable)", placeholder="State University")
            
            st.markdown("---")
            
            # Location Info
            st.markdown("**Location**")
            loc_col1, loc_col2 = st.columns(2)
            
            with loc_col1:
                player_data['hometown'] = st.text_input("Hometown", placeholder="Boston")
            
            with loc_col2:
                player_data['state'] = st.text_input("State", placeholder="MA")
            
            st.markdown("---")
            
            # Social & Bio
            st.markdown("**Bio & Social**")
            player_data['bio'] = st.text_area(
                "About Me",
                placeholder="Tell us about yourself, your baseball journey, goals, etc...",
                height=100
            )
            
            soc_col1, soc_col2 = st.columns(2)
            with soc_col1:
                player_data['instagram_handle'] = st.text_input("Instagram Handle", placeholder="@username")
            with soc_col2:
                player_data['twitter_handle'] = st.text_input("Twitter/X Handle", placeholder="@username")
    
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
                        
                        player_profile_created = True  # Track if player profile was created
                        
                        # If Player account type, create player2 profile
                        if account_type == "Player":
                            # Parse name into first/last
                            name_parts = full_name.strip().split(' ', 1)
                            first_name = name_parts[0]
                            last_name = name_parts[1] if len(name_parts) > 1 else ''
                            
                            # Convert batting/throwing hand to single letter
                            batting_hand_map = {"Right": "R", "Left": "L", "Switch": "S"}
                            throwing_hand_map = {"Right": "R", "Left": "L"}
                            
                            # Build player profile data
                            player_profile = {
                                'user_id': new_user['id'],
                                'organization_id': selected_org_id,
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                            }
                            
                            # Add optional fields if provided
                            if player_data.get('jersey_number'):
                                player_profile['jersey_number'] = player_data['jersey_number']
                            if player_data.get('primary_position'):
                                player_profile['primary_position'] = player_data['primary_position']
                            if player_data.get('secondary_position'):
                                player_profile['secondary_position'] = player_data['secondary_position']
                            if player_data.get('is_pitcher'):
                                player_profile['is_pitcher'] = player_data['is_pitcher']
                            if player_data.get('batting_hand'):
                                player_profile['batting_hand'] = batting_hand_map.get(player_data['batting_hand'])
                            if player_data.get('throwing_hand'):
                                player_profile['throwing_hand'] = throwing_hand_map.get(player_data['throwing_hand'])
                            if player_data.get('height_inches'):
                                player_profile['height_inches'] = player_data['height_inches']
                            if player_data.get('weight_lbs'):
                                player_profile['weight_lbs'] = player_data['weight_lbs']
                            if player_data.get('birthdate'):
                                player_profile['birthdate'] = player_data['birthdate'].isoformat()
                            if player_data.get('graduation_year'):
                                player_profile['graduation_year'] = player_data['graduation_year']
                            if player_data.get('class_level'):
                                player_profile['class_level'] = player_data['class_level']
                            if player_data.get('high_school'):
                                player_profile['high_school'] = player_data['high_school']
                            if player_data.get('college'):
                                player_profile['college'] = player_data['college']
                            if player_data.get('hometown'):
                                player_profile['hometown'] = player_data['hometown']
                            if player_data.get('state'):
                                player_profile['state'] = player_data['state']
                            if player_data.get('bio'):
                                player_profile['bio'] = player_data['bio']
                            if player_data.get('instagram_handle'):
                                player_profile['instagram_handle'] = player_data['instagram_handle']
                            if player_data.get('twitter_handle'):
                                player_profile['twitter_handle'] = player_data['twitter_handle']
                            
                            # Insert player profile into players2 table
                            try:
                                result = supabase.client.table('players2').insert(player_profile).execute()
                                if result.data:
                                    player_profile_created = True
                                else:
                                    player_profile_created = False
                                    st.warning("⚠️ Player profile could not be saved. You can update it later.")
                            except Exception as e:
                                player_profile_created = False
                                st.warning(f"⚠️ Account created but player profile could not be saved: {str(e)}")
                        
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

