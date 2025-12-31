#%% Imports

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
sys.path.append('..')
from utils import (
    get_auth_manager, 
    require_auth, 
    require_role,
    get_supabase_client,
    get_current_user
)

#%% Initialize

# Require authentication and team_admin role or higher
auth = get_auth_manager()
require_auth()
require_role('team_admin')

supabase = get_supabase_client()
current_user = get_current_user()

#%% Page Configuration

st.set_page_config(
    page_title="Bandbox - User Management",
    page_icon=r"app/images/bandbox.png",
    layout="wide"
)

st.title("User Management")
st.markdown("---")

#%% Tabs

tab1, tab2, tab3 = st.tabs(["View Users", "Create User", "Organizations"])

#%% Tab 1: View Users

with tab1:
    st.subheader("All Users")
    
    # Get organization filter
    organizations = supabase.get_all_organizations()
    org_options = {"All": None}
    org_options.update({org['name']: org['id'] for org in organizations})
    
    selected_org = st.selectbox(
        "Filter by Organization",
        options=list(org_options.keys())
    )
    
    # Fetch users
    if selected_org == "All":
        users = supabase.get_all_users()
    else:
        org_id = org_options[selected_org]
        users = supabase.get_users_by_organization(org_id)
    
    if users:
        # Create DataFrame for display
        user_df = pd.DataFrame(users)
        
        # Add organization names
        if 'primary_organization_id' in user_df.columns:
            org_map = {org['id']: org['name'] for org in organizations}
            user_df['organization'] = user_df['primary_organization_id'].map(org_map)
        
        # Format dates
        if 'created_at' in user_df.columns:
            user_df['created_at'] = pd.to_datetime(user_df['created_at']).dt.strftime('%Y-%m-%d')
        if 'last_login' in user_df.columns:
            user_df['last_login'] = pd.to_datetime(user_df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Select columns to display
        display_cols = ['email', 'full_name', 'organization', 'role', 'is_active', 'last_login', 'created_at']
        available_cols = [col for col in display_cols if col in user_df.columns]
        
        st.dataframe(
            user_df[available_cols],
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        st.subheader("Edit User")
        
        # Select user to edit
        user_emails = {user['email']: user for user in users}
        selected_email = st.selectbox("Select User to Edit", options=list(user_emails.keys()))
        
        if selected_email:
            selected_user = user_emails[selected_email]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User:** {selected_user.get('full_name', 'N/A')}")
                st.write(f"**Email:** {selected_user.get('email', 'N/A')}")
                st.write(f"**Current Role:** {selected_user.get('role', 'user')}")
                st.write(f"**Status:** {'Active' if selected_user.get('is_active') else 'Inactive'}")
            
            with col2:
                # Change role
                role_options = ['player', 'coach', 'team_admin', 'organization_admin', 'super_admin']
                current_role = selected_user.get('role', 'player')
                role_index = role_options.index(current_role) if current_role in role_options else 0
                
                new_role = st.selectbox(
                    "Change Role",
                    options=role_options,
                    index=role_index,
                    format_func=lambda x: {
                        'player': 'Player',
                        'coach': 'Coach',
                        'team_admin': 'Team Admin',
                        'organization_admin': 'Organization Admin',
                        'super_admin': 'Super Admin'
                    }[x]
                )
                
                if st.button("Update Role", key="update_role", type='primary'):
                    if supabase.update_user_role(selected_user['id'], new_role):
                        st.success(f"Role updated to '{new_role}'")
                        st.rerun()
                    else:
                        st.error("Failed to update role")
                
                # Toggle active status
                current_status = selected_user.get('is_active', False)
                if current_status:
                    if st.button("Deactivate User", key="deactivate", type='primary'):
                        if supabase.deactivate_user(selected_user['id']):
                            st.success("User deactivated")
                            st.rerun()
                        else:
                            st.error("Failed to deactivate user")
                else:
                    if st.button("Activate User", key="activate", type='primary'):
                        if supabase.activate_user(selected_user['id']):
                            st.success("User activated")
                            st.rerun()
                        else:
                            st.error("Failed to activate user")
    else:
        st.info("No users found")

#%% Tab 2: Create User

with tab2:
    st.subheader("Create New User")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email Address*", placeholder="user@example.com")
            new_full_name = st.text_input("Full Name*", placeholder="John Doe")
        
        with col2:
            # Organization selection
            if organizations:
                org_names = {org['name']: org['id'] for org in organizations}
                selected_org_name = st.selectbox("Organization*", options=list(org_names.keys()))
                new_org_id = org_names[selected_org_name]
            else:
                st.warning("No organizations found. Please create an organization first.")
                new_org_id = None
            
            # Role selection
            new_role = st.selectbox(
                "Role*",
                options=['player', 'coach', 'team_admin', 'organization_admin', 'super_admin'],
                format_func=lambda x: {
                    'player': 'Player - Basic access',
                    'coach': 'Coach - Can edit and upload data',
                    'team_admin': 'Team Admin - Can manage team users',
                    'organization_admin': 'Organization Admin - Full org control',
                    'super_admin': 'Super Admin - System-wide access'
                }[x],
                help="Role determines access level in the application"
            )
        
        # Google ID (optional)
        new_google_id = st.text_input(
            "Google ID (Optional)", 
            placeholder="Leave blank if user hasn't logged in yet",
            help="This will be automatically filled when user logs in with Google"
        )
        
        submit_create = st.form_submit_button("Create User", use_container_width=True)
        
        if submit_create:
            if not new_email or not new_full_name:
                st.error("Email and Full Name are required")
            elif not new_org_id:
                st.error("Please select an organization")
            else:
                # Check if user already exists
                existing_user = supabase.get_user_by_email(new_email)
                if existing_user:
                    st.error(f"User with email {new_email} already exists")
                else:
                    # Create user
                    created_user = supabase.create_user(
                        email=new_email,
                        full_name=new_full_name,
                        organization_id=new_org_id,
                        google_id=new_google_id if new_google_id else None,
                        role=new_role
                    )
                    
                    if created_user:
                        st.success(f"User created successfully: {new_email}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Failed to create user. Please check logs.")

#%% Tab 3: Organizations

with tab3:
    st.subheader("Organizations")
    
    # Display existing organizations
    if organizations:
        org_df = pd.DataFrame(organizations)
        
        # Format dates
        if 'created_at' in org_df.columns:
            org_df['created_at'] = pd.to_datetime(org_df['created_at']).dt.strftime('%Y-%m-%d')
        
        # Select columns
        display_cols = ['name', 'is_active', 'created_at']
        available_cols = [col for col in display_cols if col in org_df.columns]
        
        st.dataframe(
            org_df[available_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No organizations found")
    
    st.markdown("---")
    st.subheader("Create New Organization")
    
    with st.form("create_org_form"):
        org_name = st.text_input("Organization Name*", placeholder="Team Name or Organization")
        
        # Optional settings
        st.write("**Optional Settings:**")
        theme = st.selectbox("Theme", options=["light", "dark"])
        
        submit_org = st.form_submit_button("Create Organization", use_container_width=True)
        
        if submit_org:
            if not org_name:
                st.error("Organization name is required")
            else:
                # Check if organization already exists
                existing_orgs = [org for org in organizations if org['name'].lower() == org_name.lower()]
                if existing_orgs:
                    st.error(f"Organization '{org_name}' already exists")
                else:
                    settings = {
                        "theme": theme,
                        "features": ["plate_discipline", "rapsodo"]
                    }
                    
                    created_org = supabase.create_organization(org_name, settings)
                    
                    if created_org:
                        st.success(f"Organization created: {org_name}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Failed to create organization")