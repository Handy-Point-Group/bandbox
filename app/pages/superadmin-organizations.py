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
    st.markdown("Follow the steps below to create a new organization.")
    
    # Step 1: Organization Category
    st.markdown("### Step 1: Organization Category")
    st.caption("Select whether this is a training-focused or competitive organization.")
    
    org_category = st.radio(
        "Category *",
        options=['competitive', 'training'],
        format_func=lambda x: {
            'competitive': '🏆 Competitive - Teams that compete (Travel, High School, College, etc.)',
            'training': '🎯 Training - Facilities, trainers, scouts (no team rosters)'
        }[x],
        horizontal=True,
        help="Competitive organizations have teams and rosters. Training organizations focus on individual development."
    )
    
    # Step 2: Organization Sub-Type based on Category
    st.markdown("### Step 2: Organization Type")
    
    if org_category == 'training':
        st.caption("Training organizations don't have team rosters - they focus on player development.")
        org_subtype = st.selectbox(
            "Type *",
            options=['facility', 'personal_trainer', 'scouting', 'other'],
            format_func=lambda x: {
                'facility': '🏟️ Facility - Training facility, indoor cage, etc.',
                'personal_trainer': '👤 Personal Trainer - Individual coaching/instruction',
                'scouting': '🔍 Scouting - Scouting service or organization',
                'other': '📋 Other Training Organization'
            }[x]
        )
        has_teams = False
        max_teams_default = 0
    else:  # competitive
        st.caption("Competitive organizations have teams that compete in leagues/tournaments.")
        org_subtype = st.selectbox(
            "Type *",
            options=['travel', 'high_school', 'college_d1', 'college_d2', 'college_d3', 'juco', 'summer_league', 'youth', 'independent', 'other'],
            format_func=lambda x: {
                'travel': '🚌 Travel Ball - Club/travel team organization',
                'high_school': '🎓 High School - Varsity, JV, or freshman program',
                'college_d1': '🏛️ College D1 - NCAA Division 1',
                'college_d2': '🏛️ College D2 - NCAA Division 2',
                'college_d3': '🏛️ College D3 - NCAA Division 3',
                'juco': '📚 JUCO - Junior/Community College',
                'summer_league': '☀️ Summer League - Summer collegiate or showcase',
                'youth': '⚾ Youth - Little League, Cal Ripken, etc.',
                'independent': '🎯 Independent - Indy ball or unaffiliated',
                'other': '📋 Other Competitive Organization'
            }[x]
        )
        has_teams = True
        max_teams_default = 1
    
    st.markdown("---")
    
    # Step 3: Organization Information Form
    st.markdown("### Step 3: Organization Information")
    
    with st.form("create_organization_form", clear_on_submit=False):
        # Basic Information
        st.markdown("#### Basic Info")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Organization Name *",
                placeholder="e.g., Boston Baseball Academy",
                help="Internal reference name for the organization"
            )
            
            display_name = st.text_input(
                "Display Name",
                placeholder="e.g., BBA",
                help="Short name shown in app (optional)"
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
        
        description = st.text_area(
            "Description",
            placeholder="Brief description of the organization...",
            height=80
        )
        
        # Address Information
        st.markdown("#### Address")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            address_line1 = st.text_input(
                "Address",
                placeholder="123 Main Street"
            )
            city = st.text_input(
                "City",
                placeholder="Boston"
            )
        
        with col2:
            address_line2 = st.text_input(
                "Address Line 2",
                placeholder="Suite 100 (optional)"
            )
            state = st.text_input(
                "State",
                placeholder="MA"
            )
        
        with col3:
            postal_code = st.text_input(
                "Zip Code",
                placeholder="02101"
            )
            country = st.text_input(
                "Country",
                value="USA"
            )
        
        # Branding
        st.markdown("#### Branding")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            logo_url = st.text_input(
                "Logo URL",
                placeholder="https://example.com/logo.png"
            )
        
        with col2:
            primary_color = st.color_picker(
                "Primary Color",
                value="#1f77b4"
            )
        
        with col3:
            secondary_color = st.color_picker(
                "Secondary Color",
                value="#ff7f0e"
            )
        
        # Settings (only show max_teams for competitive orgs)
        if has_teams:
            st.markdown("#### Settings")
            col1, col2 = st.columns(2)
            with col1:
                max_teams = st.number_input(
                    "Maximum Teams",
                    min_value=1,
                    value=max_teams_default,
                    help="Maximum number of teams in this organization"
                )
            with col2:
                max_members = st.number_input(
                    "Maximum Members",
                    min_value=0,
                    value=0,
                    help="Max members per team (0 = unlimited)"
                )
        else:
            max_teams = 0
            max_members = 0
        
        # Organization Admin (Required)
        st.markdown("---")
        st.markdown("### Step 4: Organization Administrator")
        st.info("✉️ Enter the email of the person who will manage this organization. They'll receive an invitation to sign up.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            admin_email = st.text_input(
                "Admin Email Address *",
                placeholder="admin@organization.com",
                help="Email of the organization administrator"
            )
        
        with col2:
            admin_name = st.text_input(
                "Admin Full Name",
                placeholder="John Doe"
            )
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button(
                "✅ Create Organization & Send Invite",
                use_container_width=True,
                type="primary"
            )
        
        if submit_button:
            # Validate required fields
            errors = []
            if not name:
                errors.append("Organization Name is required")
            if not admin_email or '@' not in admin_email:
                errors.append("Valid Admin Email is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Prepare organization data
                org_data = {
                    "name": name,
                    "display_name": display_name if display_name else name,
                    "description": description if description else None,
                    "org_type": org_subtype if org_subtype in ['facility', 'other'] else 'team',  # Map to existing org_type
                    "org_category": org_category,
                    "org_subtype": org_subtype,
                    "has_teams": has_teams,
                    "email": email if email else None,
                    "phone": phone if phone else None,
                    "address_line1": address_line1 if address_line1 else None,
                    "address_line2": address_line2 if address_line2 else None,
                    "city": city if city else None,
                    "state": state if state else None,
                    "postal_code": postal_code if postal_code else None,
                    "country": country if country else "USA",
                    "is_active": True,
                    "max_teams": max_teams if has_teams else None,
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
                            
                            # Add organization admin to authorized users
                            try:
                                auth_user = supabase.add_authorized_user(
                                    email=admin_email.strip(),
                                    organization_id=created_org['id'],
                                    assigned_role='admin-org',
                                    authorized_by=current_user['id'],
                                    full_name=admin_name.strip() if admin_name else None,
                                    authorization_note=f"Organization Administrator - {org_subtype.replace('_', ' ').title()}"
                                )
                                
                                if auth_user:
                                    st.success(f"✅ Admin '{admin_email}' has been authorized!")
                                    st.info(f"📧 {admin_email} can now sign up at the signup page and will automatically be assigned as organization admin.")
                                else:
                                    st.warning("⚠️ Organization created but failed to authorize admin user.")
                            except Exception as admin_error:
                                st.warning(f"⚠️ Organization created but error authorizing admin: {str(admin_error)}")
                            
                            st.balloons()
                            
                            # Summary
                            st.markdown("---")
                            st.markdown("### ✅ Created Successfully!")
                            summary_col1, summary_col2 = st.columns(2)
                            with summary_col1:
                                st.markdown(f"**Organization:** {name}")
                                st.markdown(f"**Category:** {org_category.title()}")
                                st.markdown(f"**Type:** {org_subtype.replace('_', ' ').title()}")
                            with summary_col2:
                                st.markdown(f"**Admin:** {admin_email}")
                                st.markdown(f"**Has Teams:** {'Yes' if has_teams else 'No'}")
                            
                            with st.expander("📋 View Full Details"):
                                st.json(created_org)
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
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_category = st.selectbox(
                "Filter by Category",
                options=['All', 'competitive', 'training'],
                format_func=lambda x: {
                    'All': 'All Categories',
                    'competitive': '🏆 Competitive',
                    'training': '🎯 Training'
                }.get(x, x)
            )
        
        with col2:
            # Dynamic sub-type options based on category
            if filter_category == 'training':
                subtype_options = ['All', 'facility', 'personal_trainer', 'scouting', 'other']
            elif filter_category == 'competitive':
                subtype_options = ['All', 'travel', 'high_school', 'college_d1', 'college_d2', 'college_d3', 'juco', 'summer_league', 'youth', 'independent', 'other']
            else:
                subtype_options = ['All']
            
            filter_subtype = st.selectbox(
                "Filter by Type",
                options=subtype_options,
                format_func=lambda x: x.replace('_', ' ').title() if x != 'All' else 'All Types'
            )
        
        with col3:
            filter_status = st.selectbox(
                "Filter by Status",
                options=['All', 'Active', 'Inactive']
            )
        
        with col4:
            search_term = st.text_input(
                "Search",
                placeholder="Search by name..."
            )
        
        # Apply filters
        filtered_orgs = organizations
        
        if filter_category != 'All':
            filtered_orgs = [org for org in filtered_orgs if org.get('org_category') == filter_category]
        
        if filter_subtype != 'All':
            filtered_orgs = [org for org in filtered_orgs if org.get('org_subtype') == filter_subtype]
        
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
                'name', 'display_name', 'org_category', 'org_subtype', 
                'city', 'state', 'has_teams', 'is_active', 'created_at'
            ]
            available_cols = [col for col in display_cols if col in org_df.columns]
            
            # Format category and subtype for display
            if 'org_category' in org_df.columns:
                org_df['org_category'] = org_df['org_category'].apply(
                    lambda x: '🏆 Competitive' if x == 'competitive' else ('🎯 Training' if x == 'training' else x)
                )
            if 'org_subtype' in org_df.columns:
                org_df['org_subtype'] = org_df['org_subtype'].apply(
                    lambda x: x.replace('_', ' ').title() if x else 'N/A'
                )
            
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
                    category = selected_org.get('org_category', 'N/A')
                    category_display = '🏆 Competitive' if category == 'competitive' else ('🎯 Training' if category == 'training' else category)
                    st.write(f"**Category:** {category_display}")
                    subtype = selected_org.get('org_subtype', 'N/A')
                    st.write(f"**Type:** {subtype.replace('_', ' ').title() if subtype else 'N/A'}")
                    st.write(f"**Has Teams:** {'Yes' if selected_org.get('has_teams') else 'No'}")
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

