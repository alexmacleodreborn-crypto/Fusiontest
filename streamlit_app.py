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
# Z–Σ Operating Map
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
# Paste-in Fusion Data Section (CANONICAL INPUT)
# =========================================================
st.markdown("---")
st.subheader("Paste Fusion Data (CSV / Google Sheets)")

st.markdown(
    "**Required columns:**  \n"
    "`time, H98y2, P_rad, P_input, f_ELM, DeltaW_ELM`  \n\n"
    "**Optional:**  \n"
    "`tau_E` (not required; informational only)"
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

if csv_text.strip() and not use_manual:
    try:
        df = pd.read_csv(io.StringIO(csv_text))

        required_cols = {
            "time", "H98y2", "P_rad", "P_input", "f_ELM", "DeltaW_ELM"
        }

        if not required_cols.issubset(df.columns):
            st.error(
                "Missing required columns: "
                + ", ".join(required_cols - set(df.columns))
            )
        else:
            # -------------------------------------------------
            # Compute Sandy’s Law proxies
            # -------------------------------------------------
            Z_proxy = (df["H98y2"] - df["H98y2"].min()) / (
                df["H98y2"].max() - df["H98y2"].min() + 1e-6
            )

            f_rad = df["P_rad"] / df["P_input"]

            Sigma_raw = (
                0.5 * f_rad
                + 0.4 * df["f_ELM"]
                - 0.3 * df["DeltaW_ELM"]
            )

            Sigma_proxy = (Sigma_raw - Sigma_raw.min()) / (
                Sigma_raw.max() - Sigma_raw.min() + 1e-6
            )

            G_series = (1 - Z_proxy) * Sigma_proxy

            # -------------------------------------------------
            # Trajectory plot
            # -------------------------------------------------
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            ax2.plot(Z_proxy, Sigma_proxy, marker="o", lw=2)
            ax2.set_xlabel("Z proxy (normalized H98y2)")
            ax2.set_ylabel("Σ proxy (normalized entropy export)")
            ax2.set_title("Trajectory in Z–Σ Space")
            st.pyplot(fig2)

            # -------------------------------------------------
            # Gate Product time series
            # -------------------------------------------------
            st.subheader("Gate Product Over Time")
            st.line_chart(G_series)

            st.success(
                "Fusion data successfully parsed and mapped into Sandy’s Law space."
            )

    except Exception as e:
        st.error(f"Error parsing CSV data: {e}")

# =========================================================
# Footer
# =========================================================
st.markdown("---")
st.caption(
    "Sandy’s Law does not replace domain physics. "
    "It explains why control strategies succeed or fail by tracking "
    "the balance between confinement (Z) and escape (Σ)."
)