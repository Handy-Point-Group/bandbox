#%% Imports

import pandas as pd
import streamlit as st
import sys, shutil, pathlib
from utils import get_auth_manager, require_auth

# cache resets
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

#%% page definitions

# Personal pages (available to all users)
player_onboarding = st.Page("pages/player-onboarding.py",title="Player Profile",icon=":material/person:")
player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
data_input = st.Page("pages/data-input.py",title="Data Upload",icon=":material/upload:")

# Main team pages (require organization)
roster = st.Page("pages/roster-page.py",title="Home",icon=":material/light_mode:")
team_leaderboards = st.Page("pages/team-leaderboards.py",title="Leaderboards",icon=":material/social_leaderboard:")
plate_discipline_tracking = st.Page("pages/plate-discipline-tracking.py",title="Plate Discipline Tracking",icon=":material/background_dot_small:")

# Admin pages
admin_user_management = st.Page("pages/admin-user-management.py",title="User Management",icon=":material/admin_panel_settings:")
authorized_users = st.Page("pages/authorized-users.py",title="Authorized Users",icon=":material/verified_user:")
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
    
    # Show clean login/signup screen - NO SIDEBAR, NO LOGO, NO NAVIGATION
    
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>⚾ Welcome to BandBox</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2em;'>Track Your Baseball Performance</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### 🔐 Access Your Account")
        
        if st.button("🔐 Login to Existing Account", use_container_width=True, type="primary"):
            st.switch_page("pages/login.py")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📝 Create New Account", use_container_width=True):
            st.switch_page("pages/signup.py")
        
        st.markdown("---")
        
        with st.expander("ℹ️ About BandBox"):
            st.markdown("""
            **BandBox** is a comprehensive baseball performance tracking platform that helps:
            
            - 📊 Track player statistics and performance
            - ⚾ Analyze hitting and pitching data
            - 📈 View team leaderboards
            - 🎯 Monitor plate discipline
            - 📁 Upload and manage data
            
            Get started by creating an account or logging in above!
            """)
    
    st.stop()

# Only show logo and navigation AFTER authentication
st.logo(r'app/images/lighthouse 1.png', size='large')

# Display user info in sidebar
auth.display_user_info()

# Get current user and organization
current_user = auth.get_current_user()
current_org = auth.get_current_organization()
user_role = current_user.get('role', 'player') if current_user else 'player'

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

# Add admin pages based on role
if auth.has_role('team_admin'):
    pages.append(admin_user_management)

if auth.has_role('admin-org'):
    pages.append(authorized_users)

if auth.has_role('superadmin'):
    pages.append(superadmin_organizations)

# Check if we still need to show welcome page (shouldn't happen now as we have personal pages)
if not pages:
    st.title("👋 Welcome to BandBox!")
    st.markdown("---")
    
    st.success("""
    ### 🎉 Your account has been created successfully!
    """)
    
    st.info("""
    **Get started by creating your player profile:**
    
    📋 Add your baseball information (positions, stats, etc.)
    🎯 Set your goals and track your progress
    📊 Upload your training data
    🏢 Join organizations when invited by coaches
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎉 Create Your Player Profile Now", use_container_width=True, type="primary"):
            st.switch_page("pages/player-onboarding.py")
    
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
        st.caption("You can still use BandBox! Create your player profile to get started.")
    
    st.stop()

# Show navigation
nav = st.navigation(pages)
nav.run()