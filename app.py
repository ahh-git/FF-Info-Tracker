import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Import local modules
import db_manager
import ff_api
from streamlit_google_auth import Authenticate

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FireTracker BD",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
    .player-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border-radius: 20px;
        padding: 25px;
        color: white;
        border: 1px solid #FF4B4B;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2);
        margin-top: 20px;
        animation: fadeIn 0.8s;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stat-box {
        background-color: #383838;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin: 5px;
    }
    .stat-value {
        font-size: 1.2rem;
        font-weight: bold;
        color: #FF4B4B;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #b0b0b0;
    }
    .vip-tag {
        background-color: #FFD700;
        color: black;
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- INIT DB ---
db_manager.init_db()

# --- AUTHENTICATION ---
# Check if secrets exist, otherwise use a "Dev Mode" for simple testing
if "google" in st.secrets:
    authenticator = Authenticate(
        secret_credentials_path=None, # Using st.secrets
        cookie_name='firetracker_cookie',
        cookie_key='random_secret_key_signature',
        redirect_uri=st.secrets["google"]["redirect_uri"],
    )
    
    # Verify Login
    authenticator.check_authentification()
    
    if not st.session_state.get('connected'):
        st.title("🔥 FireTracker BD")
        st.write("Please sign in to access the Player Database.")
        authenticator.login()
        st.stop()
        
    # Whitelist Check
    user_email = st.session_state['user_info']['email']
    allowed_emails = st.secrets["general"]["allowed_emails"]
    
    if user_email not in allowed_emails:
        st.error(f"Access Denied: {user_email} is not in the allowlist.")
        if st.button("Logout"):
            authenticator.logout()
        st.stop()
else:
    # FALLBACK FOR DEMO WITHOUT SECRETS
    if "user_info" not in st.session_state:
        st.session_state["user_info"] = {"email": "demo@example.com", "name": "Demo User"}
    user_email = "demo@example.com"
    # st.warning("Running in DEMO mode (No Google Secrets found).")

# --- MAIN APP UI ---
def main():
    st.title("🔥 FireTracker BD")
    st.caption(f"Welcome, {st.session_state['user_info'].get('name', 'Player')}")
    
    # Tabs
    tab1, tab2 = st.tabs(["🔍 Search Player", "📜 History"])
    
    with tab1:
        st.markdown("### Find Player by UID")
        col1, col2 = st.columns([3, 1])
        with col1:
            uid_input = st.text_input("Enter Free Fire UID", placeholder="e.g. 123456789")
        with col2:
            st.write("") # Spacer
            st.write("") 
            search_btn = st.button("Search", type="primary", use_container_width=True)

        if search_btn and uid_input:
            with st.spinner("Fetching data from Garena servers..."):
                data = ff_api.get_player_data(uid_input)
                
                if "error" in data:
                    st.error(data["error"])
                else:
                    # Save to DB
                    db_manager.add_history(user_email, data['uid'], data['nickname'])
                    
                    # RENDER BEAUTIFUL CARD
                    st.markdown(f"""
                    <div class="player-card">
                        <div style="display: flex; align-items: center; margin-bottom: 20px;">
                            <img src="{data['avatar']}" style="width: 80px; height: 80px; border-radius: 50%; border: 2px solid #FF4B4B;">
                            <div style="margin-left: 20px;">
                                <h2 style="margin: 0;">{data['nickname']} 
                                    {'<span class="vip-tag">BOOYAH PASS</span>' if data['booyah_pass'] else ''}
                                </h2>
                                <p style="margin: 5px 0; color: #ccc;">UID: {data['uid']} | Region: {data['region']}</p>
                                <p style="font-style: italic; color: #888;">"{data['bio']}"</p>
                            </div>
                        </div>
                        <hr style="border-color: #444;">
                        <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                            <div class="stat-box" style="flex: 1;">
                                <div class="stat-value">{data['level']}</div>
                                <div class="stat-label">LEVEL</div>
                            </div>
                            <div class="stat-box" style="flex: 1;">
                                <div class="stat-value">{data['rank']}</div>
                                <div class="stat-label">RANK</div>
                            </div>
                            <div class="stat-box" style="flex: 1;">
                                <div class="stat-value">{data['likes']}</div>
                                <div class="stat-label">LIKES</div>
                            </div>
                            <div class="stat-box" style="flex: 1;">
                                <div class="stat-value">{data['rank_points']}</div>
                                <div class="stat-label">POINTS</div>
                            </div>
                        </div>
                        <div style="margin-top: 15px; text-align: center;">
                             <span style="color: #FF4B4B;">Guild:</span> <b>{data['guild']}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.success("Data fetched successfully!")

    with tab2:
        st.markdown("### 🕒 Search History")
        history_df = db_manager.get_user_history(user_email)
        if not history_df.empty:
            st.dataframe(
                history_df, 
                use_container_width=True,
                column_config={
                    "searched_uid": "UID",
                    "player_name": "Nickname",
                    "timestamp": "Time"
                },
                hide_index=True
            )
        else:
            st.info("No search history found.")

    # Footer
    st.markdown("---")
    if st.button("Log out"):
        # For demo mode just rerun, for real auth call logout
        if "google" in st.secrets:
            authenticator.logout()
        else:
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
