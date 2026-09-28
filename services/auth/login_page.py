import streamlit as st
from services.persistence.exercise_repo import get_or_create_user

def render_login_page():
    if st.session_state.get("user_id") is not None:
        return True  # User is already logged in, no need to show login page

    st.title(" 🏋️‍♂️ AI Real-time Gym Trainer")
    st.markdown("### Welcome ! Please enter your UserId to start")

    with st.form("login_form",clear_on_submit=False):
        username=st.text_input("Name (unique)",placeholder="enter unique UserId e.g. surajk")
        submit_button=st.form_submit_button("start session",width="stretch")

    if submit_button:
        if not username.strip():
            st.error("UserId cannot be empty.")
            return False

        user=get_or_create_user(username)  # Get or create the user in the database

        st.session_state["user_id"]=user["id"]
        st.session_state["username"]=user["username"]

        st.rerun()  # Rerun the app to reflect the logged-in state

    return False  # User is not logged in, show login page