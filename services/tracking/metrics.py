import time
import streamlit as st
from services.persistence.exercise_repo import add_exercise
from services.config.workout_config import METRICS_FIELDS

def sync_metrics_update(context):
    if not context or not hasattr(context,"state") or not context.state.playing:
        return

    processor=getattr(context,"video_processor",None)

    if not processor:
        return

    exercise=st.session_state.get("exercise_type")

    if not exercise:
        return

    processor.set_exercise(exercise)
    latest_metrics=processor.get_latest_metrics()

    if not latest_metrics:
        return

    reps = latest_metrics.get("reps")
    if reps is None:
        reps = st.session_state.get("reps", 0)
    try:
        reps = int(reps) if reps is not None else 0
    except (ValueError, TypeError):
        reps = 0

    st.session_state.reps = reps

    fields = METRICS_FIELDS.get(exercise, {})

    for key, default in fields.items():
        if key in latest_metrics and latest_metrics[key] is not None:
            st.session_state[key] = latest_metrics[key]
        elif key not in st.session_state:
            st.session_state[key] = default

    try:
        reps_per_set = int(st.session_state.get("reps_per_set", 0))
    except (ValueError, TypeError):
        reps_per_set = 0

    try:
        target_set = int(st.session_state.get("target_sets", 0))
    except (ValueError, TypeError):
        target_set = 0

    if reps_per_set > 0 and target_set > 0:
        sets_completed = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_set

    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)

    if target_set > 0 and reps_per_set > 0 and sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        time_taken = now_ts - started_at
        user_id = st.session_state.get("user_id", 0)

        add_exercise(user_id, exercise, newly_completed * reps_per_set, newly_completed, time_taken)

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed 

