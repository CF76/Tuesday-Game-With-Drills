import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="5-a-side Team Balancer", layout="wide")

# Use session state database natively (no file saving required for sandboxes)
if "player_db" not in st.session_state:
    st.session_state.player_db = [
        {"name": "Alex", "rank": 5}, {"name": "Ben", "rank": 5},
        {"name": "Charlie", "rank": 4}, {"name": "Daniel", "rank": 3},
        {"name": "Ethan", "rank": 4}, {"name": "Freddie", "rank": 2}
    ]

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
        st.info("Your master roster is currently empty. Go to the 'Edit Master Roster' tab to add players.")
    else:
        # Create a dictionary to hold checkbox values in session state if not present
        if "attendance_check" not in st.session_state:
            st.session_state.attendance_check = {player['name']: False for player in sorted_roster}

        # Handle structural roster updates (if players were added/removed in the other tab)
        for player in sorted_roster:
            if player['name'] not in st.session_state.attendance_check:
                st.session_state.attendance_check[player['name']] = False

        cols = st.columns(4)
        attendance = {}
        
        for idx, player in enumerate(sorted_roster):
            col = cols[idx % 4]
            # Use session state to manage the value dynamically
            is_present = col.checkbox(
                f"{player['name']} (Rank: {player['rank']})", 
                value=st.session_state.attendance_check[player['name']],
                key=f"match_p_{player['name']}"
            )
            # Update the session state dictionary based on current interaction
            st.session_state.attendance_check[player['name']] = is_present
            if is_present:
                attendance[player['name']] = player['rank']
                
        st.divider()
        
        attendees_count = len(attendance)
        st.metric(label="Confirmed Attendees", value=attendees_count)
        
        # Action Buttons Layout
        btn_col1, btn_col2 = st.columns([1, 4])
        
        with btn_col1:
            # Clear Weekly Selection Button
            if st.button("🔄 Clear Weekly Selection", type="secondary"):
                for name in st.session_state.attendance_check:
                    st.session_state.attendance_check[name] = False
                st.rerun()
                
        with btn_col2:
            generate_clicked = st.button("⚡ Generate Balanced Teams", type="primary")

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
            
            # Snake draft logic
            for i, player in enumerate(active_players):
                round_num = i // num_teams
                team_idx = i % num_teams
                if round_num % 2 == 1:
                    team_idx = num_teams - 1 - team_idx
                teams[team_idx].append(player)
                
            # Optimization logic
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

            # Display Results
            st.success(f"Teams generated! Ideal Target Team Score: {dynamic_target:.1f}")
            
            result_cols = st.columns(num_teams)
            whatsapp_text = "⚽ *Weekly 5-a-Side Lineups* ⚽\n\n"
            
            for idx, team in enumerate(teams):
                with result_cols[idx]:
                    score = get_team_score(team)
                    st.markdown(f"### 🎽 Team {idx+1}")
                    st.caption(f"Total Rank
