#%% Imports

import streamlit as st
import sys
sys.path.append('..')
from utils import get_password_auth, get_supabase_client

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
            
            st.success(f"You are pre-authorized to join **{auth_org['name']}**")
            st.info(f"Your assigned role will be: **{authorized_record['assigned_role']}**")
            
            if authorized_record.get('authorization_note'):
                st.info(f"Note: {authorized_record['authorization_note']}")
            
            # Store for later use
            selected_org_id = auth_org['id']
            pre_authorized = True
            assigned_role = authorized_record['assigned_role']
            auth_record_id = authorized_record['id']
        else:
            # User NOT pre-authorized - allow signup without organization
            st.info("**No pre-authorization found**")
            selected_org_id = None
    else:
        # Email not entered yet
        st.info("Enter your email address above. If you're pre-authorized, your organization will be automatically assigned.")
    
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
                        
                        # Create player profile if provided
                        player_profile_created = False
                        if player_role and player_role != "Select":
                            try:
                                # Only create player profile if role is "Player" and we have required info
                                if player_role == "Player":
                                    # Split full name for player profile
                                    name_parts = full_name.split()
                                    first_name = name_parts[0] if len(name_parts) > 0 else full_name
                                    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                                    
                                    # Build survey data
                                    survey_data = {}
                                    if batting_hand and batting_hand != "Select":
                                        survey_data['batting_hand'] = batting_hand
                                    if throwing_hand and throwing_hand != "Select":
                                        survey_data['throwing_hand'] = throwing_hand
                                    if years_playing:
                                        survey_data['years_playing'] = years_playing
                                    if current_team:
                                        survey_data['current_team'] = current_team
                                    if travel_team:
                                        survey_data['travel_team'] = travel_team
                                    if college_interest and college_interest != "Select":
                                        survey_data['college_interest'] = college_interest
                                    if goals:
                                        survey_data['goals'] = goals
                                    
                                    # Build player data
                                    player_data = {
                                        "user_id": new_user['id'],
                                        "first_name": first_name,
                                        "last_name": last_name,
                                        "email": email,
                                        "grad_year": int(grad_year) if player_role == "Player" else None,
                                        "pitcher": pitcher if player_role == "Player" else False,
                                        "pos_1": primary_position if primary_position != "Select Position" else None,
                                        "metadata": {"survey": survey_data, "role": player_role}
                                    }
                                    
                                    # Insert player profile
                                    from datetime import datetime
                                    player_data["created_at"] = datetime.now().isoformat()
                                    player_data["updated_at"] = datetime.now().isoformat()
                                    
                                    from st_supabase_connection import SupabaseConnection
                                    db = st.connection("supabase", type=SupabaseConnection)
                                    response = db.client.table("players").insert(player_data).execute()
                                    
                                    if response.data:
                                        player_profile_created = True
                            except Exception as e:
                                # Don't fail signup if player profile creation fails
                                st.warning(f"Account created but player profile failed: {e}")
                        
                        st.success("Account created successfully!")
                        
                        if player_profile_created:
                            st.success("Player profile created too!")
                        
                        if pre_authorized:
                            if assigned_role != 'player':
                                st.success(f"You have been assigned the '{assigned_role}' role!")
                                st.info(f"You have been added to the organization.")
                        
                        if player_profile_created:
                            st.info("Your player profile is ready! You can view and update it anytime.")
                        elif player_role == "Player":
                            st.info("You can complete your player profile after logging in.")
                        
                        st.balloons()
                        st.info("Redirecting to login page...")
                        
                        # Auto-redirect to login page
                        import time
                        time.sleep(2)  # Give user time to see the success message
                        st.switch_page("pages/login.py")
                    else:
                        st.error("Failed to create account. Please try again or contact support.")

#%% Footer

st.markdown("---")

st.markdown("Already have an account?")
if st.button("Login Here", use_container_width=True):
    st.switch_page("pages/login.py")

st.markdown("---")
st.caption("Your information is secure and encrypted")

