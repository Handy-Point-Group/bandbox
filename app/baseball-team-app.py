#%% Imports

import pandas as pd
import streamlit as st
import sys, shutil, pathlib
from utils import (
    get_auth_manager, 
    require_auth, 
    get_supabase_client,
    render_org_team_switcher,
    get_active_organization,
    get_active_team
)

# cache resets
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

#%% page definitions

# Auth pages (login/signup)
login_page = st.Page("pages/login.py", title="Login", icon=":material/login:")
signup_page = st.Page("pages/signup.py", title="Sign Up", icon=":material/person_add:")

# Main team pages (require organization)
roster = st.Page("pages/roster-page.py",title="Home",icon=":material/light_mode:")
team_leaderboards = st.Page("pages/team-leaderboards.py",title="Leaderboards",icon=":material/social_leaderboard:")
plate_discipline_tracking = st.Page("pages/plate-discipline-tracking.py",title="Plate Discipline Tracking",icon=":material/background_dot_small:")

# Coach pages
coach_dashboard = st.Page("pages/coach-dashboard.py",title="My Teams",icon=":material/sports_baseball:")

# Admin pages
admin_user_management = st.Page("pages/admin-user-management.py",title="User Management",icon=":material/admin_panel_settings:")
authorized_users = st.Page("pages/authorized-users.py",title="Authorized Users",icon=":material/verified_user:")
org_admin_dashboard = st.Page("pages/org-admin-dashboard.py",title="Org Dashboard",icon=":material/dashboard:")
superadmin_organizations = st.Page("pages/superadmin-organizations.py",title="Organizations",icon=":material/business:")

#%% Run the App
st.set_page_config(
    page_title="Bandbox",
    page_icon=r"app/images/bandbox.png",
    layout="wide"
)

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

# Initialize authentication
auth = get_auth_manager()

# Check if user is authenticated
if not auth.check_authentication():
    # Hide sidebar completely when not logged in
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
            [data-testid="stSidebarCollapsedControl"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Use navigation with auth pages (login as default)
    auth_nav = st.navigation([login_page, signup_page], position="hidden")
    auth_nav.run()
    st.stop()

# Only show logo and navigation AFTER authentication
st.logo(r'app/images/bandbox.png', size='large')

# Display user info in sidebar
auth.display_user_info()

# Get current user and organization
current_user = auth.get_current_user()
user_role = current_user.get('role', 'player') if current_user else 'player'

# Debug: Show current role in sidebar
st.sidebar.caption(f"🔑 Role: {user_role}")

# Render org/team switcher for players and coaches
supabase = get_supabase_client()
if current_user:
    active_org, active_team = render_org_team_switcher(supabase, current_user)
else:
    active_org, active_team = None, None

# Use active organization (from switcher) or fall back to primary
current_org = active_org or auth.get_current_organization()

# Build navigation based on organization and role
pages = []

# Personal pages available to ALL users (with or without organization)
personal_pages = [player_onboarding, player_page, data_input]

# If user has an organization, show team pages
if current_org:
    pages = [
        roster,
        team_leaderboards,
        player_page,
        data_input,
        plate_discipline_tracking,
        player_onboarding  # Add at the end for users with org
    ]
else:
    # User without organization - show only personal pages
    pages = personal_pages

# Add coach dashboard for coaches (check role directly too)
if user_role in ['coach', 'admin', 'admin-org', 'admin-team', 'superadmin'] or auth.has_role('coach'):
    pages.append(coach_dashboard)

# Add admin pages based on role
if user_role in ['admin', 'admin-team', 'admin-org', 'superadmin'] or auth.has_role('team_admin'):
    pages.append(admin_user_management)

if user_role in ['admin-org', 'superadmin'] or auth.has_role('admin-org'):
    pages.append(org_admin_dashboard)
    pages.append(authorized_users)

if user_role == 'superadmin' or auth.has_role('superadmin'):
    pages.append(superadmin_organizations)

# Check if we still need to show welcome page (shouldn't happen now as we have personal pages)
if not pages:
    st.title("Welcome to Bandbox!")
    st.markdown("---")
    
    st.success("""
    ### Your account has been created successfully!
    """)
    
    st.info("""
    **Get started by creating your player profile:**
    
    Add your baseball information (positions, stats, etc.)
    Set your goals and track your progress
    Upload your training data
    Join organizations when invited by coaches
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Create Your Player Profile Now", use_container_width=True, type="primary"):
            st.switch_page("pages/player-onboarding.py")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Your Account Info")
        if current_user:
            st.write(f"**Name:** {current_user.get('full_name', 'N/A')}")
            st.write(f"**Email:** {current_user.get('email', 'N/A')}")
            st.write(f"**Role:** {current_user.get('role', 'player').title()}")
    
    with col2:
        st.markdown("#### Organization Status")
        st.write("**Organization:** Not assigned yet")
        st.write("**Status:** Waiting for invitation")
        st.caption("You can still use Bandbox! Create your player profile to get started.")
    
    st.stop()

# Show navigation
nav = st.navigation(pages)
nav.run()