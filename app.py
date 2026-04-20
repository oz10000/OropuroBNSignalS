import streamlit as st
import core
import storage
from datetime import datetime
import time

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="BN_OroPuro_Signal", layout="centered")

# ---------- AUTO-REFRESH (60 seconds) ----------
st.markdown(
    """
    <meta http-equiv="refresh" content="60">
    """,
    unsafe_allow_html=True
)

# ---------- CUSTOM CSS: BLACK BG, WHITE TEXT, CENTERED ----------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #333333;
        color: white;
        border: 1px solid #555555;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #444444;
        border-color: #888888;
    }
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #FFFFFF !important;
    }
    .css-1v0mbdj, .css-1vbkxwb {
        background-color: #000000;
    }
    .stMarkdown, .stText {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- TITLE ----------
st.markdown("<h1 style='text-align: center;'>BN OroPuro Signal</h1>", unsafe_allow_html=True)

# ---------- RUN SCAN BUTTON ----------
if st.button("🔍 RUN SCAN"):
    with st.spinner("Escaneando mercado... / Scanning market..."):
        result = core.run_scanner()

    st.markdown("---")

    # ----- SIGNAL STATUS -----
    st.markdown("### 📡 SIGNAL STATUS")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Timestamp:** {result.get('timestamp', 'N/A')}")
    with col2:
        status = result.get('status', 'NO SIGNAL')
        color = "#00FF00" if status == "SIGNAL" else "#FFA500"
        st.markdown(f"**Status:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)

    if status == "SIGNAL":
        st.markdown("---")
        st.markdown("### 🚀 CURRENT SIGNAL")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Symbol:** {result.get('symbol', 'N/A')}")
        with col2:
            st.markdown(f"**Direction:** {result.get('direction', 'N/A')}")
        with col3:
            st.markdown(f"**Exchange:** {result.get('exchange', 'N/A')}")
        st.markdown(f"**Score (0‑1):** {result.get('score', 0.0):.3f}")

        # ----- TRADE PARAMETERS -----
        expected_move = result.get('expected_move', 0.0)
        atr = expected_move / 1.2 if expected_move > 0 else 0.0
        suggested_tp = expected_move
        suggested_sl = atr * 1.0

        st.markdown("---")
        st.markdown("### 📊 TRADE PARAMETERS")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Suggested Take Profit:** {suggested_tp:.2f}%")
        with col2:
            st.markdown(f"**Suggested Stop Loss:** {suggested_sl:.2f}%")
        st.markdown(f"**Probability proxy (score):** {result.get('score', 0.0):.3f}")

    # ----- TIME METRICS (from persistent storage) -----
    st.markdown("---")
    st.markdown("### ⏱️ TIME METRICS (persistent)")
    time_since = storage.get_time_since_last_signal()
    est_next = storage.get_estimated_next_signal()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Time since last signal (min):** {time_since:.1f}")
    with col2:
        st.markdown(f"**Estimated time to next signal (min):** {est_next:.1f}")

    # Optionally show last signal info
    last_signal = storage.get_last_signal_time()
    if last_signal:
        st.markdown(f"*Última señal registrada: {last_signal}*")

# ---------- DISCLAIMER (always visible) ----------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 0.8rem;'>
    <p><strong>ES:</strong> Este sistema no es asesoramiento financiero. Es un modelo probabilístico basado en microestructura de mercado. No garantiza resultados. El usuario asume todo el riesgo.</p>
    <p><strong>EN:</strong> This system is not financial advice. It is a probabilistic model based on market microstructure. No results are guaranteed. The user assumes all risk.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- DONATIONS ----------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
    <h4>☕ Donations / Donaciones</h4>
    <p><strong>Alias:</strong> WALYWASABY</p>
    <p><strong>USDT TRC20:</strong> <code>TCiRVXggAqDx6bhJH5KBdf8E4NcJ2voMf8</code></p>
    <p style='font-size: 0.8rem;'><em>ES:</em> Donaciones opcionales. Algunos usuarios destinan una parte de sus ganancias como práctica personal de disciplina.<br>
    <em>EN:</em> Donations are optional. Some users allocate a portion of their gains as a personal discipline practice.</p>
    </div>
    """,
    unsafe_allow_html=True
)
