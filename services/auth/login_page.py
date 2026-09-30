import streamlit as st
from services.persistence.exercise_repo import register_user, verify_user


# ── helpers ──────────────────────────────────────────────────────────────────

def _set_logged_in(user: dict):
    """Persist user info in session state and trigger a full rerun."""
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.rerun()


def _validate_password(password: str) -> list[str]:
    """Return a list of unmet password-strength requirements."""
    issues = []
    if len(password) < 8:
        issues.append("At least 8 characters")
    if not any(c.isupper() for c in password):
        issues.append("At least one uppercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("At least one number")
    return issues


# ── main render functionn ──────────────────────────────────────────────────────

def render_login_page() -> bool:
    """
    Renders the Login / Register page.
    Returns True if the user is already authenticated, False otherwise.
    """
    if st.session_state.get("user_id") is not None:
        return True  # already logged in

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <span style="font-size:3.5rem;">🏋️‍♂️</span>
            <h1 style="margin:0.25rem 0 0.1rem; font-size:2rem;">AI Real-time Gym Coach</h1>
            <p style="color:#888; font-size:0.95rem; margin:0;">
                Your personal AI-powered fitness trainer
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["🔐  Login", "📝  Create Account"])

    # LOGIN TAB

    with login_tab:
        st.markdown("##### Welcome back! Sign in to continue.")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )
            submit = st.form_submit_button("Sign In →", use_container_width=True)

        if submit:
            username = username.strip()
            if not username or not password:
                st.error("⚠️ Please fill in both username and password.")
            else:
                user = verify_user(username, password)
                if user:
                    st.success(f"✅ Welcome back, **{user['username']}**!")
                    _set_logged_in(user)
                else:
                    st.error("❌ Invalid username or password. Please try again.")

    # REGISTER TAB

    with register_tab:
        st.markdown("##### Create a new account to get started.")

        with st.form("register_form", clear_on_submit=True):
            new_username = st.text_input(
                "Choose a Username",
                placeholder="e.g. surajk",
                key="reg_username",
            )
            new_password = st.text_input(
                "Choose a Password",
                type="password",
                placeholder="Min 8 chars, 1 uppercase, 1 number",
                key="reg_password",
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="reg_confirm_password",
            )
            reg_submit = st.form_submit_button("Create Account →", use_container_width=True)

        if reg_submit:
            new_username = new_username.strip()
            errors = []

            if not new_username:
                errors.append("Username cannot be empty.")
            elif len(new_username) < 3:
                errors.append("Username must be at least 3 characters.")

            strength_issues = _validate_password(new_password)
            if strength_issues:
                errors.append("Password must have: " + ", ".join(strength_issues))

            if new_password != confirm_password:
                errors.append("Passwords do not match.")

            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
            else:
                user = register_user(new_username, new_password)
                if user is None:
                    st.error(f"❌ Username **{new_username}** is already taken. Try a different one.")
                else:
                    st.success(f"🎉 Account created! Welcome, **{user['username']}**!")
                    _set_logged_in(user)

    # ── Password strength hint shown below both tabs ──────────────────────────
    st.markdown(
        """
        <div style="text-align:center; color:#666; font-size:0.78rem; margin-top:1.5rem;">
            🔒 Passwords are stored as salted SHA-256 hashes — never in plain text.
        </div>
        """,
        unsafe_allow_html=True,
    )

    return False  # not logged in yet