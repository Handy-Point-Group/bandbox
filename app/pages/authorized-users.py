#%% Imports

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
sys.path.append('..')
from utils import (
    get_auth_manager, 
    require_auth, 
    get_supabase_client,
    get_current_user
)

#%% Page Configuration

st.set_page_config(
    page_title="Authorized Users",
    page_icon="✅",
    layout="wide"
)

#%% Authentication & Authorization

# Require authentication
auth = get_auth_manager()
require_auth()

current_user = get_current_user()
supabase = get_supabase_client()

# Check authorization - must be superadmin or admin-org
user_role = current_user.get('role', 'user')
if user_role not in ['superadmin', 'admin-org', 'admin-team']:
    st.error("🚫 Access Denied: This page is only accessible to administrators.")
    st.stop()

#%% Page Title

st.title("✅ Authorized Users Management")
st.markdown("Manage users who are pre-authorized to join organizations")
st.markdown("---")

#%% Get Organizations

organizations = supabase.get_all_organizations()

# Filter organizations based on user role
if user_role == 'superadmin':
    available_orgs = organizations
elif user_role in ['admin-org', 'admin-team']:
    # Only show user's organization
    user_org_id = current_user.get('primary_organization_id')
    available_orgs = [org for org in organizations if org['id'] == user_org_id]
else:
    available_orgs = []

if not available_orgs:
    st.error("No organizations available.")
    st.stop()

#%% Tabs

tab1, tab2 = st.tabs(["➕ Add Authorized User", "📋 View Authorized Users"])

#%% Tab 1: Add Authorized User

with tab1:
    st.subheader("Add Authorized User")
    st.markdown("Pre-authorize a user to join an organization with a specific role.")
    
    with st.form("add_authorized_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Organization selection
            org_dict = {org['name']: org['id'] for org in available_orgs}
            selected_org_name = st.selectbox(
                "Organization *",
                options=list(org_dict.keys()),
                help="Select the organization this user will join"
            )
            selected_org_id = org_dict[selected_org_name]
            
            auth_email = st.text_input(
                "Email Address *",
                placeholder="user@example.com",
                help="Email address of the user to authorize"
            )
            
            auth_full_name = st.text_input(
                "Full Name",
                placeholder="John Doe",
                help="Full name of the user (optional)"
            )
        
        with col2:
            # Role selection - limit based on current user's role
            if user_role == 'superadmin':
                role_options = ['player', 'coach', 'admin', 'admin-team', 'admin-org']
            elif user_role == 'admin-org':
                role_options = ['player', 'coach', 'admin', 'admin-team']
            else:
                role_options = ['player', 'coach', 'admin']
            
            auth_role = st.selectbox(
                "Assigned Role *",
                options=role_options,
                format_func=lambda x: {
                    'player': 'Player - Basic access',
                    'coach': 'Coach - Can edit and upload data',
                    'admin': 'Admin - Can manage team',
                    'admin-team': 'Team Admin - Can manage team users',
                    'admin-org': 'Organization Admin - Full org control'
                }[x],
                help="Role that will be assigned when user signs up"
            )
            
            auth_note = st.text_area(
                "Authorization Note",
                placeholder="e.g., Head Coach, Assistant Coach, Team Manager",
                help="Optional note about this authorization",
                height=120
            )
        
        submit_button = st.form_submit_button(
            "✅ Add Authorized User",
            use_container_width=True,
            type="primary"
        )
        
        if submit_button:
            # Validation
            if not auth_email or '@' not in auth_email:
                st.error("❌ Please enter a valid email address")
            else:
                # Check if user already exists
                existing_user = supabase.get_user_by_email(auth_email)
                if existing_user:
                    st.error(f"❌ User with email {auth_email} already exists in the system")
                else:
                    # Check if already authorized
                    existing_auth = supabase.check_user_authorized(auth_email, selected_org_id)
                    if existing_auth:
                        st.error(f"❌ User {auth_email} is already authorized for this organization")
                    else:
                        # Add authorized user
                        result = supabase.add_authorized_user(
                            email=auth_email,
                            organization_id=selected_org_id,
                            assigned_role=auth_role,
                            authorized_by=current_user['id'],
                            full_name=auth_full_name if auth_full_name else None,
                            authorization_note=auth_note if auth_note else None
                        )
                        
                        if result:
                            st.success(f"✅ User {auth_email} has been authorized!")
                            st.info(f"📧 They can now sign up and will be assigned the '{auth_role}' role.")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to authorize user. Please try again.")

#%% Tab 2: View Authorized Users

with tab2:
    st.subheader("Authorized Users")
    
    # Organization filter
    if user_role == 'superadmin':
        filter_org_options = ["All Organizations"] + list(org_dict.keys())
        selected_filter_org = st.selectbox(
            "Filter by Organization",
            options=filter_org_options
        )
    else:
        selected_filter_org = selected_org_name
    
    # Fetch authorized users
    if selected_filter_org == "All Organizations":
        # Get all authorized users for all organizations
        all_authorized = []
        for org in available_orgs:
            org_authorized = supabase.get_authorized_users_by_organization(org['id'])
            for auth_user in org_authorized:
                auth_user['organization_name'] = org['name']
            all_authorized.extend(org_authorized)
        authorized_users = all_authorized
    else:
        filter_org_id = org_dict[selected_filter_org]
        authorized_users = supabase.get_authorized_users_by_organization(filter_org_id)
        # Add organization name
        for auth_user in authorized_users:
            auth_user['organization_name'] = selected_filter_org
    
    # Status filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            options=["All", "Pending Signup", "Signed Up", "Inactive"]
        )
    
    with col2:
        role_filter = st.selectbox(
            "Role",
            options=["All"] + ['player', 'coach', 'admin', 'admin-team', 'admin-org']
        )
    
    # Apply filters
    filtered_users = authorized_users
    
    if status_filter == "Pending Signup":
        filtered_users = [u for u in filtered_users if not u.get('has_signed_up') and u.get('is_active')]
    elif status_filter == "Signed Up":
        filtered_users = [u for u in filtered_users if u.get('has_signed_up')]
    elif status_filter == "Inactive":
        filtered_users = [u for u in filtered_users if not u.get('is_active')]
    
    if role_filter != "All":
        filtered_users = [u for u in filtered_users if u.get('assigned_role') == role_filter]
    
    st.markdown(f"**Showing {len(filtered_users)} of {len(authorized_users)} authorized users**")
    
    if filtered_users:
        # Create DataFrame
        df = pd.DataFrame(filtered_users)
        
        # Format dates
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
        if 'signed_up_at' in df.columns:
            df['signed_up_at'] = pd.to_datetime(df['signed_up_at']).dt.strftime('%Y-%m-%d')
        
        # Add status column
        df['status'] = df.apply(
            lambda row: '✅ Signed Up' if row.get('has_signed_up') 
            else '❌ Inactive' if not row.get('is_active')
            else '⏳ Pending',
            axis=1
        )
        
        # Select columns to display
        display_cols = [
            'email', 'full_name', 'organization_name', 'assigned_role', 
            'status', 'authorization_note', 'created_at'
        ]
        available_cols = [col for col in display_cols if col in df.columns]
        
        st.dataframe(
            df[available_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Detailed view
        st.markdown("---")
        st.subheader("User Details")
        
        user_emails = {f"{u['email']} ({u['organization_name']})": u for u in filtered_users}
        selected_user_key = st.selectbox(
            "Select User to View Details",
            options=list(user_emails.keys())
        )
        
        if selected_user_key:
            selected_auth_user = user_emails[selected_user_key]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Authorization Details")
                st.write(f"**Email:** {selected_auth_user.get('email', 'N/A')}")
                st.write(f"**Full Name:** {selected_auth_user.get('full_name', 'N/A')}")
                st.write(f"**Organization:** {selected_auth_user.get('organization_name', 'N/A')}")
                st.write(f"**Assigned Role:** {selected_auth_user.get('assigned_role', 'N/A')}")
                
                status = '✅ Signed Up' if selected_auth_user.get('has_signed_up') else \
                        '❌ Inactive' if not selected_auth_user.get('is_active') else '⏳ Pending Signup'
                st.write(f"**Status:** {status}")
                
                if selected_auth_user.get('authorization_note'):
                    st.write(f"**Note:** {selected_auth_user.get('authorization_note')}")
            
            with col2:
                st.markdown("#### Timestamps")
                st.write(f"**Created:** {selected_auth_user.get('created_at', 'N/A')}")
                if selected_auth_user.get('signed_up_at'):
                    st.write(f"**Signed Up:** {selected_auth_user.get('signed_up_at', 'N/A')}")
                
                # Actions
                st.markdown("#### Actions")
                
                if not selected_auth_user.get('has_signed_up') and selected_auth_user.get('is_active'):
                    if st.button("🚫 Revoke Authorization", key="revoke"):
                        if supabase.remove_authorized_user(selected_auth_user['id']):
                            st.success("✅ Authorization revoked")
                            st.rerun()
                        else:
                            st.error("❌ Failed to revoke authorization")
    else:
        st.info("No authorized users found matching your filters")

#%% Footer

st.markdown("---")
st.caption(f"Logged in as: {current_user.get('email', 'Unknown')} | Role: {current_user.get('role', 'Unknown').title()}")

