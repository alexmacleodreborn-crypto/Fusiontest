import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import time

# =========================================================
# App configuration
# =========================================================
st.set_page_config(
    page_title="Sandy’s Law – Universal Phase Test",
    layout="wide"
)

st.title("Sandy’s Law — Universal Phase Stability Test")
st.caption("Fusion • Superfluid • Supersolid | Stable-state recorder")

# =========================================================
# Sidebar
# =========================================================
st.sidebar.header("Test Configuration")

system_type = st.sidebar.selectbox(
    "System Type",
    ["Fusion Plasma", "Superfluid", "Supersolid"]
)

step_delay = st.sidebar.slider(
    "Realtime step delay (s)",
    0.1, 1.5, 0.4, 0.1
)

T_hold = st.sidebar.slider(
    "Stable hold time (s)",
    2.0, 20.0, 6.0, 1.0
)

# =========================================================
# Sandy Square
# =========================================================
Z_min, Z_max = 0.30, 0.90
Sigma_min, Sigma_max = 0.15, 0.85

# =========================================================
# Synthetic generators (system-specific)
# =========================================================
def generate_row(t, system):
    if system == "Fusion Plasma":
        return dict(
            Z=0.65 + 0.10*np.sin(t/7),
            Sigma=0.30 + 0.12*np.abs(np.sin(t/4))
        )

    if system == "Superfluid":
        # Phase coherence + vortex onset
        return dict(
            Z=0.80 - 0.18*(t > 35) - 0.05*np.sin(t/10),
            Sigma=0.20 + 0.35*(t > 35) + 0.03*np.cos(t/6)
        )

    if system == "Supersolid":
        # Lattice + coherence competition
        return dict(
            Z=0.70 + 0.12*np.sin(t/12),
            Sigma=0.25 + 0.25*np.abs(np.sin(t/8))
        )

# =========================================================
# State containers
# =========================================================
df = pd.DataFrame(columns=["time", "Z", "Sigma"])
stable_states = []

current_hold = 0.0
in_stable = False
state_start = None

# =========================================================
# UI placeholders
# =========================================================
metrics_box = st.empty()
plot_box = st.empty()
ledger_box = st.empty()

# =========================================================
# Main loop
# =========================================================
for i in range(300):
    t = i * step_delay
    row = generate_row(t, system_type)
    row["time"] = t
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    if len(df) < 5:
        time.sleep(step_delay)
        continue

    # --- Metrics ---
    Z = df["Z"]
    Sigma = df["Sigma"]
    G = (1 - Z) * Sigma

    dZ = np.gradient(Z)
    dS = np.gradient(Sigma)
    PhasePressure = np.abs(dZ)*(1-Z) + np.abs(dS)*Sigma

    # --- Geometry ---
    distances = np.vstack([
        Z - Z_min,
        Z_max - Z,
        Sigma - Sigma_min,
        Sigma_max - Sigma
    ])
    d_min = np.min(distances, axis=0)

    stable_now = (
        (d_min[-1] > 0.05) and
        (PhasePressure.iloc[-1] < np.percentile(PhasePressure, 70))
    )

    # --- Stability latch ---
    if stable_now:
        current_hold += step_delay
        if not in_stable and current_hold >= T_hold:
            in_stable = True
            state_start = t - T_hold
    else:
        if in_stable:
            stable_states.append(dict(
                Z_mean=Z.iloc[-int(T_hold/step_delay):].mean(),
                Sigma_mean=Sigma.iloc[-int(T_hold/step_delay):].mean(),
                Duration=t - state_start
            ))
        in_stable = False
        current_hold = 0.0

    # =====================================================
    # Metrics UI
    # =====================================================
    with metrics_box.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Z", f"{Z.iloc[-1]:.2f}")
        c2.metric("Σ", f"{Sigma.iloc[-1]:.2f}")
        c3.metric("Gate G", f"{G.iloc[-1]:.3f}")
        c4.metric("Phase Pressure", f"{PhasePressure.iloc[-1]:.3f}")

        if stable_now:
            st.success("Stable regime")
        elif d_min[-1] < 0.05:
            st.error("Phase-0 proximity")
        else:
            st.warning("Dynamic / transitional")

    # =====================================================
    # Z–Σ Plot
    # =====================================================
    fig, ax = plt.subplots(figsize=(7,5))
    ax.plot(Z, Sigma, "-o", alpha=0.6)
    ax.scatter(Z.iloc[-1], Sigma.iloc[-1], s=120)

    ax.add_patch(Rectangle(
        (Z_min, Sigma_min),
        Z_max - Z_min,
        Sigma_max - Sigma_min,
        fill=False,
        linewidth=2
    ))

    ax.set_xlim(0,1)
    ax.set_ylim(0,1)
    ax.set_xlabel("Z (Trap Strength)")
    ax.set_ylabel("Σ (Entropy Export)")
    ax.set_title(f"{system_type} — Z–Σ Trajectory")

    plot_box.pyplot(fig)

    # =====================================================
    # Stable state ledger
    # =====================================================
    if stable_states:
        ledger_df = pd.DataFrame(stable_states)
        with ledger_box.container():
            st.subheader("Stable State Ledger")
            st.dataframe(ledger_df)

    time.sleep(step_delay)