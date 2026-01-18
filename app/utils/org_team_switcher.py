#%% Organization and Team Switcher Utility
"""
Handles multi-organization and multi-team switching for players and coaches.
Provides sidebar UI for switching between organizations and teams.
"""

import streamlit as st
from typing import Optional, List, Dict, Any

## START ORG REFERENCE ##
def get_user_organizations(supabase, user_id: str, user_email: str) -> List[Dict[str, Any]]:
    """
    Get all organizations a user has access to.
    Combines:
    - Primary organization
    - Organizations from authorized_users table
    - Organizations from organization_ids array
    """
    orgs = []
    org_ids_seen = set()
    
    try:
        # Get from authorized_users (includes role info)
        auth_result = supabase.client.table('authorized_users').select(
            '*, organizations(*)'
        ).eq('email', user_email).eq('is_active', True).execute()
        
        if auth_result.data:
            for entry in auth_result.data:
                org = entry.get('organizations')
                if org and org['id'] not in org_ids_seen:
                    org['user_role_in_org'] = entry.get('assigned_role', 'player')
                    orgs.append(org)
                    org_ids_seen.add(org['id'])
        
        # Also get primary org if not already included
        user_result = supabase.client.table('users').select(
            'primary_organization_id, organization_ids'
        ).eq('id', user_id).single().execute()
        
        if user_result.data:
            primary_org_id = user_result.data.get('primary_organization_id')
            additional_org_ids = user_result.data.get('organization_ids') or []
            
            # Combine all org IDs
            all_org_ids = set()
            if primary_org_id:
                all_org_ids.add(primary_org_id)
            all_org_ids.update(additional_org_ids)
            
            # Fetch any missing orgs
            missing_ids = all_org_ids - org_ids_seen
            if missing_ids:
                for org_id in missing_ids:
                    org_result = supabase.client.table('organizations').select('*').eq('id', org_id).single().execute()
                    if org_result.data:
                        org = org_result.data
                        org['user_role_in_org'] = 'member'  # Default role
                        orgs.append(org)
                        org_ids_seen.add(org_id)
    
    except Exception as e:
        st.error(f"Error fetching organizations: {e}")
    
    return orgs
## END ORG REFERENCE ##

def get_user_teams(supabase, user_id: str, user_email: str, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all teams a user has access to.
    For players: from team_players junction
    For coaches: from team_coaches junction + head_coach_id
    Optionally filtered by organization.
    """
    teams = []
    team_ids_seen = set()
    
    try:
        # Get player profile(s) for this user
        player_result = supabase.client.table('players2').select('id').eq('email', user_email).execute()
        player_ids = [p['id'] for p in (player_result.data or [])]
        
        # Get teams from team_players
        for player_id in player_ids:
            tp_result = supabase.client.table('team_players').select(
                '*, teams(*)'
            ).eq('player_id', player_id).eq('is_active', True).execute()
            
            if tp_result.data:
                for entry in tp_result.data:
                    team = entry.get('teams')
                    if team and team['id'] not in team_ids_seen:
                        if organization_id is None or team.get('organization_id') == organization_id:
                            team['user_role_in_team'] = 'player'
                            team['jersey_number'] = entry.get('jersey_number')
                            teams.append(team)
                            team_ids_seen.add(team['id'])
        
        # Get coach profile(s) for this user
        coach_result = supabase.client.table('coaches').select('id').eq('email', user_email).execute()
        coach_ids = [c['id'] for c in (coach_result.data or [])]
        
        # Also try by user_id
        coach_by_user = supabase.client.table('coaches').select('id').eq('user_id', user_id).execute()
        if coach_by_user.data:
            for c in coach_by_user.data:
                if c['id'] not in coach_ids:
                    coach_ids.append(c['id'])
        
        # Get teams where user is head coach
        for coach_id in coach_ids:
            head_coach_result = supabase.client.table('teams').select('*').eq('head_coach_id', coach_id).execute()
            if head_coach_result.data:
                for team in head_coach_result.data:
                    if team['id'] not in team_ids_seen:
                        if organization_id is None or team.get('organization_id') == organization_id:
                            team['user_role_in_team'] = 'head_coach'
                            teams.append(team)
                            team_ids_seen.add(team['id'])
        
        # Get teams from team_coaches junction
        for coach_id in coach_ids:
            tc_result = supabase.client.table('team_coaches').select(
                '*, teams(*)'
            ).eq('coach_id', coach_id).execute()
            
            if tc_result.data:
                for entry in tc_result.data:
                    team = entry.get('teams')
                    if team and team['id'] not in team_ids_seen:
                        if organization_id is None or team.get('organization_id') == organization_id:
                            team['user_role_in_team'] = entry.get('role', 'assistant_coach')
                            teams.append(team)
                            team_ids_seen.add(team['id'])
        
        # Also check user's team_ids array
        user_result = supabase.client.table('users').select('team_ids').eq('id', user_id).single().execute()
        if user_result.data and user_result.data.get('team_ids'):
            for team_id in user_result.data['team_ids']:
                if team_id not in team_ids_seen:
                    team_result = supabase.client.table('teams').select('*').eq('id', team_id).single().execute()
                    if team_result.data:
                        team = team_result.data
                        if organization_id is None or team.get('organization_id') == organization_id:
                            team['user_role_in_team'] = 'member'
                            teams.append(team)
                            team_ids_seen.add(team_id)
    
    except Exception as e:
        st.error(f"Error fetching teams: {e}")
    
    return teams


def init_org_team_session():
    """Initialize session state for org/team switching"""
    if 'active_organization_id' not in st.session_state:
        st.session_state.active_organization_id = None
    if 'active_organization' not in st.session_state:
        st.session_state.active_organization = None
    if 'active_team_id' not in st.session_state:
        st.session_state.active_team_id = None
    if 'active_team' not in st.session_state:
        st.session_state.active_team = None
    if 'user_organizations' not in st.session_state:
        st.session_state.user_organizations = []
    if 'user_teams' not in st.session_state:
        st.session_state.user_teams = []

## START ORG REFERENCE ##
def render_org_team_switcher(supabase, current_user: Dict[str, Any]):
    """
    Render the organization and team switcher in the sidebar.
    Returns the active organization and team.
    """
    init_org_team_session()
    
    user_id = current_user.get('id')
    user_email = current_user.get('email')
    user_role = current_user.get('role', 'player')
    
    # Get user's organizations
    orgs = get_user_organizations(supabase, user_id, user_email)
    st.session_state.user_organizations = orgs
    
    # If no orgs found, use primary_organization_id
    if not orgs and current_user.get('primary_organization_id'):
        primary_org = supabase.get_organization(current_user['primary_organization_id'])
        if primary_org:
            primary_org['user_role_in_org'] = user_role
            orgs = [primary_org]
            st.session_state.user_organizations = orgs
    
    active_org = None
    active_team = None
    
    # Only show switcher if user has multiple orgs or is a player/coach
    if orgs:
        st.sidebar.markdown("---")
        
        # Organization Switcher
        if len(orgs) > 1:
            st.sidebar.markdown("### 🏢 Organization")
            org_options = {org.get('display_name') or org.get('name', 'Unknown'): org for org in orgs}
            
            # Determine current selection
            current_org_name = None
            if st.session_state.active_organization_id:
                for name, org in org_options.items():
                    if org['id'] == st.session_state.active_organization_id:
                        current_org_name = name
                        break
            
            if current_org_name is None:
                current_org_name = list(org_options.keys())[0]
            
            selected_org_name = st.sidebar.selectbox(
                "Select Organization",
                options=list(org_options.keys()),
                index=list(org_options.keys()).index(current_org_name) if current_org_name in org_options else 0,
                key="org_switcher",
                label_visibility="collapsed"
            )
            
            active_org = org_options[selected_org_name]
            
            # Update session state if changed
            if active_org['id'] != st.session_state.active_organization_id:
                st.session_state.active_organization_id = active_org['id']
                st.session_state.active_organization = active_org
                st.session_state.active_team_id = None  # Reset team when org changes
                st.session_state.active_team = None
                st.rerun()
        else:
            # Single org - just display it
            active_org = orgs[0]
            st.session_state.active_organization_id = active_org['id']
            st.session_state.active_organization = active_org
            st.sidebar.caption(f"🏢 {active_org.get('display_name') or active_org.get('name', 'Organization')}")
        
        # Team Switcher (for players/coaches)
        if user_role in ['player', 'coach', 'admin', 'admin-team']:
            teams = get_user_teams(supabase, user_id, user_email, active_org['id'] if active_org else None)
            st.session_state.user_teams = teams
            
            if teams:
                if len(teams) > 1:
                    st.sidebar.markdown("### ⚾ Team")
                    team_options = {team.get('name', 'Unknown'): team for team in teams}
                    
                    # Determine current selection
                    current_team_name = None
                    if st.session_state.active_team_id:
                        for name, team in team_options.items():
                            if team['id'] == st.session_state.active_team_id:
                                current_team_name = name
                                break
                    
                    if current_team_name is None or current_team_name not in team_options:
                        current_team_name = list(team_options.keys())[0]
                    
                    selected_team_name = st.sidebar.selectbox(
                        "Select Team",
                        options=list(team_options.keys()),
                        index=list(team_options.keys()).index(current_team_name) if current_team_name in team_options else 0,
                        key="team_switcher",
                        label_visibility="collapsed"
                    )
                    
                    active_team = team_options[selected_team_name]
                    
                    # Update session state if changed
                    if active_team['id'] != st.session_state.active_team_id:
                        st.session_state.active_team_id = active_team['id']
                        st.session_state.active_team = active_team
                        st.rerun()
                    
                    # Show role badge
                    role_in_team = active_team.get('user_role_in_team', 'member')
                    st.sidebar.caption(f"📋 Role: {role_in_team.replace('_', ' ').title()}")
                    
                elif len(teams) == 1:
                    # Single team - just display it
                    active_team = teams[0]
                    st.session_state.active_team_id = active_team['id']
                    st.session_state.active_team = active_team
                    st.sidebar.caption(f"⚾ {active_team.get('name', 'Team')}")
                    role_in_team = active_team.get('user_role_in_team', 'member')
                    st.sidebar.caption(f"📋 {role_in_team.replace('_', ' ').title()}")
    
    return active_org, active_team
## END ORG REFERENCE ##

## START ORG REFERENCE ##
def get_active_organization() -> Optional[Dict[str, Any]]:
    """Get the currently active organization from session state"""
    init_org_team_session()
    return st.session_state.active_organization
## END ORG REFERENCE ##

## START ORG REFERENCE ##
def get_active_team() -> Optional[Dict[str, Any]]:
    """Get the currently active team from session state"""
    init_org_team_session()
    return st.session_state.active_team
## END ORG REFERENCE ##

## START ORG REFERENCE ##
def get_active_organization_id() -> Optional[str]:
    """Get the currently active organization ID from session state"""
    init_org_team_session()
    return st.session_state.active_organization_id
## END ORG REFERENCE ##

## START ORG REFERENCE ##
def get_active_team_id() -> Optional[str]:
    """Get the currently active team ID from session state"""
    init_org_team_session()
    return st.session_state.active_team_id
## END ORG REFERENCE ##