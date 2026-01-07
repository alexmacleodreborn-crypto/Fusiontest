import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
    "A control-space diagnostic for stability and failure based on the "
    "Law of Environment-Dependent Evolution."
)

# =========================================================
# Sidebar controls
# =========================================================
st.sidebar.header("System Controls")

system_type = st.sidebar.selectbox(
    "System Type",
    [
        "Fusion (Tokamak)",
        "Stellar System",
        "Generic Energy System"
    ]
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
# Sandy’s Law core quantity (manual mode)
# =========================================================
G_manual = (1 - Z_manual) * Sigma_manual

# =========================================================
# Diagnostics panel (manual)
# =========================================================
st.subheader("Current System State (Manual Mode)")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Trap Strength Z", f"{Z_manual:.2f}")
with col2:
    st.metric("Entropy Export Σ", f"{Sigma_manual:.2f}")
with col3:
    st.metric("Gate Product (1 − Z)Σ", f"{G_manual:.4f}")

if Z_manual < 0.3:
    phase = "Dead Zone"
    message = "Low confinement. Energy escapes freely. No sustained structure."
elif Z_manual > 0.7 and Sigma_manual < 0.15:
    phase = "Danger Zone (Phase III Risk)"
    message = (
        "High confinement with insufficient entropy export. "
        "Stress accumulation likely."
    )
else:
    phase = "Safe Zone (Phase II – False Freedom)"
    message = (
        "High confinement with controlled entropy flow. "
        "Stable operation without stress buildup."
    )

st.markdown(f"**Current Phase:** `{phase}`")
st.write(message)

# =========================================================
# Z–Σ Operating Map (base)
# =========================================================
st.subheader("Z–Σ Operating Map")

fig, ax = plt.subplots(figsize=(8, 6))

# Zone shading
ax.axvspan(0.0, 0.3, alpha=0.1)
ax.axvspan(0.7, 1.0, ymin=0.0, ymax=0.25, alpha=0.1)
ax.axvspan(0.7, 1.0, ymin=0.25, ymax=1.0, alpha=0.1)

ax.text(0.15, 0.5, "Dead Zone\n(No Gain)", ha="center", va="center")
ax.text(0.85, 0.12, "Danger Zone\n(Pressure Cooker)", ha="center", va="center")
ax.text(0.85, 0.65, "Safe Zone\n(False Freedom)", ha="center", va="center")

# Gate-product contours
Zg = np.linspace(0.01, 0.99, 200)
Sg = np.linspace(0.01, 0.99, 200)
ZZ, SS = np.meshgrid(Zg, Sg)
Gg = (1 - ZZ) * SS

contours = ax.contour(
    ZZ, SS, Gg,
    levels=[0.02, 0.05, 0.10],
    linestyles="dashed"
)
ax.clabel(contours, inline=True, fontsize=8)

# Manual point
ax.scatter(Z_manual, Sigma_manual, s=120, zorder=5)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("Trap Strength Z (Confinement)")
ax.set_ylabel("Entropy Export Σ")
ax.set_title("Sandy’s Law Z–Σ Operating Space")

st.pyplot(fig)

# =========================================================
# Paste-in Fusion Data Section (Primary Input)
# =========================================================
st.markdown("---")
st.subheader("Paste Fusion Data (Google Sheets / CSV)")

st.markdown(
    """
**Recommended format (Fusion-Native):**