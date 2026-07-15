import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="5-a-side Team Balancer", layout="wide")

# Safe initialization of session state database
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
# SECTION 2: MASTER ROSTER EDITOR
# ==========================================
with app_mode[1]:
    st.subheader("Manage Master Roster & Skill Rankings")
    
    current_roster = st.session_state.player_db
    manage_cols = st.columns([1, 2])
    
    # Left Column: Add New Player Form
    with manage_cols[0]:
        st.markdown("### Add New Player")
        with st.form("admin_add_form", clear_on_submit=True):
            admin_name = st.text_input("Player Name").strip()
            admin_rank = st.slider("Initial Rank", 1, 5, 3)
            submit_add = st.form_submit_button("Add to Roster")
            
            if submit_add and admin_name:
                st.session_state.player_db.append({"name": admin_name, "rank": admin_rank})
                st.success(f"Added {admin_name}!")
                st.rerun()
                
        st.markdown("""
        ### 📊 Skill Index Guide
        * **5 (Elite):** High fitness, dominant player
        * **4 (Strong):** Reliable, good game awareness
        * **3 (Average):** Decent fitness, regular casual
        * **2 (Casual):** Plays occasionally, lower fitness
        * **1 (Beginner):** Minimal football experience
        """)

    # Right Column: Stable Modifier Panel
    with manage_cols[1]:
        st.markdown("### Existing Players Roster")
        
        if len(current_roster) > 0:
            df_display = pd.DataFrame(current_roster).sort_values(by="name")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.divider()
            st.markdown("### Update or Delete a Player")
            
            player_names = [p["name"] for p in sorted(current_roster, key=lambda x: x["name"])]
            selected_player = st.selectbox("Select a player to modify:", player_names, key="select_player_modify")
            
            current_player_data = next(p for p in current_roster if p["name"] == selected_player)
            mod_col1, mod_col2 = st.columns(2)
            
            with mod_col1:
                new_rank = st.selectbox(
                    f"Update rank for {selected_player}:", 
                    [1, 2, 3, 4, 5], 
                    index=int(current_player_data["rank"])-1,
                    key=f"rank_select_{selected_player}"
                )
                if st.button("🔄 Update Rank", key=f"update_btn_{selected_player}"):
                    for p in st.session_state.player_db:
                        if p["name"] == selected_player:
                            p["rank"] = new_rank
                    st.success(f"Updated {selected_player} to Rank {new_rank}!")
                    st.rerun()
                    
            with mod_col2:
                st.write("Danger Zone:")
                if st.button("❌ Delete Player Entirely", type="primary", key=f"del_btn_{selected_player}"):
                    st.session_state.player_db = [p for p in current_roster if p["name"] != selected_player]
                    if "attendance_check" in st.session_state and selected_player in st.session_state.attendance_check:
                        del st.session_state.attendance_check[selected_player]
                    st.warning(f"Removed {selected_player} from roster.")
                    st.rerun()
        else:
            st.info("The master roster is currently empty.")
