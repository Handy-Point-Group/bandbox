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
    get_current_user,
    get_active_organization_id,
    get_active_organization
)

#%% Page Configuration

st.set_page_config(
    page_title="Bandbox - Organization Dashboard",
    page_icon=r"app/images/bandbox.png",
    layout="wide"
)

#%% Authentication & Authorization

auth = get_auth_manager()
require_auth()

current_user = get_current_user()
user_role = current_user.get('role', 'player') if current_user else 'player'

# Check for admin-org role or higher
allowed_roles = ['admin-org', 'superadmin']
if user_role not in allowed_roles:
    st.error("Access Denied: This page is only accessible to Organization Administrators.")
    st.stop()

supabase = get_supabase_client()

# Get the active organization (from switcher) or fall back to primary
user_org_id = get_active_organization_id() or current_user.get('primary_organization_id')
if not user_org_id:
    st.error("No organization assigned. Please contact your administrator.")
    st.stop()

# Fetch organization details (use cached active org if available)
user_org = get_active_organization()
if not user_org:
    user_org = supabase.get_organization(user_org_id)
if not user_org:
    st.error("Organization not found.")
    st.stop()

#%% Page Title

st.title(f"{user_org.get('display_name', user_org.get('name', 'Organization'))} Dashboard")
org_category = user_org.get('org_category', 'competitive')
org_subtype = user_org.get('org_subtype', '')
has_teams = user_org.get('has_teams', True)

if org_category == 'training':
    st.caption(f"Training Organization - {org_subtype.replace('_', ' ').title() if org_subtype else 'N/A'}")
else:
    st.caption(f"Competitive Organization - {org_subtype.replace('_', ' ').title() if org_subtype else 'N/A'}")

st.markdown("---")

#%% Tabs based on organization type

if has_teams:
    tab1, tab2, tab3, tab4 = st.tabs(["Teams", "Players", "Coaches", "Roster Management"])
else:
    tab1, tab2, tab3 = st.tabs(["Players", "Coaches", "Overview"])

#%% Helper Functions

def get_org_teams():
    """Get all teams for this organization"""
    try:
        result = supabase.client.table('teams').select('*').eq('organization_id', user_org_id).execute()
        return result.data if result.data else []
    except:
        return []

def get_org_coaches():
    """Get all coaches for this organization"""
    try:
        result = supabase.client.table('coaches').select('*').eq('organization_id', user_org_id).execute()
        return result.data if result.data else []
    except:
        return []

def get_org_players():
    """Get all players for this organization"""
    try:
        result = supabase.client.table('players2').select('*').eq('organization_id', user_org_id).execute()
        return result.data if result.data else []
    except:
        return []

def get_org_users():
    """Get all users in this organization"""
    try:
        return supabase.get_users_by_organization(user_org_id)
    except:
        return []

#%% Helper: Get team coaches
def get_team_coaches(team_id):
    """Get all coaches assigned to a specific team"""
    try:
        # Get from team_coaches junction table
        result = supabase.client.table('team_coaches').select('*, coaches(*)').eq('team_id', team_id).execute()
        return result.data if result.data else []
    except:
        return []

#%% Teams Tab (only for competitive orgs)

if has_teams:
    with tab1:
        st.subheader("⚾ Team Management")
        
        teams = get_org_teams()
        coaches = get_org_coaches()
        
        # Display existing teams with coach info
        if teams:
            st.markdown("### Current Teams")
            
            for team in teams:
                with st.expander(f"**{team.get('name', 'Unknown')}** - {team.get('age_group', 'N/A')} | {(team.get('level') or 'N/A').replace('_', ' ').title()}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Season:** {team.get('season', 'N/A')}")
                        st.write(f"**Status:** {'Active' if team.get('is_active', True) else 'Inactive'}")
                        
                        # Show head coach
                        head_coach_id = team.get('head_coach_id')
                        head_coach_name = "Not Assigned"
                        if head_coach_id:
                            for c in coaches:
                                if c['id'] == head_coach_id:
                                    head_coach_name = f"{c['first_name']} {c['last_name']}"
                                    break
                        st.write(f"**Head Coach:** {head_coach_name}")
                        
                        # Show assistant coaches
                        team_coach_entries = get_team_coaches(team['id'])
                        if team_coach_entries:
                            assistant_names = []
                            for entry in team_coach_entries:
                                coach_info = entry.get('coaches', {})
                                if coach_info:
                                    role = entry.get('role', 'assistant').replace('_', ' ').title()
                                    assistant_names.append(f"{coach_info.get('first_name', '')} {coach_info.get('last_name', '')} ({role})")
                            if assistant_names:
                                st.write(f"**Staff:** {', '.join(assistant_names)}")
                    
                    with col2:
                        # Quick actions
                        st.markdown("**Quick Actions:**")
                        
                        # Change head coach
                        available_coaches = [c for c in coaches]
                        if available_coaches:
                            coach_options_quick = {"-- Select New Head Coach --": None}
                            coach_options_quick.update({f"{c['first_name']} {c['last_name']}": c['id'] for c in available_coaches})
                            new_head_coach = st.selectbox(
                                "Set Head Coach",
                                options=list(coach_options_quick.keys()),
                                key=f"head_coach_{team['id']}"
                            )
                            
                            if new_head_coach != "-- Select New Head Coach --" and st.button("Set", key=f"set_hc_{team['id']}"):
                                try:
                                    supabase.client.table('teams').update({
                                        'head_coach_id': coach_options_quick[new_head_coach]
                                    }).eq('id', team['id']).execute()
                                    st.success(f"{new_head_coach} is now head coach!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
        else:
            st.info("No teams created yet. Create your first team below!")
        
        st.markdown("---")
        
        # Assign Coach to Team Section
        if teams and coaches:
            st.markdown("### Assign Coach to Team")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Select team
                team_assign_options = {t['name']: t['id'] for t in teams}
                selected_team_for_coach = st.selectbox(
                    "Select Team",
                    options=list(team_assign_options.keys()),
                    key="assign_coach_team"
                )
                selected_team_id_for_coach = team_assign_options[selected_team_for_coach]
            
            with col2:
                # Select coach
                coach_assign_options = {f"{c['first_name']} {c['last_name']}": c['id'] for c in coaches}
                selected_coach_name = st.selectbox(
                    "Select Coach",
                    options=list(coach_assign_options.keys()),
                    key="assign_coach_coach"
                )
                selected_coach_id = coach_assign_options[selected_coach_name]
            
            # Role selection
            coach_role = st.selectbox(
                "Role on Team",
                options=['head_coach', 'assistant_coach', 'pitching_coach', 'hitting_coach', 
                         'catching_coach', 'infield_coach', 'outfield_coach', 'bullpen_coach', 'bench_coach', 'other'],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="assign_coach_role"
            )
            
            if st.button("➕ Assign Coach to Team", type="primary", key="assign_coach_btn"):
                try:
                    if coach_role == 'head_coach':
                        # Update the team's head_coach_id directly
                        supabase.client.table('teams').update({
                            'head_coach_id': selected_coach_id
                        }).eq('id', selected_team_id_for_coach).execute()
                        
                        # Also add to team_coaches for completeness
                        team_coach_entry = {
                            'team_id': selected_team_id_for_coach,
                            'coach_id': selected_coach_id,
                            'role': coach_role,
                            'is_primary': True
                        }
                        try:
                            supabase.client.table('team_coaches').insert(team_coach_entry).execute()
                        except:
                            pass  # Might already exist
                        
                        st.success(f"{selected_coach_name} is now Head Coach of {selected_team_for_coach}!")
                    else:
                        # Add to team_coaches junction table
                        team_coach_entry = {
                            'team_id': selected_team_id_for_coach,
                            'coach_id': selected_coach_id,
                            'role': coach_role,
                            'is_primary': False
                        }
                        supabase.client.table('team_coaches').insert(team_coach_entry).execute()
                        st.success(f"{selected_coach_name} assigned as {coach_role.replace('_', ' ').title()} for {selected_team_for_coach}!")
                    
                    st.rerun()
                except Exception as e:
                    if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                        st.warning("This coach is already assigned to this team.")
                    else:
                        st.error(f"Error: {str(e)}")
        
        st.markdown("---")
        
        # Create new team
        st.markdown("### Create New Team")
        
        with st.form("create_team_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                team_name = st.text_input("Team Name *", placeholder="e.g., 16U National")
                team_age_group = st.selectbox(
                    "Age Group",
                    options=[None, "8U", "9U", "10U", "11U", "12U", "13U", "14U", "15U", "16U", "17U", "18U", 
                             "Freshman", "JV", "Varsity", "College", "Adult"],
                    index=0
                )
            
            with col2:
                team_level = st.selectbox(
                    "Level",
                    options=[None, 'varsity', 'jv', 'freshman', 'travel_a', 'travel_b', 'rec', 'showcase', 'other'],
                    format_func=lambda x: {
                        None: "Select Level",
                        'varsity': 'Varsity',
                        'jv': 'JV',
                        'freshman': 'Freshman',
                        'travel_a': 'Travel A (Elite)',
                        'travel_b': 'Travel B',
                        'rec': 'Recreational',
                        'showcase': 'Showcase',
                        'other': 'Other'
                    }.get(x, x)
                )
                team_season = st.text_input("Season", placeholder="e.g., Spring 2025")
            
            # Head coach selection
            if coaches:
                coach_options = {f"{c['first_name']} {c['last_name']}": c['id'] for c in coaches}
                coach_options = {"Select Head Coach": None, **coach_options}
                selected_coach = st.selectbox("Head Coach", options=list(coach_options.keys()))
                head_coach_id = coach_options[selected_coach]
            else:
                st.info("No coaches added yet. You can assign a head coach later.")
                head_coach_id = None
            
            team_description = st.text_area("Description (Optional)", placeholder="Team description...", height=80)
            
            submit_team = st.form_submit_button("Create Team", use_container_width=True, type="primary")
            
            if submit_team:
                if not team_name:
                    st.error("Team name is required")
                else:
                    team_data = {
                        "organization_id": user_org_id,
                        "name": team_name,
                        "age_group": team_age_group,
                        "level": team_level,
                        "season": team_season if team_season else None,
                        "head_coach_id": head_coach_id,
                        "description": team_description if team_description else None,
                        "is_active": True
                    }
                    
                    try:
                        result = supabase.client.table('teams').insert(team_data).execute()
                        if result.data:
                            st.success(f"Team '{team_name}' created successfully!")
                            
                            # If head coach selected, also add to team_coaches
                            if head_coach_id:
                                try:
                                    team_coach_entry = {
                                        'team_id': result.data[0]['id'],
                                        'coach_id': head_coach_id,
                                        'role': 'head_coach',
                                        'is_primary': True
                                    }
                                    supabase.client.table('team_coaches').insert(team_coach_entry).execute()
                                except:
                                    pass
                            
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Failed to create team")
                    except Exception as e:
                        st.error(f"Error creating team: {str(e)}")

#%% Players Tab

players_tab = tab2 if has_teams else tab1

with players_tab:
    st.subheader("👥 Player Management")
    
    players = get_org_players()
    
    # Display existing players
    if players:
        st.markdown("### Current Players")
        players_df = pd.DataFrame(players)
        players_df['full_name'] = players_df['first_name'] + ' ' + players_df['last_name']
        display_cols = ['full_name', 'email', 'primary_position', 'graduation_year', 'batting_hand', 'throwing_hand']
        available_cols = [col for col in display_cols if col in players_df.columns]
        st.dataframe(players_df[available_cols], use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(players)} players")
    else:
        st.info("No players added yet.")
    
    st.markdown("---")
    
    # Add players section
    st.markdown("### Add Players")
    
    add_method = st.radio(
        "How would you like to add players?",
        options=['invite_new', 'add_existing'],
        format_func=lambda x: {
            'invite_new': 'Invite New Player (send signup invitation)',
            'add_existing': 'Add Existing User (already has an account)'
        }[x],
        horizontal=True
    )
    
    if add_method == 'invite_new':
        st.markdown("#### Invite New Player")
        st.caption("The player will receive an email to sign up and will automatically be added to your organization.")
        
        with st.form("invite_player_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                player_email = st.text_input("Email Address *", placeholder="player@email.com")
                player_name = st.text_input("Full Name", placeholder="John Doe")
            
            with col2:
                player_position = st.selectbox(
                    "Primary Position",
                    options=[None, "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "P", "DH", "UT"]
                )
                player_grad_year = st.number_input(
                    "Graduation Year",
                    min_value=2020,
                    max_value=2035,
                    value=None,
                    placeholder="2026"
                )
            
            invite_note = st.text_input("Note (Optional)", placeholder="e.g., Recruited from tryouts")
            
            submit_invite = st.form_submit_button("📧 Send Invitation", use_container_width=True, type="primary")
            
            if submit_invite:
                if not player_email or '@' not in player_email:
                    st.error("Valid email address is required")
                else:
                    # Check if user already exists
                    existing_user = supabase.get_user_by_email(player_email)
                    
                    if existing_user:
                        # User exists - check if already in org
                        if existing_user.get('primary_organization_id') == user_org_id:
                            st.warning("This user is already in your organization")
                        else:
                            # Add to authorized_users to join this org
                            try:
                                auth_result = supabase.add_authorized_user(
                                    email=player_email,
                                    organization_id=user_org_id,
                                    assigned_role='player',
                                    authorized_by=current_user['id'],
                                    full_name=player_name if player_name else None,
                                    authorization_note=invite_note if invite_note else "Added by org admin"
                                )
                                if auth_result:
                                    st.success(f"{player_email} has been authorized to join your organization!")
                                    st.info("They can now switch to your organization from their account.")
                                else:
                                    st.error("Failed to authorize user")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    else:
                        # New user - add to authorized_users
                        try:
                            # Check if already authorized
                            existing_auth = supabase.check_user_authorized(player_email, user_org_id)
                            if existing_auth:
                                st.warning("This email has already been invited")
                            else:
                                auth_result = supabase.add_authorized_user(
                                    email=player_email,
                                    organization_id=user_org_id,
                                    assigned_role='player',
                                    authorized_by=current_user['id'],
                                    full_name=player_name if player_name else None,
                                    authorization_note=invite_note if invite_note else "Invited player"
                                )
                                if auth_result:
                                    st.success(f"Invitation sent to {player_email}!")
                                    st.info("They will be automatically added when they sign up.")
                                    
                                    # Also create a placeholder player2 record if we have enough info
                                    if player_name:
                                        name_parts = player_name.strip().split(' ', 1)
                                        player_data = {
                                            'organization_id': user_org_id,
                                            'first_name': name_parts[0],
                                            'last_name': name_parts[1] if len(name_parts) > 1 else '',
                                            'email': player_email,
                                            'primary_position': player_position,
                                            'graduation_year': player_grad_year
                                        }
                                        try:
                                            supabase.client.table('players2').insert(player_data).execute()
                                        except:
                                            pass  # Ignore if fails, player profile will be created on signup
                                    
                                    st.rerun()
                                else:
                                    st.error("Failed to send invitation")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    else:  # add_existing
        st.markdown("#### Add Existing User")
        st.caption("Add a user who already has an account in the system.")
        
        # Search for existing users not in this org
        search_email = st.text_input("Search by Email", placeholder="Enter email to search...")
        
        if search_email and len(search_email) > 2:
            found_user = supabase.get_user_by_email(search_email)
            
            if found_user:
                if found_user.get('primary_organization_id') == user_org_id:
                    st.success(f"{found_user.get('full_name', search_email)} is already in your organization!")
                else:
                    st.info(f"Found: **{found_user.get('full_name', 'Unknown')}** ({found_user.get('email')})")
                    
                    if st.button("Add to Organization", type="primary"):
                        try:
                            # Add to authorized_users
                            auth_result = supabase.add_authorized_user(
                                email=found_user['email'],
                                organization_id=user_org_id,
                                assigned_role='player',
                                authorized_by=current_user['id'],
                                full_name=found_user.get('full_name'),
                                authorization_note="Added by org admin"
                            )
                            
                            if auth_result:
                                # Also update user's organization directly if they don't have one
                                if not found_user.get('primary_organization_id'):
                                    supabase.client.table('users').update({
                                        'primary_organization_id': user_org_id
                                    }).eq('id', found_user['id']).execute()
                                    st.success(f"{found_user.get('full_name', search_email)} has been added to your organization!")
                                else:
                                    st.success(f"{found_user.get('full_name', search_email)} has been authorized to join!")
                                    st.info("They can switch to your organization from their account settings.")
                                st.rerun()
                            else:
                                st.error("Failed to add user")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            else:
                st.warning(f"No user found with email: {search_email}")
                st.info("Use 'Invite New Player' to send them a signup invitation.")

#%% Coaches Tab

coaches_tab = tab3 if has_teams else tab2

with coaches_tab:
    st.subheader("Coach Management")
    
    coaches = get_org_coaches()
    
    # Display existing coaches
    if coaches:
        st.markdown("### Current Coaches")
        coaches_df = pd.DataFrame(coaches)
        coaches_df['full_name'] = coaches_df['first_name'] + ' ' + coaches_df['last_name']
        display_cols = ['full_name', 'email', 'title', 'role_type', 'phone']
        available_cols = [col for col in display_cols if col in coaches_df.columns]
        st.dataframe(coaches_df[available_cols], use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(coaches)} coaches")
    else:
        st.info("No coaches added yet.")
    
    st.markdown("---")
    
    # Add coaches section
    st.markdown("### Add Coaches")
    
    coach_add_method = st.radio(
        "How would you like to add a coach?",
        options=['invite_new_coach', 'add_existing_coach'],
        format_func=lambda x: {
            'invite_new_coach': 'Invite New Coach (send signup invitation)',
            'add_existing_coach': 'Add Existing User as Coach'
        }[x],
        horizontal=True,
        key="coach_add_method"
    )
    
    if coach_add_method == 'invite_new_coach':
        st.markdown("#### Invite New Coach")
        
        with st.form("invite_coach_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                coach_email = st.text_input("Email Address *", placeholder="coach@email.com", key="coach_email")
                coach_name = st.text_input("Full Name", placeholder="Coach Smith", key="coach_name")
            
            with col2:
                coach_title = st.text_input("Title", placeholder="e.g., Head Coach", key="coach_title")
                coach_role_type = st.selectbox(
                    "Role",
                    options=[None, "head_coach", "assistant_coach", "pitching_coach", "hitting_coach", 
                             "catching_coach", "infield_coach", "outfield_coach", "strength_coach", "volunteer", "other"],
                    format_func=lambda x: x.replace('_', ' ').title() if x else "Select Role",
                    key="coach_role"
                )
            
            coach_phone = st.text_input("Phone (Optional)", placeholder="+1 (555) 123-4567", key="coach_phone")
            
            submit_coach_invite = st.form_submit_button("📧 Send Coach Invitation", use_container_width=True, type="primary")
            
            if submit_coach_invite:
                if not coach_email or '@' not in coach_email:
                    st.error("Valid email address is required")
                else:
                    # Check if already authorized
                    existing_auth = supabase.check_user_authorized(coach_email, user_org_id)
                    if existing_auth:
                        st.warning("This email has already been invited")
                    else:
                        try:
                            # Add to authorized_users as coach
                            auth_result = supabase.add_authorized_user(
                                email=coach_email,
                                organization_id=user_org_id,
                                assigned_role='coach',
                                authorized_by=current_user['id'],
                                full_name=coach_name if coach_name else None,
                                authorization_note=f"{coach_title}" if coach_title else "Coach"
                            )
                            
                            if auth_result:
                                st.success(f"✅ Coach invitation sent to {coach_email}!")
                                
                                # Create coach profile
                                if coach_name:
                                    name_parts = coach_name.strip().split(' ', 1)
                                    coach_data = {
                                        'organization_id': user_org_id,
                                        'first_name': name_parts[0],
                                        'last_name': name_parts[1] if len(name_parts) > 1 else '',
                                        'email': coach_email,
                                        'title': coach_title if coach_title else None,
                                        'role_type': coach_role_type,
                                        'phone': coach_phone if coach_phone else None
                                    }
                                    try:
                                        supabase.client.table('coaches').insert(coach_data).execute()
                                    except:
                                        pass  # Profile will be created on signup
                                
                                st.rerun()
                            else:
                                st.error("Failed to send invitation")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    else:  # add_existing_coach
        st.markdown("#### Promote Existing User to Coach")
        
        org_users = get_org_users()
        non_coach_users = [u for u in org_users if u.get('role') not in ['coach', 'admin-org', 'superadmin']]
        
        if non_coach_users:
            user_options = {f"{u.get('full_name', 'Unknown')} ({u.get('email')})": u for u in non_coach_users}
            selected_user_key = st.selectbox("Select User", options=list(user_options.keys()))
            selected_user = user_options[selected_user_key]
            
            with st.form("promote_to_coach_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_coach_title = st.text_input("Title", placeholder="e.g., Assistant Coach")
                with col2:
                    new_coach_role = st.selectbox(
                        "Role Type",
                        options=["assistant_coach", "pitching_coach", "hitting_coach", "catching_coach", 
                                 "infield_coach", "outfield_coach", "strength_coach", "volunteer", "other"],
                        format_func=lambda x: x.replace('_', ' ').title()
                    )
                
                if st.form_submit_button("Make Coach", type="primary"):
                    try:
                        # Update user role
                        supabase.update_user_role(selected_user['id'], 'coach')
                        
                        # Create coach profile
                        name_parts = selected_user.get('full_name', '').strip().split(' ', 1)
                        coach_data = {
                            'user_id': selected_user['id'],
                            'organization_id': user_org_id,
                            'first_name': name_parts[0] if name_parts else '',
                            'last_name': name_parts[1] if len(name_parts) > 1 else '',
                            'email': selected_user.get('email'),
                            'title': new_coach_title if new_coach_title else None,
                            'role_type': new_coach_role
                        }
                        supabase.client.table('coaches').insert(coach_data).execute()
                        
                        st.success(f"{selected_user.get('full_name')} is now a coach!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("No users available to promote. All users are already coaches or admins.")

#%% Roster Management Tab (only for competitive orgs with teams)

if has_teams:
    with tab4:
        st.subheader("Roster Management")
        
        teams = get_org_teams()
        players = get_org_players()
        
        if not teams:
            st.warning("Create a team first before managing rosters.")
        elif not players:
            st.warning("Add some players first before building rosters.")
        else:
            # Select team
            team_options = {t['name']: t['id'] for t in teams}
            selected_team_name = st.selectbox("Select Team", options=list(team_options.keys()))
            selected_team_id = team_options[selected_team_name]
            
            # Get current roster
            try:
                roster_result = supabase.client.table('team_players').select('*, players2(*)').eq('team_id', selected_team_id).execute()
                current_roster = roster_result.data if roster_result.data else []
            except:
                current_roster = []
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Current Roster")
                if current_roster:
                    for entry in current_roster:
                        player = entry.get('players2', {})
                        st.write(f"• {player.get('first_name', '')} {player.get('last_name', '')} - #{entry.get('jersey_number', 'N/A')}")
                else:
                    st.info("No players assigned to this team yet.")
            
            with col2:
                st.markdown("### Add to Roster")
                
                # Get players not on this team
                roster_player_ids = [r['player_id'] for r in current_roster]
                available_players = [p for p in players if p['id'] not in roster_player_ids]
                
                if available_players:
                    player_options = {f"{p['first_name']} {p['last_name']}": p['id'] for p in available_players}
                    selected_player_name = st.selectbox("Select Player", options=list(player_options.keys()))
                    selected_player_id = player_options[selected_player_name]
                    
                    jersey_num = st.number_input("Jersey Number", min_value=0, max_value=99, value=None)
                    
                    if st.button("Add to Team", type="primary"):
                        try:
                            roster_entry = {
                                'team_id': selected_team_id,
                                'player_id': selected_player_id,
                                'jersey_number': jersey_num,
                                'is_active': True
                            }
                            supabase.client.table('team_players').insert(roster_entry).execute()
                            st.success(f"Added {selected_player_name} to {selected_team_name}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.info("All players are already on this team.")

#%% Overview Tab (for training orgs)

if not has_teams:
    with tab3:
        st.subheader("Organization Overview")
        
        players = get_org_players()
        coaches = get_org_coaches()
        users = get_org_users()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Players", len(players))
        
        with col2:
            st.metric("Total Coaches", len(coaches))
        
        with col3:
            st.metric("Total Users", len(users))
        
        st.markdown("---")
        st.markdown("### Organization Details")
        st.write(f"**Name:** {user_org.get('name', 'N/A')}")
        st.write(f"**Type:** {org_subtype.replace('_', ' ').title() if org_subtype else 'N/A'}")
        st.write(f"**Email:** {user_org.get('email', 'N/A')}")
        st.write(f"**Phone:** {user_org.get('phone', 'N/A')}")
