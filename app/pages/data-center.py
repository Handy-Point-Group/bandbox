#%% Imports

import os
import sys
import math
from decimal import Decimal
from datetime import date, time, datetime

import numpy as np
import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

sys.path.append("..")
from utils import (
    get_auth_manager,
    get_supabase_client,
    get_active_organization,
    get_active_team,
)

#%% Page Configuration
st.set_page_config(
    page_title="Bandbox - Data Center",
    page_icon=r"app/images/bandbox.png",
    layout="wide"
)

#%% Authentication Check
auth = get_auth_manager()
supabase_client = get_supabase_client()

if not auth.check_authentication():
    st.error("You must be logged in to access this page.")
    st.stop()

current_user = auth.get_current_user()

# Get active org from switcher, fall back to auth
current_org = get_active_organization() or auth.get_current_organization()
active_team = get_active_team()

# Users can upload data with or without an organization
if not current_org:
    st.info("You can upload your personal training data even without an organization.")

# Show active team context if selected
if active_team:
    st.sidebar.success(f"Viewing: {active_team.get('name', 'Team')}")

#%% Connect to Supabase
db = st.connection("supabase",type=SupabaseConnection)

#%% Data Retrieval

# Function to fetch data from any table
def fetch_table_data(table_name):
    response = db.client.table(table_name).select("*").execute()

    # Supabase v2 client: actual rows are in response.data
    data = response.data
    if not data:
        st.warning(f"No data returned from table '{table_name}'.")
        return pd.DataFrame()

    # Normalize into DataFrame
    df = pd.DataFrame(data)

   # Set index to 'id' if it exists, otherwise 'uuid'
    if 'id' in df.columns:
        df.set_index('id', inplace=True)
    elif 'uuid' in df.columns:
        df.set_index('uuid', inplace=True)
    return df

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
swings = fetch_table_data('swings')
dk_curves = fetch_table_data('dk_curves')
video = fetch_table_data('video')

#%% Data Adjustments

# assign class levels to index of years
classdict = {
        0: "Grad",
        1: "Senior",
        2: "Junior",
        3: "Sophomore",
        4: "Freshman",
        5: "Middle"
}

# create the display version of players
players_show = players.copy()

# assign class year names to each player based on graduation year
def classdef(df):
    class_years = []
    for grad_year in df['grad_year']:
        if isinstance(grad_year, Decimal):
            grad_year = int(grad_year)
        # Calculate difference in years between grad date and today
        years_diff = math.ceil((date(grad_year, 9, 1) - date.today()).days / 365)
        # Cap within 0–5
        if years_diff >= 5:
            years_diff = 5
        elif years_diff < 1:
            years_diff = 0
        # Look up label from classdict
        class_year = classdict.get(years_diff, "Unknown")
        class_years.append(class_year)
    # Assign back to the DataFrame
    df['class'] = class_years

# Run the function on your display DataFrame
classdef(players_show)

# Create Players Full Name Column
players_show['full_name'] = players_show['first_name'] + ' ' + players_show['last_name']

# assign player active status by class
active_classes = ['Freshman','Sophomore','Junior','Senior']
players_show['active'] = players_show['class'].isin(active_classes)

# create currentplayers table
currentplayers = players_show.query('active == True')

# Prepare dropdown options
player_options = players_show['full_name'].to_dict()
pitch_type_options = {
    "Four Seam",
    "Two Seam",
    "Cutter",
    "Changeup",
    "Splitter",
    "Curveball",
    "Slider",
}

#%% .csv Data Dump

st.title("Data Center")
st.subheader("Upload Data Here")
new_file = st.file_uploader("Dump Diamond Kinetics .csv File, or Rapsodo 'pitchinggroup' or 'hittinggroup' File Here",type="csv")

if new_file is not None:
    file_df=pd.read_csv(new_file)
    file_df.replace("-", None, inplace=True)
    file_cols = file_df.columns
    # Determine file type
    if "Pitch ID" in file_cols:
        file_type = "rapsodo_pitching"
    elif "HitID" in file_cols:
        file_type = "rapsodo_hitting"
    elif "user.battingOrientation" in file_cols:
        file_type = "dk_hitting"
        cols = [
            "uuid","created_date","created_datetime","swing_power","max_acceleration",
            "impact_momentum","max_hand_speed","max_barrel_speed","speed_efficiency",
            "trigger_to_impact","attack_angle","hand_cast","distance_in_zone",
            "sensor_time_sec","vertical_angle","barrel_x","barrel_y","barrel_z",
            "exit_velocity","potential_distance","player_id","bat_length"
        ]
        file_df = file_df.copy()
        file_df = file_df.iloc[3:, 15:]
        file_df = file_df.drop(columns=["swing.sensorDateTime"])
        file_df.columns = cols
        file_df.reset_index(drop=True, inplace=True)
    else:
        file_type = None
        st.error("Unrecognized file type.")

    # Standardize Date column if it exists
    if "Date" in file_cols:
        file_df['Date'] = pd.to_datetime(file_df['Date']).dt.strftime('%Y-%m-%d')

    # Upload button
    upload = st.button("Upload Data")
    if upload and file_type:
        if file_type == "rapsodo_pitching":
            pitch_upload = file_df[~file_df['Pitch ID'].isin(rapsodo_pitching['Pitch ID'])]
            if len(pitch_upload) == 0:
                st.success("Rapsodo Pitching Data is Up To Date")
            else:
                pitch_upload = pitch_upload.to_dict(orient="records")
                response = db.table("rapsodo_pitching").insert(pitch_upload).execute()
                st.session_state.form_submitted = True
                st.success("Rapsodo Pitching Data Successfully Uploaded")

        elif file_type == "rapsodo_hitting":
            hit_upload = file_df[~file_df['HitID'].isin(rapsodo_hitting['HitID'])]
            if len(hit_upload) == 0:
                st.success("Rapsodo Hitting Data is Up To Date")
            else:
                hit_upload = hit_upload.to_dict(orient="records")
                response = db.table("rapsodo_hitting").insert(hit_upload).execute()
                st.session_state.form_submitted = True
                st.success("Rapsodo Hitting Data Successfully Uploaded")

        elif file_type == "dk_hitting":
            dk_upload = file_df[~file_df['uuid'].isin(swings.index)]
            if len(dk_upload) == 0:
                st.success("Diamond Kinetics Hitting Data is Up To Date")
            dk_upload = dk_upload.replace({np.nan: None})
            records = dk_upload.to_dict(orient="records")
            response = db.table("swings").insert(records).execute()
            st.session_state.form_submitted = True
            st.success("Diamond Kinetics Data Successfully Uploaded")

#%% Video Upload and Bucket Connection

st.subheader("Upload Video Here")
vid = st.file_uploader("Place Video Here", type=['mp4', 'mov'])
video_submit = None

if vid is None:
    st.write("Please upload a video")
else:
    video_player = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id], index=None)
    video_date = st.date_input("Date", value=date.today())
    video_type = st.selectbox("Video Type", ["Pitcher", "Hitter", "Fielder"], index=None)
    video_speed = st.selectbox("Video Speed", ["Slo-Mo", "Regular"], index=None)
    video_view = st.selectbox("View", ["Pitcher's Mound","Home Plate","Open Side","Closed Side"], index=None)
    video_pitch_type = None
    if video_type == "Pitcher":
        video_pitch_type = st.selectbox("Pitch Type", list(pitch_type_options), index=None)

    video_submit = st.button("Upload Video")

# Check if the user uploaded a video
if video_submit and vid is not None:

    # Convert date
    video_date_str = video_date.isoformat()

    # Base filename
    if video_type == "Pitcher":
        base_name = f"{video_player} - {video_type} - {video_pitch_type} - {video_speed} - {video_view} - {video_date_str}"
    else:
        base_name = f"{video_player} - {video_type} - {video_speed} - {video_view} - {video_date_str}"

    # ---- STEP 1: Generate a unique filename ----
    ext = ".mov"
    file_name = base_name + ext

    bucket = "pitching" if video_type == "Pitcher" else "hitting"

    # Get list of existing files in the bucket
    existing_files = db.client.storage.from_(bucket).list()

    existing_names = [f["name"] for f in existing_files]

    counter = 1
    while file_name in existing_names:
        file_name = f"{base_name}-{counter}{ext}"
        counter += 1

    # ---- STEP 2: Upload ----
    file_bytes = vid.read()

    response = db.client.storage.from_(bucket).upload(
        file_name,
        file_bytes,
        file_options={"contentType": "video/quicktime"}
    )

    video_url = db.client.storage.from_(bucket).get_public_url(file_name)

    # ---- STEP 3: Insert database row ----
    new_video_row = {
        'player_id': video_player,
        'date': video_date_str,
        'type': video_type,
        'view': video_view,
        'speed': video_speed,
        'url': video_url
    }

    if video_type == "Pitcher":
        new_video_row['pitch_type'] = video_pitch_type

    db.client.table("video").insert(new_video_row).execute()

    st.success(f"Uploaded: {file_name}")