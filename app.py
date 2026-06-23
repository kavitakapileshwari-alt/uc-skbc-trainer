import streamlit as st
import pandas as pd
import plotly.express as px
from database import init_db, sqlite3, DB_NAME

# Initialize Database
init_db()

st.set_page_config(page_title="UrbanCompany SKBC Trainer", layout="wide")

# Hardcoded team password so you never have to deal with settings dashboards
CORRECT_PASSWORD = "UC-TRAINER-2026"

# --- BULLETPROOF LOGIN FLOW ---
if "authenticated" not in st.session_state:
    st.title("🚀 UrbanCompany Agent Portal")
    st.write("Please enter your official corporate email and team password to access the trainer.")
    
    email_input = st.text_input("Corporate Email (@urbancompany.com / @urbanclap.com):").strip().lower()
    password_input = st.text_input("Team Password:", type="password")
    
    if st.button("Log In"):
        if not (email_input.endswith("@urbancompany.com") or email_input.endswith("@urbanclap.com")):
            st.error("❌ Access Denied. You must use an official @urbancompany.com or @urbanclap.com email address.")
        elif password_input != CORRECT_PASSWORD:
            st.error("❌ Incorrect team password. Please check with your team lead.")
        else:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email_input
            st.rerun()
else:
    user_email = st.session_state["user_email"]

    # --- PORTAL INTERFACE ---
    st.sidebar.title("UC SKBC Trainer")
    st.sidebar.write(f"Logged in as: **{user_email}**")
    
    menu = st.sidebar.radio("Go To:", ["Voice Simulator", "My Performance", "Team Leaderboard"])
    
    if st.sidebar.button("Log Out"):
        del st.session_state["authenticated"]
        del st.session_state["user_email"]
        st.rerun()

    if menu == "Voice Simulator":
        st.title("🎧 Live Agent Voice Sandbox")
        st.write("Click the button below to launch your dedicated call simulator interface.")
        
        # Fixed back to your original 24-character ID
        lyzr_url = "https://studio.lyzr.ai/voice-new-create/6a3a4d1022200aea16a5a7fa?tab=playground"
        
        st.link_button("🎙️ Start Live Voice Simulation Call", lyzr_url, use_container_width=True)
        
        st.info("💡 Note: Ensure you allow browser microphone access when the simulation tab opens.")
        
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
