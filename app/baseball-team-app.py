#%% Imports

import pandas as pd
import streamlit as st
import sys, shutil, pathlib
from utils import get_auth_manager, require_auth

# cache resets
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

#%% page definitions

roster = st.Page("pages/roster-page.py",title="Home",icon=":material/light_mode:")
team_leaderboards = st.Page("pages/team-leaderboards.py",title="Leaderboards",icon=":material/social_leaderboard:")
player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
plate_discipline_tracking = st.Page("pages/plate-discipline-tracking.py",title="Plate Discipline Tracking",icon=":material/background_dot_small:")
data_input = st.Page("pages/data-input.py",title="Data Upload",icon=":material/upload:")
admin_user_management = st.Page("pages/admin-user-management.py",title="User Management",icon=":material/admin_panel_settings:")

#%% Run the App
st.set_page_config(layout="wide")

# Initialize authentication
auth = get_auth_manager()

# Check if user is authenticated
if not auth.check_authentication():
    # Show only login/signup options - NO SIDEBAR, NO LOGO, NO NAVIGATION
    st.warning("⚠️ You must be logged in to access this application.")
    st.info("Please log in or create an account to continue.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔐 Login", use_container_width=True, type="primary"):
            st.switch_page("pages/login.py")
    
    with col2:
        if st.button("📝 Sign Up", use_container_width=True):
            st.switch_page("pages/signup.py")
    
    st.stop()

# Only show logo and navigation AFTER authentication
st.logo(r'app/images/lighthouse 1.png', size='large')

# Display user info in sidebar
auth.display_user_info()

# Build navigation based on user role
pages = [
    roster,
    team_leaderboards,
    player_page,
    data_input,
    plate_discipline_tracking
]

# Add admin page for team_admin and above
if auth.has_role('team_admin'):
    pages.append(admin_user_management)

nav = st.navigation(pages)
nav.run()