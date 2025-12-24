#%% Imports

import streamlit as st
import sys
from datetime import date
import time
sys.path.append('..')
from utils import get_password_auth, get_supabase_client, get_auth_manager

#%% Page Configuration

st.set_page_config(page_title="Sign Up - Bandbox", page_icon=r"app/images/bandbox.png", layout="centered")

# Custom CSS for button styling
st.markdown("""
<style>
    /* Make primary button text black instead of white */
    .stButton > button[kind="primary"] {
        color: black !important;
    }
    button[data-testid="baseButton-primary"] {
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

#%% Main Content

st.title("Create Your Account")
st.markdown("Join Bandbox to own your baseball future")

# Initialize services
password_auth = get_password_auth()
supabase = get_supabase_client()

st.markdown("---")

#%% Step 1: Email Check (outside form for real-time authorization check)

st.subheader("Step 1: Enter Your Email")
st.caption("We'll check if you've been pre-authorized by an organization.")

email = st.text_input("Email Address *", placeholder="your.email@example.com", key="signup_email")

# Initialize authorization state
pre_authorized = False
assigned_role = 'player'
auth_record_id = None
selected_org_id = None
auth_org = None
authorized_record = None

# Check for pre-authorization
if email and '@' in email:
    authorized_record = supabase.check_user_authorized_any_org(email)
    
    if authorized_record:
        auth_org = supabase.get_organization(authorized_record['organization_id'])
        
        st.success(f"✅ **Welcome!** You are pre-authorized to join **{auth_org.get('name', 'Unknown Organization')}**")
        
        # Show role info
        role_display = {
            'admin-org': '🏢 Organization Administrator',
            'admin': '👤 Team Admin',
            'coach': '🧢 Coach',
            'player': '⚾ Player'
        }.get(authorized_record['assigned_role'], authorized_record['assigned_role'])
        
        st.info(f"📋 Your assigned role: **{role_display}**")
        
        if authorized_record.get('authorization_note'):
            st.caption(f"📝 Note: {authorized_record['authorization_note']}")
        
        pre_authorized = True
        assigned_role = authorized_record['assigned_role']
        auth_record_id = authorized_record['id']
        selected_org_id = auth_org['id']
    else:
        st.info("💡 No pre-authorization found. You can create an account and join an organization later when invited.")

st.markdown("---")

#%% Signup Form

with st.form("signup_form"):
    st.subheader("Step 2: Account Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name *", placeholder="John Doe")
    
    with col2:
        password = st.text_input("Password *", type="password", placeholder="Min. 8 characters")
        confirm_password = st.text_input("Confirm Password *", type="password")
    
    # Password requirements
    with st.expander("Password Requirements"):
        st.markdown("""
        Your password must:
        - Be at least 8 characters long
        - Contain at least one uppercase letter (A-Z)
        - Contain at least one lowercase letter (a-z)
        - Contain at least one number (0-9)
        """)
    
    st.divider()
    
    #%% Account Type Selection
    st.subheader("Step 3: Account Type")
    
    # Build account type options based on authorization
    if pre_authorized and assigned_role in ['admin-org', 'admin']:
        # Pre-authorized admin - show admin option
        account_type_options = ["Organization Admin"]
        account_type_index = 0
        st.caption("✅ Your account type is set based on your pre-authorization.")
    elif pre_authorized and assigned_role == 'coach':
        # Pre-authorized coach
        account_type_options = ["Coach"]
        account_type_index = 0
        st.caption("✅ Your account type is set based on your pre-authorization.")
    elif pre_authorized and assigned_role == 'player':
        # Pre-authorized player
        account_type_options = ["Player"]
        account_type_index = 0
        st.caption("✅ Your account type is set based on your pre-authorization.")
    else:
        # Not pre-authorized - allow Player or Coach selection
        account_type_options = ["Player", "Coach"]
        account_type_index = 0
    
    account_type = st.selectbox(
        "I am a... *",
        options=account_type_options,
        index=account_type_index,
        help="Select your role.",
        disabled=pre_authorized  # Lock if pre-authorized
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
    
    elif account_type == "Organization Admin":
        st.info("🏢 As an Organization Admin, you'll be able to manage teams, players, and coaches for your organization.")
    
    st.divider()
    
    # Show organization assignment if pre-authorized
    if pre_authorized and auth_org:
        st.subheader("Organization Assignment")
        st.success(f"✅ You will be added to: **{auth_org.get('name', 'Unknown')}**")
    else:
        st.caption("💡 You can be added to an organization later by an administrator.")
    
    st.divider()
    
    st.subheader("Player/Coach Profile (Optional)")
    
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.caption("Complete your profile now to get started faster, or skip and add it later")
    with col_info2:
        st.caption("**Recommended**")
    
    # Initialize player profile variables
    player_role = "Select"
    grad_year = None
    batting_hand = "Select"
    throwing_hand = "Select"
    pitcher = False
    primary_position = "Select Position"
    current_team = ""
    travel_team = ""
    years_playing = 0
    college_interest = "Select"
    goals = ""
    
    with st.expander("Add Player Profile Information", expanded=False):
        st.markdown("**This is optional but recommended for players and coaches**")
        
        # Basic player info
        col1, col2 = st.columns(2)
        
        with col1:
            player_role = st.selectbox(
                "I am a:",
                options=["Select", "Player", "Coach", "Parent/Guardian", "Other"],
                help="This helps us customize your experience",
                key="player_role_select"
            )
        
        # Show player-specific fields if role is Player
        if player_role == "Player":
            # Calculate default graduation year
            from datetime import datetime
            current_year = datetime.now().year
            default_grad_year = current_year + 4
            
            col1, col2 = st.columns(2)
            
            with col1:
                grad_year = st.number_input(
                    "High School Graduation Year",
                    min_value=current_year - 10,
                    max_value=current_year + 10,
                    value=default_grad_year,
                    step=1
                )
                
                batting_hand = st.selectbox(
                    "Batting Hand",
                    options=["Select", "Right", "Left", "Switch"]
                )
                
                pitcher = st.checkbox("I am a Pitcher")
            
            with col2:
                throwing_hand = st.selectbox(
                    "Throwing Hand",
                    options=["Select", "Right", "Left"]
                )
                
                position_options = [
                    "Select Position",
                    "Catcher (C)",
                    "First Base (1B)",
                    "Second Base (2B)",
                    "Third Base (3B)",
                    "Shortstop (SS)",
                    "Left Field (LF)",
                    "Center Field (CF)",
                    "Right Field (RF)",
                    "Designated Hitter (DH)",
                    "Pitcher (P)"
                ]
                
                primary_position = st.selectbox(
                    "Primary Position",
                    options=position_options
                )
            
            st.markdown("**Additional Information**")
            
            col3, col4 = st.columns(2)
            
            with col3:
                current_team = st.text_input(
                    "Current Team/School",
                    placeholder="e.g., Lincoln High School"
                )
                
                years_playing = st.number_input(
                    "Years Playing Baseball",
                    min_value=0,
                    max_value=20,
                    value=0,
                    step=1
                )
            
            with col4:
                travel_team = st.text_input(
                    "Travel/Club Team (if any)",
                    placeholder="e.g., Elite Baseball 16U"
                )
                
                college_interest = st.selectbox(
                    "College Baseball Interest",
                    options=["Select", "Division I", "Division II", "Division III", "NAIA", "JUCO", "Not Interested", "Undecided"]
                )
            
            goals = st.text_area(
                "Your Baseball Goals (optional)",
                placeholder="What are your goals for this season?",
                height=80
            )
    
    st.divider()
    
    # Terms checkbox
    agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
    
    # Submit button
    submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
    
    if submitted:
        # Validation
        errors = []
        
        if not full_name or not email or not password or not confirm_password:
            errors.append("All fields are required")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Validate password strength
        is_valid, password_error = password_auth.validate_password_strength(password)
        if not is_valid:
            errors.append(f"{password_error}")
        
        # Check email format
        if email and '@' not in email:
            errors.append("Invalid email format")
        
        if not agree_terms:
            errors.append("You must agree to the Terms of Service")
        
        # Display errors or create account
        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner("Creating your account..."):
                # Check if user already exists
                existing_user = supabase.get_user_by_email(email)
                
                if existing_user:
                    st.error("An account with this email already exists. Please login instead.")
                else:
                    # Determine role based on account type or pre-authorization
                    if pre_authorized:
                        # Use the role from authorization record
                        final_role = assigned_role
                    elif account_type == "Organization Admin":
                        final_role = 'admin-org'
                    elif account_type == "Coach":
                        final_role = 'coach'
                    else:
                        final_role = 'player'
                    
                    # Create the user (with or without organization)
                    new_user = password_auth.create_user_with_password(
                        email=email,
                        password=password,
                        full_name=full_name,
                        organization_id=selected_org_id,  # Can be None
                        role=final_role
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
                        
                        # Organization Admin - no profile needed, just show success
                        elif account_type == "Organization Admin":
                            profile_created = True
                        
                        st.success("✅ Account created successfully!")
                        
                        # Show role and organization info
                        role_display = {
                            'admin-org': 'Organization Administrator',
                            'admin': 'Team Admin',
                            'coach': 'Coach',
                            'player': 'Player'
                        }.get(final_role, final_role)
                        
                        if final_role != 'player':
                            st.success(f"🎉 You have been assigned the **{role_display}** role!")
                        
                        if pre_authorized and selected_org_id:
                            st.info(f"🏢 You have been added to the organization.")
                        
                        st.balloons()
                        
                        # Automatically log the user in
                        auth = get_auth_manager()
                        login_success = auth.login_with_password(email, password)
                        
                        if login_success:
                            st.success("🎉 You're now logged in! Redirecting to dashboard...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # Fallback - redirect to login page
                            st.info("💡 Please log in with your new credentials.")
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error("Failed to create account. Please try again or contact support.")

#%% Footer

st.markdown("---")

st.markdown("Already have an account?")
if st.button("Login Here", use_container_width=True):
    st.switch_page("pages/login.py")

st.markdown("---")
st.caption("Your information is secure and encrypted")

