import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# Configuration and Constants
# -----------------------------------------------------------------------------
# Current sensor: ACS712-30A (nominal 66 mV/A sensitivity)
ACS712_SENSITIVITY = 0.066  # V / A

# File paths (relative to project root)
OFF_PATH = 'EEII/JP_Smith/Plate_OFF_Response.csv'
ON_PATH = 'EEII/JP_Smith/Plate_ON_Response.csv'
OUTPUT_PDF = 'EngineeringDesign_Group18_Report/figures/JP_Magnet_response.pdf'

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)

# -----------------------------------------------------------------------------
# Load Data
# -----------------------------------------------------------------------------
off_df = pd.read_csv(OFF_PATH)
on_df = pd.read_csv(ON_PATH)

t_off_raw = off_df['TIME'].to_numpy(dtype=float)
v_off_raw = off_df['CH1'].to_numpy(dtype=float)

t_on_raw = on_df['TIME'].to_numpy(dtype=float)
v_on_raw = on_df['CH1'].to_numpy(dtype=float)

# -----------------------------------------------------------------------------
# Zero-Offset Calibration & Current Conversion
# -----------------------------------------------------------------------------
# Determine baseline (zero current offset) from pre-trigger region (t < -0.05 s)
base_off = np.mean(v_off_raw[t_off_raw < -0.05])
base_on = np.mean(v_on_raw[t_on_raw < -0.05])

i_off_raw = (v_off_raw - base_off) / ACS712_SENSITIVITY
i_on_raw = (v_on_raw - base_on) / ACS712_SENSITIVITY

# -----------------------------------------------------------------------------
# Filtering
# -----------------------------------------------------------------------------
# Symmetric moving average filter (21 samples ~ 7 ms at 3.12 kS/s)
# Suppresses high-frequency oscilloscope digitizing noise while preserving transient dynamics
window_size = 21
i_off_filt = pd.Series(i_off_raw).rolling(window_size, center=True).mean().bfill().ffill().to_numpy()
i_on_filt = pd.Series(i_on_raw).rolling(window_size, center=True).mean().bfill().ffill().to_numpy()

# Steady-state currents (averaged over settled interval 0.15 s to 0.30 s)
ss_off = np.mean(i_off_filt[(t_off_raw >= 0.15) & (t_off_raw <= 0.30)])
ss_on = np.mean(i_on_filt[(t_on_raw >= 0.15) & (t_on_raw <= 0.30)])
ss_target = (ss_off + ss_on) / 2.0  # ~2.81 A

# -----------------------------------------------------------------------------
# Alignment to Excitation Trigger / Onset (t = 0 ms)
# -----------------------------------------------------------------------------
def detect_excitation_onset(t, i_filt, i_raw):
    """
    Detects the excitation onset t0 where the current starts rising from the zero baseline.
    Locates the sustained step above noise and traces backward to zero crossing.
    """
    pre_mask = (t < -0.05)
    noise_std = np.std(i_raw[pre_mask])
    threshold = 2.5 * noise_std  # ~0.02-0.03 A

    # Locate sustained departure from baseline
    idx_start = np.where(t > -0.05)[0][0]
    idx_det = None
    for k in range(idx_start, len(t) - 20):
        if np.all(i_filt[k:k+15] > threshold):
            idx_det = k
            break

    # Trace backward to locate the exact zero crossing departure
    for k in range(idx_det, 0, -1):
        if i_filt[k] <= 0.0:
            t0 = t[k] + (0.0 - i_filt[k]) * (t[k+1] - t[k]) / (i_filt[k+1] - i_filt[k])
            return t0

    # Fallback linear extrapolation
    slope, intercept = np.polyfit(t[idx_det:idx_det+10], i_filt[idx_det:idx_det+10], 1)
    return -intercept / slope

t0_off = detect_excitation_onset(t_off_raw, i_off_filt, i_off_raw)
t0_on = detect_excitation_onset(t_on_raw, i_on_filt, i_on_raw)

# Shift and convert time to milliseconds relative to excitation onset
t_off_ms = (t_off_raw - t0_off) * 1000.0
t_on_ms = (t_on_raw - t0_on) * 1000.0

# -----------------------------------------------------------------------------
# Time Constant (tau = 63.2% rise) Determination
# -----------------------------------------------------------------------------
target_off_63 = 0.632 * ss_off
target_on_63 = 0.632 * ss_on

tau_off_ms = t_off_ms[np.where((t_off_ms >= 0) & (i_off_filt >= target_off_63))[0][0]]
tau_on_ms = t_on_ms[np.where((t_on_ms >= 0) & (i_on_filt >= target_on_63))[0][0]]

# -----------------------------------------------------------------------------
# Generate Figure
# -----------------------------------------------------------------------------
plt.style.use('default')
fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=300)

# Color scheme
color_off = '#D62728'       # Crimson red for Plate OFF (unloaded)
color_on = '#1F77B4'        # Deep blue for Plate ON (loaded)

# Plot filtered responses
ax.plot(t_off_ms, i_off_filt, color=color_off, linewidth=2.2,
        label=rf'Plate OFF (Unloaded, $\tau \approx {tau_off_ms:.1f}\ \mathrm{{ms}}$)')
ax.plot(t_on_ms, i_on_filt, color=color_on, linewidth=2.2,
        label=rf'Plate ON (Loaded, $\tau \approx {tau_on_ms:.1f}\ \mathrm{{ms}}$)')

# Steady-state reference line
ax.axhline(ss_target, color='#555555', linestyle='--', linewidth=1.1, alpha=0.85,
           label=rf'Steady-State Current ($I_{{ss}} \approx {ss_target:.2f}\ \mathrm{{A}}$)')

# Zero line and excitation vertical marker
ax.axvline(0, color='#888888', linestyle=':', linewidth=1.0)
ax.axhline(0, color='#888888', linestyle=':', linewidth=1.0)

# Axes limits and labels
ax.set_xlim(-10, 200)
ax.set_ylim(-0.15, 3.20)
ax.set_xlabel('Time After Excitation (ms)', fontsize=11, fontweight='bold')
ax.set_ylabel('Electromagnet Coil Current (A)', fontsize=11, fontweight='bold')
ax.set_title('EERI II Magnetic Load Attachment: Transient Current Step Response',
             fontsize=12, fontweight='bold', pad=12)

# Grid and Legend
ax.grid(True, linestyle='--', alpha=0.55)
ax.legend(loc='lower right', frameon=True, framealpha=0.95, facecolor='white',
          edgecolor='#CCCCCC', fontsize=10)

plt.tight_layout()
plt.savefig(OUTPUT_PDF, format='pdf', bbox_inches='tight')
plt.close(fig)

print(f"Successfully generated response figure at: {OUTPUT_PDF}")
