import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="5-a-side Team Balancer", layout="wide")

# --- DATABASE CONNECTION (GOOGLE SHEETS) ---
# Paste your public Google Sheet link here
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/export?format=csv"

@st.cache_data(ttl=60)  # Caches the data for 60 seconds to prevent constant API calls
def load_roster_from_sheets(url):
    try:
        df = pd.read_csv(url)
        # Ensure correct column headers exist
        if "name" in df.columns and "rank" in df.columns:
            return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"Error loading database: {e}")
    
    # Fallback default values if connection fails
    return [
        {"name": "Alex", "rank": 5}, {"name": "Ben", "rank": 5},
        {"name": "Charlie", "rank": 4}, {"name": "Daniel", "rank": 3}
    ]

# Populate database from Google Sheet
if "player_db" not in st.session_state:
    st.session_state.player_db = load_roster_from_sheets(SHEET_URL)

# Main App Navigation
st.title("⚽ 5-a-Side Organizer Workspace")
app_mode = st.tabs(["🗓️ Weekly Match Selection", "📝 Edit Master Roster"])

# ==========================================
# SECTION 1: WEEKLY MATCH SELECTION
# ==========================================
with app_mode[0]:
    st.subheader("Select attending players for this week's match:")
    
    sorted_roster = sorted(st.session_state.player_db, key=lambda x: x["name"])
    
    if not sorted_roster:
        st.info("Your master roster is currently empty.")
    else:
        if "attendance_check" not in st.session_state:
            st.session_state.attendance_check = {player['name']: False for player in sorted_roster}

        for player in sorted_roster:
            if player['name'] not in st.session_state.attendance_check:
                st.session_state.attendance_check[player['name']] = False

        cols = st.columns(4)
        attendance = {}
        
        for idx, player in enumerate(sorted_roster):
            col = cols[idx % 4]
            is_present = col.checkbox(
                f"{player['name']} (Rank: {player['rank']})", 
                value=st.session_state.attendance_check[player['name']],
                key=f"match_p_{player['name']}"
            )
            st.session_state.attendance_check[player['name']] = is_present
            if is_present:
                attendance[player['name']] = player['rank']
                
        st.divider()
        
        attendees_count = len(attendance)
        st.metric(label="Confirmed Attendees", value=attendees_count)
        
        btn_col1, btn_col2 = st.columns([1, 4])
        
        with btn_col1:
            if st.button("🔄 Clear Weekly Selection", key="clear_attendance_btn"):
                for name in st.session_state.attendance_check:
                    st.session_state.attendance_check[name] = False
                st.rerun()
                
        with btn_col2:
            generate_clicked = st.button("⚡ Generate Balanced Teams", type="primary", key="generate_teams_btn")

        if attendees_count < 5 and generate_clicked:
            st.warning("You need at least 5 checked players to balance teams.")
        elif generate_clicked:
            active_players = [{"name": name, "rank": rank} for name, rank in attendance.items()]
            team_size = 5
            num_teams = max(1, round(attendees_count / team_size))
            
            dynamic_target = sum(p["rank"] for p in active_players) / num_teams
            
            random.shuffle(active_players)
            active_players.sort(key=lambda x: x["rank"], reverse=True)
            
            teams = [[] for _ in range(num_teams)]
            
            for i, player in enumerate(active_players):
                round_num = i // num_teams
                team_idx = i % num_teams
                if round_num % 2 == 1:
                    team_idx = num_teams - 1 - team_idx
                teams[team_idx].append(player)
                
            def get_team_score(t):
                return sum(p["rank"] for p in t)
                
            for _ in range(100):
                teams.sort(key=get_team_score)
                weakest = teams[0]
                strongest = teams[-1]
                diff = get_team_score(strongest) - get_team_score(weakest)
                
                if diff <= 1:
                    break
                    
                swapped = False
                for p_strong in strongest:
                    for p_weak in weakest:
                        rank_diff = p_strong["rank"] - p_weak["rank"]
                        if 0 < rank_diff < diff:
                            strongest.remove(p_strong)
                            weakest.remove(p_weak)
                            strongest.append(p_weak)
                            weakest.append(p_strong)
                            swapped = True
                            break
                    if swapped:
                        break
                if not swapped:
                    break

            st.success(f"Teams generated! Ideal Target Team Score: {dynamic_target:.1f}")
            
            result_cols = st.columns(num_teams)
            whatsapp_text = "⚽ *Weekly 5-a-Side Lineups* ⚽\n\n"
            
            for idx, team in enumerate(teams):
                with result_cols[idx]:
                    score = get_team_score(team)
                    st.markdown(f"### 🎽 Team {idx+1}")
                    st.caption(f"Total Rank: **{score}**")
                    
                    team_names = []
                    for p in team:
                        st.write(f"• {p['name']}")
                        team_names.append(p['name'])
                    
                    whatsapp_text += f"*Team {idx+1}:*\n" + "\n".join([f"• {n}" for n in team_names]) + "\n\n"
            
            st.divider()
            st.subheader("📋 Copy Lineups for Chat")
            st.text_area("Copy the block below to paste into WhatsApp/Telegram:", value=whatsapp_text, height=200)

# ==========================================
# SECTION 2: VIEW MASTER ROSTER
# ==========================================
with app_mode[1]:
    st.subheader("Master Roster (Read-Only via Google Sheets)")
    st.write("To add, edit, or delete players permanently, update your master list directly inside your Google Sheet file.")
    
    if st.button("🔄 Sync with Google Sheet Now"):
        st.cache_data.clear()
        st.session_state.player_db = load_roster_from_sheets(SHEET_URL)
        st.rerun()

    st.divider()
    
    if len(st.session_state.player_db) > 0:
        df_display = pd.DataFrame(st.session_state.player_db).sort_values(by="name")
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("The master roster is empty.")
