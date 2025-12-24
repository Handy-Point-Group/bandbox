#%% Imports

import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, datetime
import sys
sys.path.append('..')
from utils import get_auth_manager, get_supabase_client

#%% Page Configuration

st.set_page_config(page_title="Player Onboarding - BandBox", page_icon="⚾", layout="wide")

#%% Authentication Check
auth = get_auth_manager()
supabase_client = get_supabase_client()

if not auth.check_authentication():
    st.error("⚠️ You must be logged in to access this page.")
    st.stop()

current_user = auth.get_current_user()
current_org = auth.get_current_organization()

#%% Connect to Supabase
db = st.connection("supabase", type=SupabaseConnection)

#%% Check if player profile exists

def get_user_player_profile(user_id):
    """Get player profile linked to user"""
    try:
        response = db.client.table("players").select("*").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching player profile: {e}")
        return None

existing_profile = get_user_player_profile(current_user['id'])

#%% Header

st.title("⚾ Player Profile & Onboarding")

if existing_profile:
    st.info("✅ You already have a player profile. You can update it below.")
else:
    st.success("👋 Welcome! Let's create your player profile.")

st.markdown("---")

#%% Main Form

with st.form("player_onboarding_form", clear_on_submit=False):
    st.subheader("📋 Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input(
            "First Name *",
            value=existing_profile.get('first_name', '') if existing_profile else current_user.get('full_name', '').split()[0] if current_user.get('full_name') else '',
            placeholder="John"
        )
        
        # Calculate default graduation year (current year + 4 for typical high schooler)
        current_year = datetime.now().year
        default_grad_year = current_year + 4
        
        grad_year = st.number_input(
            "High School Graduation Year *",
            min_value=current_year - 10,
            max_value=current_year + 10,
            value=existing_profile.get('grad_year', default_grad_year) if existing_profile else default_grad_year,
            step=1
        )
        
        birthdate = st.date_input(
            "Date of Birth",
            value=existing_profile.get('birthdate') if existing_profile and existing_profile.get('birthdate') else None,
            min_value=date(1990, 1, 1),
            max_value=date.today()
        )
    
    with col2:
        last_name = st.text_input(
            "Last Name *",
            value=existing_profile.get('last_name', '') if existing_profile else current_user.get('full_name', '').split()[-1] if current_user.get('full_name') and len(current_user.get('full_name', '').split()) > 1 else '',
            placeholder="Doe"
        )
        
        pitcher = st.checkbox(
            "I am a Pitcher",
            value=existing_profile.get('pitcher', False) if existing_profile else False
        )
    
    st.divider()
    
    st.subheader("⚾ Position Information")
    
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pos_1_current = existing_profile.get('pos_1', 'Select Position') if existing_profile else 'Select Position'
        pos_1_index = position_options.index(pos_1_current) if pos_1_current in position_options else 0
        pos_1 = st.selectbox("Primary Position", options=position_options, index=pos_1_index)
    
    with col2:
        pos_2_current = existing_profile.get('pos_2', 'Select Position') if existing_profile else 'Select Position'
        pos_2_index = position_options.index(pos_2_current) if pos_2_current in position_options else 0
        pos_2 = st.selectbox("Secondary Position", options=position_options, index=pos_2_index)
    
    with col3:
        pos_3_current = existing_profile.get('pos_3', 'Select Position') if existing_profile else 'Select Position'
        pos_3_index = position_options.index(pos_3_current) if pos_3_current in position_options else 0
        pos_3 = st.selectbox("Tertiary Position", options=position_options, index=pos_3_index)
    
    st.divider()
    
    st.subheader("🔗 Integration IDs (Optional)")
    st.caption("These help link your data from external systems like Rapsodo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        rapsodo_id = st.text_input(
            "Rapsodo Player ID",
            value=existing_profile.get('rapsodo_id', '') if existing_profile else '',
            placeholder="Your Rapsodo ID (if you have one)"
        )
    
    with col2:
        email = st.text_input(
            "Email (for data matching)",
            value=existing_profile.get('email', current_user.get('email', '')) if existing_profile else current_user.get('email', ''),
            placeholder="your.email@example.com"
        )
    
    st.divider()
    
    st.subheader("📊 Player Survey")
    st.caption("Help us understand your background and goals")
    
    # Get existing survey data from metadata
    existing_survey = existing_profile.get('metadata', {}).get('survey', {}) if existing_profile else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        batting_hand = st.selectbox(
            "Batting Hand *",
            options=["Select", "Right", "Left", "Switch"],
            index=["Select", "Right", "Left", "Switch"].index(existing_survey.get('batting_hand', 'Select')) if existing_survey.get('batting_hand') in ["Select", "Right", "Left", "Switch"] else 0
        )
        
        throwing_hand = st.selectbox(
            "Throwing Hand *",
            options=["Select", "Right", "Left"],
            index=["Select", "Right", "Left"].index(existing_survey.get('throwing_hand', 'Select')) if existing_survey.get('throwing_hand') in ["Select", "Right", "Left"] else 0
        )
        
        height_ft = st.number_input(
            "Height (feet)",
            min_value=4,
            max_value=7,
            value=existing_survey.get('height_ft', 5),
            step=1
        )
        
        height_in = st.number_input(
            "Height (inches)",
            min_value=0,
            max_value=11,
            value=existing_survey.get('height_in', 10),
            step=1
        )
        
        weight = st.number_input(
            "Weight (lbs)",
            min_value=80,
            max_value=400,
            value=existing_survey.get('weight', 150),
            step=5
        )
    
    with col2:
        years_playing = st.number_input(
            "Years Playing Baseball",
            min_value=0,
            max_value=20,
            value=existing_survey.get('years_playing', 0),
            step=1
        )
        
        current_team = st.text_input(
            "Current Team/School",
            value=existing_survey.get('current_team', ''),
            placeholder="e.g., Lincoln High School Varsity"
        )
        
        travel_team = st.text_input(
            "Travel/Club Team (if any)",
            value=existing_survey.get('travel_team', ''),
            placeholder="e.g., Elite Baseball Club 16U"
        )
        
        college_interest = st.selectbox(
            "College Baseball Interest",
            options=["Select", "Division I", "Division II", "Division III", "NAIA", "JUCO", "Not Interested", "Undecided"],
            index=["Select", "Division I", "Division II", "Division III", "NAIA", "JUCO", "Not Interested", "Undecided"].index(existing_survey.get('college_interest', 'Select')) if existing_survey.get('college_interest') in ["Select", "Division I", "Division II", "Division III", "NAIA", "JUCO", "Not Interested", "Undecided"] else 0
        )
    
    st.divider()
    
    st.subheader("🎯 Goals & Notes")
    
    goals = st.text_area(
        "Your Baseball Goals",
        value=existing_survey.get('goals', ''),
        placeholder="What are your goals for this season? What skills do you want to improve?",
        height=100
    )
    
    notes = st.text_area(
        "Additional Notes",
        value=existing_survey.get('notes', ''),
        placeholder="Any injuries, medical conditions, or other information your coach should know?",
        height=100
    )
    
    st.divider()
    
    # Submit button
    submitted = st.form_submit_button(
        "💾 Save Player Profile" if existing_profile else "🎉 Create Player Profile",
        use_container_width=True,
        type="primary"
    )
    
    if submitted:
        # Validation
        errors = []
        
        if not first_name or not last_name:
            errors.append("❌ First name and last name are required")
        
        if not grad_year or grad_year < current_year - 10 or grad_year > current_year + 10:
            errors.append("❌ Please enter a valid graduation year")
        
        if batting_hand == "Select":
            errors.append("❌ Please select your batting hand")
        
        if throwing_hand == "Select":
            errors.append("❌ Please select your throwing hand")
        
        # Display errors
        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner("Saving your profile..."):
                try:
                    # Clean up position values
                    def clean_position(pos):
                        if pos == "Select Position" or not pos:
                            return None
                        return pos
                    
                    # Build survey data
                    survey_data = {
                        'batting_hand': batting_hand if batting_hand != "Select" else None,
                        'throwing_hand': throwing_hand if throwing_hand != "Select" else None,
                        'height_ft': height_ft,
                        'height_in': height_in,
                        'weight': weight,
                        'years_playing': years_playing,
                        'current_team': current_team if current_team else None,
                        'travel_team': travel_team if travel_team else None,
                        'college_interest': college_interest if college_interest != "Select" else None,
                        'goals': goals if goals else None,
                        'notes': notes if notes else None
                    }
                    
                    # Build player data
                    player_data = {
                        "user_id": current_user['id'],
                        "first_name": first_name,
                        "last_name": last_name,
                        "grad_year": int(grad_year),
                        "pitcher": pitcher,
                        "pos_1": clean_position(pos_1),
                        "pos_2": clean_position(pos_2),
                        "pos_3": clean_position(pos_3),
                        "rapsodo_id": rapsodo_id if rapsodo_id else None,
                        "email": email if email else current_user.get('email'),
                        "birthdate": birthdate.strftime('%Y-%m-%d') if birthdate else None,
                        "metadata": {"survey": survey_data}
                    }
                    
                    if existing_profile:
                        # Update existing profile
                        player_data["updated_at"] = datetime.now().isoformat()
                        response = db.client.table("players").update(player_data).eq("id", existing_profile['id']).execute()
                        
                        if response.data:
                            st.success("✅ Player profile updated successfully!")
                            st.balloons()
                            st.info("Redirecting to your player page...")
                            import time
                            time.sleep(2)
                            st.switch_page("pages/player-page.py")
                        else:
                            st.error("❌ Failed to update profile. Please try again.")
                    else:
                        # Create new profile
                        player_data["created_at"] = datetime.now().isoformat()
                        response = db.client.table("players").insert(player_data).execute()
                        
                        if response.data:
                            st.success("✅ Player profile created successfully!")
                            st.balloons()
                            st.info("🎉 Welcome to BandBox! Redirecting to your player page...")
                            import time
                            time.sleep(2)
                            st.switch_page("pages/player-page.py")
                        else:
                            st.error("❌ Failed to create profile. Please try again.")
                
                except Exception as e:
                    st.error(f"❌ Error saving profile: {e}")
                    st.exception(e)

#%% Footer

st.markdown("---")

with st.expander("ℹ️ Why do we collect this information?"):
    st.markdown("""
    **Your player profile helps:**
    
    - 📊 **Track Your Progress**: Link all your training data and stats to your profile
    - 🎯 **Personalized Insights**: Get tailored recommendations based on your position and goals
    - 👥 **Team Integration**: Easily join organizations and teams when invited
    - 📈 **Performance Analysis**: Compare your stats to players at your level
    - 🎓 **College Recruiting**: Showcase your development to coaches (if interested)
    
    **Privacy**: Your data is secure and only shared with organizations you join.
    """)

st.caption("🔒 Your information is secure and encrypted")

