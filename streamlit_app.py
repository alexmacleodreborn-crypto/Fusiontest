import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import time
import io

# =========================================================
# App configuration
# =========================================================
st.set_page_config(
    page_title="Sandy’s Law – Z–Σ Realtime Control Map",
    layout="wide"
)

st.title("Sandy’s Law: Z–Σ Realtime Control Map")
st.caption("Realtime and offline phase-space diagnostics for fusion systems")

# =========================================================
# Sidebar controls
# =========================================================
st.sidebar.header("System Controls")

input_mode = st.sidebar.radio(
    "Input Source",
    ["Upload CSV", "Paste CSV", "Realtime Simulation"]
)

step_delay = st.sidebar.slider(
    "Realtime step delay (seconds)",
    0.1, 2.0, 0.5, 0.1
)

# =========================================================
# Sandy Square definition
# =========================================================
Z_min, Z_max = 0.30, 0.90
Sigma_min, Sigma_max = 0.15, 0.85

# =========================================================
# Helper: compute Sandy metrics
# =========================================================
def compute_metrics(df):
    Z_raw = (
        0.55 * df["H98y2"] +
        0.25 * (1 - df["P_rad"] / df["P_input"]) +
        0.20 * np.exp(-df["f_ELM"] / df["f_ELM"].max())
    )
    Z = (Z_raw - Z_raw.min()) / (Z_raw.max() - Z_raw.min() + 1e-6)

    Sigma_raw = (
        0.50 * (df["P_rad"] / df["P_input"]) +
        0.35 * df["f_ELM"] +
        0.15 * df["DeltaW_ELM"]
    )
    Sigma = (Sigma_raw - Sigma_raw.min()) / (Sigma_raw.max() - Sigma_raw.min() + 1e-6)

    G = (1 - Z) * Sigma

    dZ = np.gradient(Z)
    dS = np.gradient(Sigma)
    PhasePressure = np.abs(dZ) * (1 - Z) + np.abs(dS) * Sigma

    return Z, Sigma, G, PhasePressure

# =========================================================
# Data input
# =========================================================
df_full = None

if input_mode == "Upload CSV":
    st.subheader("Upload Fusion Telemetry (CSV)")
    uploaded = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded:
        df_full = pd.read_csv(uploaded)
    else:
        st.stop()

elif input_mode == "Paste CSV":
    st.subheader("Paste Fusion Telemetry (CSV)")

    st.markdown(
        "**Required columns:** `time, H98y2, P_rad, P_input, f_ELM, DeltaW_ELM`"
    )

    csv_text = st.text_area(
        "Paste CSV data here",
        height=260,
        placeholder=(
            "time,H98y2,P_rad,P_input,f_ELM,DeltaW_ELM\n"
            "0.0,1.05,5.2,25.0,20,0.050\n"
            "0.1,1.07,5.5,25.0,22,0.045\n"
            "0.2,1.10,5.9,25.0,25,0.040\n"
        )
    )

    if csv_text.strip():
        try:
            df_full = pd.read_csv(io.StringIO(csv_text))
        except Exception as e:
            st.error(f"CSV parsing error: {e}")
            st.stop()
    else:
        st.stop()

else:
    st.subheader("Realtime Fusion Telemetry (Simulated)")

    def generate_row(t):
        return {
            "time": t,
            "H98y2": 1.0 + 0.15 * np.sin(t / 6),
            "P_rad": 4.5 + 0.8 * np.sin(t / 4),
            "P_input": 25.0,
            "f_ELM": 15 + 6 * np.abs(np.sin(t / 3)),
            "DeltaW_ELM": 0.04 + 0.01 * np.cos(t / 5)
        }

    df_full = pd.DataFrame(columns=[
        "time", "H98y2", "P_rad", "P_input", "f_ELM", "DeltaW_ELM"
    ])

# =========================================================
# Realtime / playback loop
# =========================================================
placeholder = st.empty()
chart_placeholder = st.empty()

max_steps = len(df_full) if input_mode != "Realtime Simulation" else 500

for i in range(max_steps):

    if input_mode == "Realtime Simulation":
        new_row = generate_row(i * step_delay)
        df_full = pd.concat([df_full, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df_full = df_full.iloc[: i + 1]

    if len(df_full) < 5:
        continue

    Z, Sigma, G, PhasePressure = compute_metrics(df_full)

    distances = np.vstack([
        Z - Z_min,
        Z_max - Z,
        Sigma - Sigma_min,
        Sigma_max - Sigma
    ])
    d_min = np.min(distances, axis=0)

    phase0 = (
        (d_min < 0.04) &
        (PhasePressure > np.percentile(PhasePressure, 90))
    )

    with placeholder.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Z (trap)", f"{Z.iloc[-1]:.2f}")
        c2.metric("Σ (entropy)", f"{Sigma.iloc[-1]:.2f}")
        c3.metric("Gate G", f"{G.iloc[-1]:.3f}")
        c4.metric("Phase Pressure", f"{PhasePressure.iloc[-1]:.3f}")

        if phase0.any():
            st.error("⚠️ PHASE-0 DETECTED — SYSTEM LOSING SAFE DOF")
        else:
            st.success("System stable inside Sandy Square")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(Z, Sigma, marker="o", alpha=0.7)
    ax.add_patch(
        Rectangle(
            (Z_min, Sigma_min),
            Z_max - Z_min,
            Sigma_max - Sigma_min,
            fill=False,
            linewidth=2
        )
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Z (Confinement)")
    ax.set_ylabel("Σ (Entropy Export)")
    ax.set_title("Z–Σ Trajectory")
    chart_placeholder.pyplot(fig)

    time.sleep(step_delay)