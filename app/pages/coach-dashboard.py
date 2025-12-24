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
    get_active_team_id
)

#%% Page Configuration

st.set_page_config(
    page_title="Coach Dashboard",
    page_icon="🧢",
    layout="wide"
)

#%% Authentication & Authorization

auth = get_auth_manager()
require_auth()

current_user = get_current_user()
user_role = current_user.get('role', 'player') if current_user else 'player'

# Check for coach role or higher
allowed_roles = ['coach', 'admin', 'admin-org', 'superadmin']
if user_role not in allowed_roles:
    st.error("🚫 Access Denied: This page is only accessible to coaches and administrators.")
    st.stop()

supabase = get_supabase_client()

# Get the active organization (from switcher) or fall back to primary
user_org_id = get_active_organization_id() or current_user.get('primary_organization_id')
active_team_id = get_active_team_id()

#%% Find Coach Profile

def get_coach_profile():
    """Get the coach profile for the current user - checks by user_id first, then by email"""
    try:
        # First try to find by user_id
        result = supabase.client.table('coaches').select('*').eq('user_id', current_user['id']).execute()
        if result.data:
            return result.data[0]
        
        # If not found by user_id, try to find by email
        user_email = current_user.get('email')
        if user_email:
            email_result = supabase.client.table('coaches').select('*').eq('email', user_email).execute()
            if email_result.data:
                coach = email_result.data[0]
                # Link the coach profile to this user account
                try:
                    supabase.client.table('coaches').update({
                        'user_id': current_user['id']
                    }).eq('id', coach['id']).execute()
                    coach['user_id'] = current_user['id']
                except:
                    pass  # Continue even if update fails
                return coach
        
        # Also check by organization if user has one
        if user_org_id:
            # Look for any coach in this org with matching email
            org_result = supabase.client.table('coaches').select('*').eq('organization_id', user_org_id).eq('email', user_email).execute()
            if org_result.data:
                coach = org_result.data[0]
                # Link the coach profile
                try:
                    supabase.client.table('coaches').update({
                        'user_id': current_user['id']
                    }).eq('id', coach['id']).execute()
                except:
                    pass
                return coach
        
        return None
    except Exception as e:
        st.error(f"Error fetching coach profile: {e}")
        return None

def get_coach_teams(coach_id):
    """Get teams where this coach is assigned (head coach or assistant)"""
    teams = []
    try:
        # Get teams where coach is head coach
        head_coach_result = supabase.client.table('teams').select('*').eq('head_coach_id', coach_id).execute()
        if head_coach_result.data:
            for team in head_coach_result.data:
                team['coach_role'] = 'Head Coach'
                teams.append(team)
        
        # Get teams from team_coaches junction table
        assistant_result = supabase.client.table('team_coaches').select('*, teams(*)').eq('coach_id', coach_id).execute()
        if assistant_result.data:
            for entry in assistant_result.data:
                if entry.get('teams'):
                    team = entry['teams']
                    team['coach_role'] = entry.get('role', 'Assistant').replace('_', ' ').title()
                    # Avoid duplicates
                    if not any(t['id'] == team['id'] for t in teams):
                        teams.append(team)
    except Exception as e:
        st.error(f"Error fetching teams: {e}")
    
    return teams

def get_all_org_teams():
    """Get all teams in the organization (fallback for admins)"""
    try:
        result = supabase.client.table('teams').select('*').eq('organization_id', user_org_id).execute()
        return result.data if result.data else []
    except:
        return []

def get_team_roster(team_id):
    """Get roster for a specific team"""
    try:
        result = supabase.client.table('team_players').select('*, players2(*)').eq('team_id', team_id).execute()
        return result.data if result.data else []
    except:
        return []

def get_org_players():
    """Get all players in the organization"""
    try:
        result = supabase.client.table('players2').select('*').eq('organization_id', user_org_id).execute()
        return result.data if result.data else []
    except:
        return []

#%% Page Title

st.title("🧢 Coach Dashboard")

# Get coach profile
coach_profile = get_coach_profile()

if not coach_profile:
    st.warning("⚠️ No coach profile found for your account.")
    st.info("""
    **Possible reasons:**
    - Your coach profile hasn't been created yet
    - You signed up as a different role
    
    Contact your organization administrator to set up your coach profile.
    """)
    
    # Allow admin-org users to proceed anyway
    if user_role in ['admin-org', 'superadmin']:
        st.info("As an administrator, you can still manage teams from the Org Dashboard.")
    st.stop()

# Display coach info
st.caption(f"👋 Welcome, {coach_profile.get('first_name', '')} {coach_profile.get('last_name', '')}!")
if coach_profile.get('title'):
    st.caption(f"📋 {coach_profile.get('title')}")

st.markdown("---")

#%% Get Coach's Teams

my_teams = get_coach_teams(coach_profile['id'])

# Debug: Show coach profile ID
st.caption(f"🔍 Coach Profile ID: {coach_profile['id'][:8]}...")

if not my_teams:
    st.warning("📋 No direct team assignments found for your coach profile.")
    
    # Check if there are any teams in the organization
    all_org_teams = get_all_org_teams()
    
    if all_org_teams:
        st.info(f"💡 Found **{len(all_org_teams)} team(s)** in your organization. You may need to be assigned as head coach or added to the team_coaches table.")
        
        # For admin-org users, show all teams as a fallback
        if user_role in ['admin-org', 'superadmin', 'admin']:
            st.success("🔓 As an admin, you can manage all organization teams:")
            my_teams = all_org_teams
            for team in my_teams:
                team['coach_role'] = 'Admin Access'
        else:
            st.markdown("**Assign yourself to a team:**")
            
            # Allow coaches to self-assign to teams
            team_options = {t.get('name', 'Unknown'): t['id'] for t in all_org_teams}
            selected_team_name = st.selectbox("Select a team to join:", options=list(team_options.keys()))
            selected_team_id = team_options[selected_team_name]
            
            assign_role = st.selectbox("Your role on this team:", options=['assistant_coach', 'head_coach', 'pitching_coach', 'hitting_coach', 'other'])
            
            if st.button("✅ Assign Myself to Team", type="primary"):
                try:
                    # Add to team_coaches junction table
                    team_coach_entry = {
                        'team_id': selected_team_id,
                        'coach_id': coach_profile['id'],
                        'role': assign_role,
                        'is_primary': assign_role == 'head_coach'
                    }
                    supabase.client.table('team_coaches').insert(team_coach_entry).execute()
                    
                    # If head coach, also update the team's head_coach_id
                    if assign_role == 'head_coach':
                        supabase.client.table('teams').update({
                            'head_coach_id': coach_profile['id']
                        }).eq('id', selected_team_id).execute()
                    
                    st.success(f"✅ You've been assigned to **{selected_team_name}** as {assign_role.replace('_', ' ').title()}!")
                    st.rerun()
                except Exception as e:
                    if 'duplicate' in str(e).lower():
                        st.warning("⚠️ You're already assigned to this team.")
                    else:
                        st.error(f"❌ Error: {str(e)}")
            
            st.markdown("---")
            with st.expander("🔍 Debug: Available teams"):
                for team in all_org_teams:
                    st.write(f"- {team.get('name')} (ID: {team['id'][:8]}...)")
            st.stop()
    else:
        st.info("No teams have been created in your organization yet.")
        st.stop()

#%% Tabs

tab1, tab2, tab3 = st.tabs(["⚾ My Teams", "👥 Manage Rosters", "📧 Invite Players"])

#%% Tab 1: My Teams Overview

with tab1:
    st.subheader("⚾ My Teams")
    
    for team in my_teams:
        with st.expander(f"**{team.get('name', 'Unknown Team')}** - {team.get('coach_role', 'Coach')}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Age Group:** {team.get('age_group', 'N/A')}")
                st.write(f"**Level:** {(team.get('level') or 'N/A').replace('_', ' ').title()}")
            
            with col2:
                st.write(f"**Season:** {team.get('season', 'N/A')}")
                st.write(f"**Your Role:** {team.get('coach_role', 'Coach')}")
            
            with col3:
                roster = get_team_roster(team['id'])
                st.write(f"**Roster Size:** {len(roster)} players")
                st.write(f"**Status:** {'✅ Active' if team.get('is_active', True) else '❌ Inactive'}")
            
            if team.get('description'):
                st.caption(f"📝 {team.get('description')}")

#%% Tab 2: Manage Rosters

with tab2:
    st.subheader("👥 Manage Team Rosters")
    
    # Team selector
    team_options = {f"{t['name']} ({t.get('coach_role', 'Coach')})": t for t in my_teams}
    selected_team_key = st.selectbox("Select Team", options=list(team_options.keys()), key="roster_team_select")
    selected_team = team_options[selected_team_key]
    
    st.markdown("---")
    
    # Get roster
    roster = get_team_roster(selected_team['id'])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### Current Roster: {selected_team['name']}")
        
        if roster:
            roster_data = []
            for entry in roster:
                player = entry.get('players2', {})
                roster_data.append({
                    'Name': f"{player.get('first_name', '')} {player.get('last_name', '')}",
                    'Jersey #': entry.get('jersey_number', 'N/A'),
                    'Position': player.get('primary_position', 'N/A'),
                    'Grad Year': player.get('graduation_year', 'N/A'),
                    'Email': player.get('email', 'N/A'),
                    'player_id': entry.get('player_id'),
                    'roster_id': entry.get('id')
                })
            
            roster_df = pd.DataFrame(roster_data)
            display_df = roster_df[['Name', 'Jersey #', 'Position', 'Grad Year', 'Email']]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(roster)} players")
        else:
            st.info("No players on this roster yet. Add players from the right panel.")
    
    with col2:
        st.markdown("### ➕ Add to Roster")
        
        # Get available players (not already on team)
        all_players = get_org_players()
        roster_player_ids = [r.get('player_id') for r in roster]
        available_players = [p for p in all_players if p['id'] not in roster_player_ids]
        
        if available_players:
            player_options = {f"{p['first_name']} {p['last_name']}": p['id'] for p in available_players}
            selected_player_name = st.selectbox("Select Player", options=list(player_options.keys()), key="add_player_select")
            selected_player_id = player_options[selected_player_name]
            
            jersey_number = st.number_input("Jersey #", min_value=0, max_value=99, value=None, key="jersey_input")
            
            if st.button("➕ Add to Team", type="primary", key="add_player_btn"):
                try:
                    roster_entry = {
                        'team_id': selected_team['id'],
                        'player_id': selected_player_id,
                        'jersey_number': jersey_number if jersey_number else None,
                        'is_active': True
                    }
                    supabase.client.table('team_players').insert(roster_entry).execute()
                    st.success(f"✅ Added {selected_player_name} to the team!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.info("All players are already on this team or no players in organization.")
        
        st.markdown("---")
        
        # Remove player from roster
        if roster:
            st.markdown("### 🗑️ Remove from Roster")
            
            remove_options = {f"{r['players2']['first_name']} {r['players2']['last_name']}": r['id'] for r in roster if r.get('players2')}
            if remove_options:
                remove_player_name = st.selectbox("Select Player to Remove", options=list(remove_options.keys()), key="remove_player_select")
                remove_roster_id = remove_options[remove_player_name]
                
                if st.button("🗑️ Remove from Team", type="secondary", key="remove_player_btn"):
                    try:
                        supabase.client.table('team_players').delete().eq('id', remove_roster_id).execute()
                        st.success(f"✅ Removed {remove_player_name} from the team.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

#%% Tab 3: Invite Players

with tab3:
    st.subheader("📧 Invite New Players")
    st.caption("Invite new players to join your organization. They'll be added to the authorized users list.")
    
    # Team selector for invite
    team_options_invite = {f"{t['name']}": t for t in my_teams}
    selected_team_invite_key = st.selectbox("Select Team for Invitation", options=list(team_options_invite.keys()), key="invite_team_select")
    selected_team_invite = team_options_invite[selected_team_invite_key]
    
    st.markdown("---")
    
    with st.form("invite_player_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            invite_email = st.text_input("Player Email *", placeholder="player@email.com")
            invite_name = st.text_input("Player Name", placeholder="John Doe")
        
        with col2:
            invite_position = st.selectbox(
                "Primary Position",
                options=[None, "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "P", "DH", "UT"]
            )
            invite_grad_year = st.number_input(
                "Graduation Year",
                min_value=2020,
                max_value=2035,
                value=None,
                placeholder="2026"
            )
        
        invite_note = st.text_input("Note (Optional)", placeholder="e.g., Recruited from tryouts")
        
        submit_invite = st.form_submit_button("📧 Send Invitation", use_container_width=True, type="primary")
        
        if submit_invite:
            if not invite_email or '@' not in invite_email:
                st.error("❌ Valid email address is required")
            else:
                # Check if user already exists
                existing_user = supabase.get_user_by_email(invite_email)
                
                if existing_user and existing_user.get('primary_organization_id') == user_org_id:
                    st.warning("⚠️ This user is already in your organization. Add them from the Roster tab.")
                else:
                    # Check if already authorized
                    existing_auth = supabase.check_user_authorized(invite_email, user_org_id)
                    
                    if existing_auth:
                        st.warning("⚠️ This email has already been invited.")
                    else:
                        try:
                            # Add to authorized users
                            auth_result = supabase.add_authorized_user(
                                email=invite_email,
                                organization_id=user_org_id,
                                assigned_role='player',
                                authorized_by=current_user['id'],
                                full_name=invite_name if invite_name else None,
                                authorization_note=f"Invited by coach for {selected_team_invite['name']}. {invite_note}" if invite_note else f"Invited by coach for {selected_team_invite['name']}"
                            )
                            
                            if auth_result:
                                st.success(f"✅ Invitation sent to {invite_email}!")
                                st.info("📧 They will be added to your organization when they sign up.")
                                
                                # Create player profile placeholder
                                if invite_name:
                                    name_parts = invite_name.strip().split(' ', 1)
                                    player_data = {
                                        'organization_id': user_org_id,
                                        'first_name': name_parts[0],
                                        'last_name': name_parts[1] if len(name_parts) > 1 else '',
                                        'email': invite_email,
                                        'primary_position': invite_position,
                                        'graduation_year': invite_grad_year
                                    }
                                    try:
                                        supabase.client.table('players2').insert(player_data).execute()
                                    except:
                                        pass  # Profile will be created on signup
                                
                                st.rerun()
                            else:
                                st.error("❌ Failed to send invitation")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

#%% Footer

st.markdown("---")
st.caption(f"Logged in as: {current_user.get('email', 'Unknown')} | Role: Coach")
