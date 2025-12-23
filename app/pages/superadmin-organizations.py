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
    page_title="Superadmin - Organizations",
    page_icon="🏢",
    layout="wide"
)

#%% Authentication & Authorization

# Require authentication
auth = get_auth_manager()
require_auth()

# Check for superadmin role
current_user = get_current_user()
if not current_user or current_user.get('role') != 'superadmin':
    st.error("🚫 Access Denied: This page is only accessible to superadmins.")
    st.stop()

supabase = get_supabase_client()

#%% Page Title

st.title("🏢 Superadmin - Organization Management")
st.markdown("Create and manage organizations across the entire platform")
st.markdown("---")

#%% Tabs

tab1, tab2 = st.tabs(["➕ Create Organization", "📋 View All Organizations"])

#%% Tab 1: Create Organization

with tab1:
    st.subheader("Create New Organization")
    st.markdown("Fill out the form below to create a new organization. Fields marked with * are required.")
    
    with st.form("create_organization_form", clear_on_submit=False):
        # Basic Information
        st.markdown("### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Organization Name*",
                placeholder="e.g., Red Sox Baseball Club",
                help="Internal reference name for the organization"
            )
            
            display_name = st.text_input(
                "Display Name",
                placeholder="e.g., Boston Red Sox",
                help="Public-facing name (optional, defaults to Organization Name)"
            )
            
            org_type = st.selectbox(
                "Organization Type*",
                options=['team', 'league', 'club', 'school', 'other'],
                format_func=lambda x: {
                    'team': '⚾ Team',
                    'league': '🏆 League',
                    'club': '🎯 Club',
                    'school': '🎓 School',
                    'other': '📋 Other'
                }[x]
            )
        
        with col2:
            email = st.text_input(
                "Contact Email",
                placeholder="contact@organization.com"
            )
            
            phone = st.text_input(
                "Phone Number",
                placeholder="+1 (555) 123-4567"
            )
            
            website = st.text_input(
                "Website",
                placeholder="https://www.organization.com"
            )
        
        description = st.text_area(
            "Description",
            placeholder="Brief description of the organization...",
            height=100
        )
        
        # Address Information
        st.markdown("### Address Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            address_line1 = st.text_input(
                "Address Line 1",
                placeholder="123 Main Street"
            )
            
            address_line2 = st.text_input(
                "Address Line 2",
                placeholder="Suite 100 (optional)"
            )
        
        with col2:
            city = st.text_input(
                "City",
                placeholder="Boston"
            )
            
            state = st.text_input(
                "State/Province",
                placeholder="MA"
            )
        
        with col3:
            postal_code = st.text_input(
                "Postal Code",
                placeholder="02101"
            )
            
            country = st.text_input(
                "Country",
                value="USA",
                placeholder="USA"
            )
        
        # Organization Settings
        st.markdown("### Organization Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            is_active = st.checkbox(
                "Active Status",
                value=True,
                help="Whether this organization is currently active"
            )
        
        with col2:
            max_teams = st.number_input(
                "Maximum Teams",
                min_value=1,
                value=1,
                help="Maximum number of teams allowed in this organization"
            )
        
        with col3:
            max_members = st.number_input(
                "Maximum Members",
                min_value=0,
                value=0,
                help="Maximum number of members (0 = unlimited)"
            )
        
        # Branding
        st.markdown("### Branding (Optional)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            logo_url = st.text_input(
                "Logo URL",
                placeholder="https://example.com/logo.png",
                help="URL to organization logo image"
            )
        
        with col2:
            primary_color = st.color_picker(
                "Primary Color",
                value="#1f77b4",
                help="Primary brand color"
            )
        
        with col3:
            secondary_color = st.color_picker(
                "Secondary Color",
                value="#ff7f0e",
                help="Secondary brand color"
            )
        
        # Organization Admin
        st.markdown("### Organization Administrator (Optional)")
        st.info("💡 You can pre-authorize an organization admin who will be able to sign up and manage this organization.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            admin_email = st.text_input(
                "Admin Email Address",
                placeholder="admin@organization.com",
                help="Email of the person who will be the organization administrator"
            )
        
        with col2:
            admin_name = st.text_input(
                "Admin Full Name",
                placeholder="John Doe",
                help="Full name of the organization administrator"
            )
        
        admin_note = st.text_area(
            "Authorization Note",
            placeholder="e.g., Head Coach, Team Manager, etc.",
            help="Optional note about this administrator",
            height=80
        )
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button(
                "✅ Create Organization",
                use_container_width=True,
                type="primary"
            )
        
        if submit_button:
            # Validate required fields
            if not name:
                st.error("❌ Organization Name is required")
            else:
                # Prepare organization data
                org_data = {
                    "name": name,
                    "display_name": display_name if display_name else name,
                    "description": description if description else None,
                    "org_type": org_type,
                    "email": email if email else None,
                    "phone": phone if phone else None,
                    "website": website if website else None,
                    "address_line1": address_line1 if address_line1 else None,
                    "address_line2": address_line2 if address_line2 else None,
                    "city": city if city else None,
                    "state": state if state else None,
                    "postal_code": postal_code if postal_code else None,
                    "country": country if country else "USA",
                    "is_active": is_active,
                    "max_teams": max_teams,
                    "max_members": max_members if max_members > 0 else None,
                    "logo_url": logo_url if logo_url else None,
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                }
                
                # Check if organization already exists
                existing_orgs = supabase.get_all_organizations()
                if any(org['name'].lower() == name.lower() for org in existing_orgs):
                    st.error(f"❌ Organization '{name}' already exists")
                else:
                    # Create organization
                    try:
                        created_org = supabase.create_organization_full(org_data)
                        
                        if created_org:
                            st.success(f"✅ Organization '{name}' created successfully!")
                            
                            # Add organization admin to authorized users if provided
                            if admin_email and admin_email.strip():
                                try:
                                    auth_user = supabase.add_authorized_user(
                                        email=admin_email.strip(),
                                        organization_id=created_org['id'],
                                        assigned_role='admin-org',
                                        authorized_by=current_user['id'],
                                        full_name=admin_name.strip() if admin_name else None,
                                        authorization_note=admin_note.strip() if admin_note else "Organization Administrator"
                                    )
                                    
                                    if auth_user:
                                        st.success(f"✅ Organization admin '{admin_email}' has been authorized!")
                                        st.info(f"📧 {admin_email} can now sign up and will be automatically assigned as organization admin.")
                                    else:
                                        st.warning("⚠️ Organization created but failed to authorize admin user.")
                                except Exception as admin_error:
                                    st.warning(f"⚠️ Organization created but error authorizing admin: {str(admin_error)}")
                            
                            st.balloons()
                            
                            # Display created organization details
                            with st.expander("📋 View Created Organization Details"):
                                st.json(created_org)
                            
                            st.info("💡 Tip: You can manage authorized users through the User Management page.")
                        else:
                            st.error("❌ Failed to create organization. Please check the logs.")
                    except Exception as e:
                        st.error(f"❌ Error creating organization: {str(e)}")

#%% Tab 2: View Organizations

with tab2:
    st.subheader("All Organizations")
    
    # Fetch all organizations
    organizations = supabase.get_all_organizations()
    
    if organizations:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filter by Type",
                options=['All'] + ['team', 'league', 'club', 'school', 'other']
            )
        
        with col2:
            filter_status = st.selectbox(
                "Filter by Status",
                options=['All', 'Active', 'Inactive']
            )
        
        with col3:
            search_term = st.text_input(
                "Search Organizations",
                placeholder="Search by name..."
            )
        
        # Apply filters
        filtered_orgs = organizations
        
        if filter_type != 'All':
            filtered_orgs = [org for org in filtered_orgs if org.get('org_type') == filter_type]
        
        if filter_status == 'Active':
            filtered_orgs = [org for org in filtered_orgs if org.get('is_active', False)]
        elif filter_status == 'Inactive':
            filtered_orgs = [org for org in filtered_orgs if not org.get('is_active', False)]
        
        if search_term:
            filtered_orgs = [
                org for org in filtered_orgs 
                if search_term.lower() in org.get('name', '').lower() or 
                   search_term.lower() in org.get('display_name', '').lower()
            ]
        
        st.markdown(f"**Showing {len(filtered_orgs)} of {len(organizations)} organizations**")
        
        # Display organizations
        if filtered_orgs:
            org_df = pd.DataFrame(filtered_orgs)
            
            # Format dates
            if 'created_at' in org_df.columns:
                org_df['created_at'] = pd.to_datetime(org_df['created_at']).dt.strftime('%Y-%m-%d')
            if 'updated_at' in org_df.columns:
                org_df['updated_at'] = pd.to_datetime(org_df['updated_at']).dt.strftime('%Y-%m-%d')
            
            # Select columns to display
            display_cols = [
                'name', 'display_name', 'org_type', 'email', 
                'city', 'state', 'max_teams', 'max_members',
                'is_active', 'created_at'
            ]
            available_cols = [col for col in display_cols if col in org_df.columns]
            
            st.dataframe(
                org_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
            
            # Detailed view of selected organization
            st.markdown("---")
            st.subheader("Organization Details")
            
            org_names = {org['name']: org for org in filtered_orgs}
            selected_org_name = st.selectbox(
                "Select Organization to View Details",
                options=list(org_names.keys())
            )
            
            if selected_org_name:
                selected_org = org_names[selected_org_name]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Basic Information")
                    st.write(f"**Name:** {selected_org.get('name', 'N/A')}")
                    st.write(f"**Display Name:** {selected_org.get('display_name', 'N/A')}")
                    st.write(f"**Type:** {selected_org.get('org_type', 'N/A').title()}")
                    st.write(f"**Status:** {'✅ Active' if selected_org.get('is_active') else '❌ Inactive'}")
                    st.write(f"**Description:** {selected_org.get('description', 'N/A')}")
                    
                    st.markdown("#### Contact Information")
                    st.write(f"**Email:** {selected_org.get('email', 'N/A')}")
                    st.write(f"**Phone:** {selected_org.get('phone', 'N/A')}")
                    st.write(f"**Website:** {selected_org.get('website', 'N/A')}")
                
                with col2:
                    st.markdown("#### Address")
                    address_parts = [
                        selected_org.get('address_line1'),
                        selected_org.get('address_line2'),
                        f"{selected_org.get('city', '')}, {selected_org.get('state', '')} {selected_org.get('postal_code', '')}",
                        selected_org.get('country')
                    ]
                    address = "\n".join([part for part in address_parts if part and part.strip()])
                    st.text(address if address else "No address provided")
                    
                    st.markdown("#### Settings")
                    st.write(f"**Max Teams:** {selected_org.get('max_teams', 'N/A')}")
                    st.write(f"**Max Members:** {selected_org.get('max_members', 'Unlimited')}")
                    
                    st.markdown("#### Timestamps")
                    st.write(f"**Created:** {selected_org.get('created_at', 'N/A')}")
                    st.write(f"**Updated:** {selected_org.get('updated_at', 'N/A')}")
                
                # Show branding if available
                if selected_org.get('logo_url') or selected_org.get('primary_color') or selected_org.get('secondary_color'):
                    st.markdown("#### Branding")
                    brand_col1, brand_col2, brand_col3 = st.columns(3)
                    
                    with brand_col1:
                        if selected_org.get('logo_url'):
                            st.write(f"**Logo:** {selected_org.get('logo_url')}")
                    
                    with brand_col2:
                        if selected_org.get('primary_color'):
                            st.color_picker("Primary Color", value=selected_org.get('primary_color'), disabled=True)
                    
                    with brand_col3:
                        if selected_org.get('secondary_color'):
                            st.color_picker("Secondary Color", value=selected_org.get('secondary_color'), disabled=True)
        else:
            st.info("No organizations match your filters")
    else:
        st.info("No organizations found")

#%% Footer

st.markdown("---")
st.caption(f"Logged in as: {current_user.get('email', 'Unknown')} | Role: Superadmin")

