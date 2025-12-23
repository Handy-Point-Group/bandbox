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
player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
plate_discipline_tracking = st.Page("pages/plate-discipline-tracking.py",title="Plate Discipline Tracking",icon=":material/background_dot_small:")
data_input = st.Page("pages/data-input.py",title="Data Upload",icon=":material/upload:")

# Coach pages
coach_dashboard = st.Page("pages/coach-dashboard.py",title="My Teams",icon=":material/sports_baseball:")

# Admin pages
admin_user_management = st.Page("pages/admin-user-management.py",title="User Management",icon=":material/admin_panel_settings:")
authorized_users = st.Page("pages/authorized-users.py",title="Authorized Users",icon=":material/verified_user:")
org_admin_dashboard = st.Page("pages/org-admin-dashboard.py",title="Org Dashboard",icon=":material/dashboard:")
superadmin_organizations = st.Page("pages/superadmin-organizations.py",title="Organizations",icon=":material/business:")

#%% Run the App
st.set_page_config(layout="wide")

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
st.logo(r'app/images/lighthouse 1.png', size='large')

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

# If user has an organization, show team pages
if current_org:
    pages = [
        roster,
        team_leaderboards,
        player_page,
        data_input,
        plate_discipline_tracking
    ]

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

# If user has no pages (no org and not admin), show a welcome page
if not pages:
    st.title("👋 Welcome to BandBox!")
    st.markdown("---")
    
    st.info("""
    ### 🎉 Your account has been created successfully!
    
    **Next Steps:**
    
    1. **Wait for an invitation** - Your organization administrator will invite you to join their team
    2. **Check your email** - You may receive a notification when you're added to an organization
    3. **Contact your administrator** - If you're not sure who to contact, reach out to your team coach or manager
    
    Once you're added to an organization, you'll see team pages appear in the navigation menu.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📧 Your Account Info")
        if current_user:
            st.write(f"**Name:** {current_user.get('full_name', 'N/A')}")
            st.write(f"**Email:** {current_user.get('email', 'N/A')}")
            st.write(f"**Role:** {current_user.get('role', 'player').title()}")
    
    with col2:
        st.markdown("#### 🏢 Organization Status")
        st.write("**Organization:** Not assigned yet")
        st.write("**Status:** ⏳ Waiting for invitation")
    
    st.stop()

# Show navigation
nav = st.navigation(pages)
nav.run()