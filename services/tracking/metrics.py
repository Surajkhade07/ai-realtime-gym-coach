import time
import streamlit as st
from services.persistence.exercise_repo import add_exercise
from services.config.workout_config import METRICS_FIELDS


def sync_metrics_from_processor(processor) -> None:
    """
    Pull the latest metrics out of VideoProcessorClass and push them into
    st.session_state. Also handles set/rep accounting and DB persistence.
    """
    if processor is None:
        return

    exercise = st.session_state.get("exercise_type")
    if not exercise:
        return

    latest_metrics = processor.get_latest_metrics()
    if not latest_metrics:
        return

    # --- reps ---
    reps = latest_metrics.get("reps")
    try:
        reps = int(reps) if reps is not None else 0
    except (ValueError, TypeError):
        reps = 0
    st.session_state.reps = reps

    # --- exercise-specific fields ---
    for key, default in METRICS_FIELDS.get(exercise, {}).items():
        if key in latest_metrics and latest_metrics[key] is not None:
            st.session_state[key] = latest_metrics[key]
        elif key not in st.session_state:
            st.session_state[key] = default

    # --- set / completion accounting ---
    try:
        reps_per_set = int(st.session_state.get("reps_per_set", 0))
    except (ValueError, TypeError):
        reps_per_set = 0

    try:
        target_set = int(st.session_state.get("target_sets", 0))
    except (ValueError, TypeError):
        target_set = 0

    if reps_per_set > 0 and target_set > 0:
        sets_completed  = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_set
    else:
        sets_completed   = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed  = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    # --- persist newly completed sets to DB ---
    last_saved = st.session_state.get("last_saved_sets_completed", 0)
    if target_set > 0 and reps_per_set > 0 and sets_completed > last_saved:
        newly  = sets_completed - last_saved
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        add_exercise(
            st.session_state.get("user_id", 0),
            exercise,
            newly * reps_per_set,
            newly,
            now_ts - started_at,
        )
        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed
