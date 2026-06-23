import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_oauth import OAuth2Component
from database import init_db, sqlite3, DB_NAME
import json
import base64

# Initialize Database
init_db()

# Pull credentials securely from the Streamlit Cloud Dashboard settings
CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "http://localhost:8501")
AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"

st.set_page_config(page_title="UrbanCompany SKBC Trainer", layout="wide")

# --- LIVE GOOGLE AUTHENTICATION FLOW ---
if "auth" not in st.session_state:
    st.title("🔒 UrbanCompany Agent Portal")
    st.write("Please sign in using your official corporate account to proceed.")
    
    if CLIENT_ID == "":
        st.warning("Google Auth credentials are not set up yet. Please complete the setup in Streamlit Secrets.")
    else:
        oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)
        result = oauth2.authorize_button("Sign in with Google", redirect_uri=REDIRECT_URI, scope="openid email profile")
        
        if result and "token" in result:
            st.session_state["auth"] = result["token"]
            st.rerun()
else:
    # Read the secure token sent back by Google to find the email address
    payload = st.session_state["auth"]["id_token"].split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    user_info = json.loads(base64.b64decode(payload).decode("utf-8"))
    user_email = user_info.get("email", "").strip().lower()

    # Domain Guardrail: Hard block any email that is not UrbanCompany
    if not user_email.endswith("@urbancompany.com"):
        st.error("❌ Access Denied. This system is strictly restricted to @urbancompany.com employee accounts.")
        if st.button("Log Out"):
            del st.session_state["auth"]
            st.rerun()
        st.stop()

    # --- PORTAL INTERFACE ---
    st.sidebar.title("UC SKBC Trainer")
    st.sidebar.write(f"Logged in as: **{user_email}**")
    
    menu = st.sidebar.radio("Go To:", ["Voice Simulator", "My Performance", "Team Leaderboard"])
    
    if st.sidebar.button("Log Out"):
        del st.session_state["auth"]
        st.rerun()

    if menu == "Voice Simulator":
        st.title("🎧 Live Agent Voice Sandbox")
        st.write("Interact with the simulation below. Ensure your microphone permissions are allowed.")
        lyzr_url = "https://studio.lyzr.ai/" # Replace with your deployment widget link
        st.components.v1.iframe(lyzr_url, height=600, scrolling=True)

    elif menu == "My Performance":
        st.title("📈 Performance Trends")
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query(f"SELECT * FROM evaluations WHERE agent_email='{user_email}'", conn)
        conn.close()
        
        if df.empty:
            st.info("No practice data tracked yet. Complete a simulator call to populate graphs!")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Your Average Score", f"{round(df['overall_score'].mean(), 1)}/100")
            col2.metric("Total Calls Practiced", len(df))
            
            fig = px.line(df, x="timestamp", y="overall_score", title="Your Learning Progress Over Time", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "Team Leaderboard":
        st.title("🏆 Top Practicing Agents")
        conn = sqlite3.connect(DB_NAME)
        df_all = pd.read_sql_query("SELECT agent_email, MAX(overall_score) as top_score, COUNT(id) as total_runs FROM evaluations GROUP BY agent_email ORDER BY top_score DESC", conn)
        conn.close()
        
        if df_all.empty:
            st.info("No records in the system yet.")
        else:
            st.dataframe(df_all, use_container_width=True)
