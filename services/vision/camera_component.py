from pathlib import Path
from typing import Optional
import streamlit.components.v1 as components

# Resolve the path to the HTML component folder
_COMPONENT_DIR = Path(__file__).resolve().parents[2] / "components" / "camera_component"

_camera_func = components.declare_component(
    "camera_stream",
    path=str(_COMPONENT_DIR),
)


def camera_stream(annotated_b64: str = "", key: str = "camera_stream") -> Optional[str]:
    """
    Custom Streamlit component that:
      1. Accesses the user's webcam directly in the browser (no WebRTC P2P needed).
      2. Sends raw JPEG frames (base64 data-URL) to Python via Streamlit's WebSocket.
      3. Displays the annotated frame returned by Python.

    Returns:
        A base64 data-URL string of the latest raw webcam frame, or None.
    """
    return _camera_func(
        annotated=annotated_b64,
        key=key,
        default=None,
    )
