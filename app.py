import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="UrbanCompany SKBC Trainer", layout="wide")

CORRECT_PASSWORD = "UC-TRAINER-2026"

# --- LIVE GOOGLE SHEETS CONNECTION CONFIG ---
def get_google_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    secret_credentials = json.loads(st.secrets["GCP_JSON"])
    creds = Credentials.from_service_account_info(secret_credentials, scopes=scopes)
    client = gspread.authorize(creds)
    # This dynamically searches your Google Drive for the sheet you shared
    return client.open("UC Trainer Database").sheet1

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

    # --- PORTAL INTERFACE SIDEBAR ---
    st.sidebar.title("UC SKBC Trainer")
    st.sidebar.write(f"Logged in as: **{user_email}**")
    
    menu = st.sidebar.radio("Go To:", ["Voice Simulator", "My Performance", "Team Leaderboard"])
    
    if st.sidebar.button("Log Out"):
        del st.session_state["authenticated"]
        del st.session_state["user_email"]
        st.rerun()

    # --- MENU NAVIGATION OPTIONS ---
    if menu == "Voice Simulator":
        st.title("🎧 Live Agent Voice Sandbox")
        st.write("Click the button below to launch your dedicated call simulator interface.")
        
        lyzr_url = "https://studio.lyzr.ai/voice-new-create/6a3a4d1022200aea16a5a7fa?tab=playground"
        st.link_button("🎙️ Start Live Voice Simulation Call", lyzr_url, use_container_width=True)
        st.info("💡 Note: Ensure you allow browser microphone access when the simulation tab opens.")
        
        st.write("---")
        # Direct Logging form so trainers or agents can track scores manually after a simulator run
        st.subheader("📝 Log Simulation Results")
        with st.form("score_form", clear_on_submit=True):
            score = st.slider("Overall Score Achieved:", min_value=0, max_value=100, value=85)
            submit_button = st.form_submit_button("Submit Evaluation Score to Database")
            
            if submit_button:
                try:
                    sheet = get_google_sheet()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([now, user_email, score])
                    st.success("🎯 Score logged successfully! Check your trends on the Performance tab.")
                except Exception as e:
                    st.error(f"Error writing to Google Sheet: {e}")

    elif menu == "My Performance":
        st.title("📈 Performance Trends")
        try:
            sheet = get_google_sheet()
            records = sheet.get_all_records()
            
            if not records:
                st.info("No practice data tracked in the Google Sheet yet. Log a score on the Simulator page to start!")
            else:
                df = pd.DataFrame(records)
                # Filter specifically for the logged-in agent
                df_user = df[df['agent_email'] == user_email]
                
                if df_user.empty:
                    st.info("No practice data tracked for your account yet. Complete a simulator call and save your score!")
                else:
                    col1, col2 = st.columns(2)
                    col1.metric("Your Average Score", f"{round(df_user['overall_score'].mean(), 1)}/100")
                    col2.metric("Total Calls Practiced", len(df_user))
                    
                    fig = px.line(df_user, x="timestamp", y="overall_score", title="Your Learning Progress Over Time", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to fetch cloud records: {e}")

    elif menu == "Team Leaderboard":
        st.title("🏆 Top Practicing Agents")
        try:
            sheet = get_google_sheet()
            records = sheet.get_all_records()
            
            if not records:
                st.info("No history recorded in the cloud database yet.")
            else:
                df = pd.DataFrame(records)
                # Construct aggregate stats for the team leaderboard group
                leaderboard = df.groupby('agent_email').agg(
                    Top_Score=('overall_score', 'max'),
                    Total_Runs=('overall_score', 'count')
                ).reset_index().sort_values(by='Top_Score', ascending=False)
                
                st.dataframe(leaderboard, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load leaderboard metrics: {e}")
