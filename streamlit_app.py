import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# App configuration
# -------------------------------
st.set_page_config(
    page_title="Sandy’s Law – Z–Σ Control Map",
    layout="wide"
)

st.title("Sandy’s Law: Z–Σ Control Map Explorer")
st.caption(
    "A control-space diagnostic for stability, confinement, and breakout "
    "based on the Law of Environment-Dependent Evolution."
)

# -------------------------------
# Sidebar controls
# -------------------------------
st.sidebar.header("System Controls")

system_type = st.sidebar.selectbox(
    "System Type",
    [
        "Fusion (Tokamak)",
        "Stellar System",
        "Generic Energy System"
    ]
)

Z = st.sidebar.slider(
    "Trap Strength Z (Confinement Proxy)",
    min_value=0.0,
    max_value=1.0,
    value=0.85,
    step=0.01
)

Sigma = st.sidebar.slider(
    "Entropy Export Σ (Exhaust / Leakage Proxy)",
    min_value=0.0,
    max_value=1.0,
    value=0.30,
    step=0.01
)

# -------------------------------
# Sandy’s Law core quantity
# -------------------------------
G = (1 - Z) * Sigma

# -------------------------------
# Diagnostics panel
# -------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Trap Strength (Z)", f"{Z:.2f}")

with col2:
    st.metric("Entropy Export (Σ)", f"{Sigma:.2f}")

with col3:
    st.metric("Gate Product (1 − Z)Σ", f"{G:.4f}")

# -------------------------------
# Phase interpretation
# -------------------------------
st.subheader("System State Interpretation")

if Z < 0.3:
    phase = "Dead Zone"
    message = (
        "Low confinement. Energy escapes freely. "
        "No sustained structure or gain is possible."
    )
    color = "gray"

elif Z > 0.7 and Sigma < 0.15:
    phase = "Danger Zone (Phase III Risk)"
    message = (
        "High confinement with insufficient entropy export. "
        "Stress accumulation likely. Breakout or disruption imminent."
    )
    color = "red"

else:
    phase = "Safe Zone (Phase II – False Freedom)"
    message = (
        "High confinement with controlled entropy flow. "
        "System remains stable without stress accumulation."
    )
    color = "green"

st.markdown(f"**Current Phase:** `{phase}`")
st.write(message)

# -------------------------------
# Z–Σ Operating Map
# -------------------------------
st.subheader("Z–Σ Operating Map")

fig, ax = plt.subplots(figsize=(8, 6))

# Zone shading
ax.axvspan(0.0, 0.3, alpha=0.1)
ax.axvspan(0.7, 1.0, ymin=0.0, ymax=0.25, alpha=0.1)
ax.axvspan(0.7, 1.0, ymin=0.25, ymax=1.0, alpha=0.1)

# Labels
ax.text(0.15, 0.5, "Dead Zone\n(No Gain)", ha="center", va="center")
ax.text(0.85, 0.12, "Danger Zone\n(Pressure Cooker)", ha="center", va="center")
ax.text(0.85, 0.65, "Safe Zone\n(False Freedom)", ha="center", va="center")

# Plot current state
ax.scatter(Z, Sigma, s=120, zorder=5)

# Gate-product contours
Z_grid = np.linspace(0.01, 0.99, 200)
Sigma_grid = np.linspace(0.01, 0.99, 200)
ZZ, SS = np.meshgrid(Z_grid, Sigma_grid)
G_grid = (1 - ZZ) * SS

contours = ax.contour(
    ZZ, SS, G_grid,
    levels=[0.02, 0.05, 0.1],
    linestyles="dashed"
)
ax.clabel(contours, inline=True, fontsize=8)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("Trap Strength Z (Confinement)")
ax.set_ylabel("Entropy Export Σ")
ax.set_title("Sandy’s Law Z–Σ Operating Space")

st.pyplot(fig)

# -------------------------------
# Optional CSV upload
# -------------------------------
st.subheader("Optional: Load Time-Series Data")

uploaded_file = st.file_uploader(
    "Upload CSV with columns: time, Z_proxy, Sigma_proxy",
    type=["csv"]
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if {"Z_proxy", "Sigma_proxy"}.issubset(df.columns):
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        ax2.plot(df["Z_proxy"], df["Sigma_proxy"], lw=2)
        ax2.set_xlabel("Z proxy")
        ax2.set_ylabel("Σ proxy")
        ax2.set_title("System Trajectory in Z–Σ Space")
        st.pyplot(fig2)
    else:
        st.error("CSV must contain columns: Z_proxy, Sigma_proxy")

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.caption(
    "Sandy’s Law does not replace domain physics. "
    "It explains why control strategies succeed or fail by tracking "
    "the balance between confinement and escape."
)