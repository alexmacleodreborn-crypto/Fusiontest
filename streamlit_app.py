import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import io

# =========================================================
# App configuration
# =========================================================
st.set_page_config(
    page_title="Sandy’s Law – Z–Σ Control Map",
    layout="wide"
)

st.title("Sandy’s Law: Z–Σ Control Map Explorer")
st.caption(
    "A control-space diagnostic and early-warning framework based on the "
    "Law of Environment-Dependent Evolution."
)

# =========================================================
# Sidebar controls
# =========================================================
st.sidebar.header("System Controls")

system_type = st.sidebar.selectbox(
    "System Type",
    ["Fusion (Tokamak)", "Stellar System", "Generic Energy System"]
)

Z_manual = st.sidebar.slider(
    "Manual Trap Strength Z (theory exploration)",
    0.0, 1.0, 0.85, 0.01
)

Sigma_manual = st.sidebar.slider(
    "Manual Entropy Export Σ (theory exploration)",
    0.0, 1.0, 0.30, 0.01
)

use_manual = st.sidebar.checkbox(
    "Use manual Z–Σ (ignore pasted data)",
    value=False
)

# =========================================================
# Sandy Square definition (global)
# =========================================================
Z_min, Z_max = 0.30, 0.90
Sigma_min, Sigma_max = 0.15, 0.85

# =========================================================
# Manual diagnostics
# =========================================================
G_manual = (1 - Z_manual) * Sigma_manual

st.subheader("Current System State (Manual Mode)")

c1, c2, c3 = st.columns(3)
c1.metric("Z", f"{Z_manual:.2f}")
c2.metric("Σ", f"{Sigma_manual:.2f}")
c3.metric("Gate Product", f"{G_manual:.4f}")

# =========================================================
# Z–Σ Operating Map (Manual)
# =========================================================
st.subheader("Z–Σ Operating Map")

fig, ax = plt.subplots(figsize=(8, 6))

# Sandy Square
ax.add_patch(
    Rectangle(
        (Z_min, Sigma_min),
        Z_max - Z_min,
        Sigma_max - Sigma_min,
        fill=False,
        linewidth=2
    )
)

# Gate contours
Zg = np.linspace(0.01, 0.99, 200)
Sg = np.linspace(0.01, 0.99, 200)
ZZ, SS = np.meshgrid(Zg, Sg)
Gg = (1 - ZZ) * SS
ax.contour(ZZ, SS, Gg, levels=[0.02, 0.05, 0.1], linestyles="dashed")

# Manual point
ax.scatter(Z_manual, Sigma_manual, s=120)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("Z (Confinement)")
ax.set_ylabel("Σ (Entropy Export)")
ax.set_title("Sandy Square (Phase II Manifold)")
st.pyplot(fig)

# =========================================================
# Paste-in Fusion Data
# =========================================================
st.markdown("---")
st.subheader("Paste Fusion Data (CSV)")

st.markdown(
    "**Required:** `time, H98y2, P_rad, P_input, f_ELM, DeltaW_ELM`  \n"
    "**Optional:** `tau_E`"
)

csv_text = st.text_area(
    "Paste CSV data here",
    height=220,
    placeholder=(
        "time,H98y2,P_rad,P_input,f_ELM,DeltaW_ELM\n"
        "0.0,1.05,5.2,25.0,20,0.050\n"
        "0.1,1.07,5.5,25.0,22,0.045\n"
        "0.2,1.10,5.9,25.0,25,0.040\n"
    )
)

# =========================================================
# Data processing + Phase-0 detection
# =========================================================
if csv_text.strip() and not use_manual:
    try:
        df = pd.read_csv(io.StringIO(csv_text))

        required = {"time", "H98y2", "P_rad", "P_input", "f_ELM", "DeltaW_ELM"}
        if not required.issubset(df.columns):
            st.error("Missing required columns.")
        else:
            # --- Z and Σ proxies ---
            Z_proxy = (df["H98y2"] - df["H98y2"].min()) / (
                df["H98y2"].max() - df["H98y2"].min() + 1e-6
            )

            f_rad = df["P_rad"] / df["P_input"]
            Sigma_raw = 0.5 * f_rad + 0.4 * df["f_ELM"] - 0.3 * df["DeltaW_ELM"]
            Sigma_proxy = (Sigma_raw - Sigma_raw.min()) / (
                Sigma_raw.max() - Sigma_raw.min() + 1e-6
            )

            G_series = (1 - Z_proxy) * Sigma_proxy

            # =================================================
            # PHASE-0 METRICS
            # =================================================
            distances = np.vstack([
                Z_proxy - Z_min,
                Z_max - Z_proxy,
                Sigma_proxy - Sigma_min,
                Sigma_max - Sigma_proxy
            ])

            d_min = np.min(distances, axis=0)

            # Gate Product slope
            dG_dt = np.gradient(G_series)

            # Thresholds (conservative defaults)
            d_crit = 0.05
            dG_crit = np.percentile(dG_dt, 90)

            # Phase-0 flags
            proximity_flag = d_min < d_crit
            pressure_flag = dG_dt > dG_crit

            phase0_flag = proximity_flag | pressure_flag

            # =================================================
            # Visuals
            # =================================================
            st.subheader("Trajectory in Z–Σ Space (with Sandy Square)")

            fig2, ax2 = plt.subplots(figsize=(8, 6))
            ax2.plot(Z_proxy, Sigma_proxy, marker="o")
            ax2.add_patch(
                Rectangle(
                    (Z_min, Sigma_min),
                    Z_max - Z_min,
                    Sigma_max - Sigma_min,
                    fill=False,
                    linewidth=2
                )
            )
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.set_xlabel("Z proxy")
            ax2.set_ylabel("Σ proxy")
            st.pyplot(fig2)

            st.subheader("Gate Product Over Time")
            st.line_chart(G_series)

            # =================================================
            # Phase-0 Status Panel
            # =================================================
            st.subheader("Phase-0 Early Warning Status")

            if phase0_flag.any():
                st.warning(
                    f"Phase-0 detected in {phase0_flag.sum()} samples. "
                    "System is losing safe degrees of freedom."
                )
            else:
                st.success("No Phase-0 detected. System remains safely inside the Sandy Square.")

            # Metrics
            m1, m2 = st.columns(2)
            m1.metric("Min distance to wall", f"{d_min.min():.3f}")
            m2.metric("Max dG/dt", f"{dG_dt.max():.4f}")

    except Exception as e:
        st.error(f"Error parsing data: {e}")

# =========================================================
# Footer
# =========================================================
st.markdown("---")
st.caption(
    "Phase-0 indicates loss of safe degrees of freedom prior to physical failure. "
    "Sandy’s Law provides early warning through geometry, not prediction."
)