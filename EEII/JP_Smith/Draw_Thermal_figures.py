import os
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# Configuration and File Paths
# -----------------------------------------------------------------------------
INPUT_CSV = 'EEII/JP_Smith/Mag_Thermals.csv'
OUTPUT_PDF = 'EngineeringDesign_Group18_Report/figures/JP_Mag_Thermals.pdf'

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)

# -----------------------------------------------------------------------------
# Load Data
# -----------------------------------------------------------------------------
df = pd.read_csv(INPUT_CSV)
time_min = df['Time'].to_numpy(dtype=float)
temp_c = df['Temperature'].to_numpy(dtype=float)
current_a = df['Current'].to_numpy(dtype=float)

# -----------------------------------------------------------------------------
# Generate Figure
# -----------------------------------------------------------------------------
plt.style.use('default')
fig, ax1 = plt.subplots(figsize=(8.0, 4.8), dpi=300)

# Color scheme
color_temp = '#D62728'  # Crimson red for temperature
color_curr = '#1F77B4'  # Deep blue for current

# Primary axis (Left): Temperature
l1 = ax1.plot(time_min, temp_c, color=color_temp, linewidth=2.2,
              marker='o', markersize=4.5, label='Measured Surface Temperature (°C)')
ax1.set_xlabel('Elapsed Time (min)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Temperature (°C)', color=color_temp, fontsize=11, fontweight='bold')
ax1.tick_params(axis='y', labelcolor=color_temp)
ax1.set_xlim(-0.5, 16.5)
ax1.set_ylim(22, 40)
ax1.grid(True, linestyle='--', alpha=0.55)

# Secondary axis (Right): Coil Current
ax2 = ax1.twinx()
l2 = ax2.plot(time_min, current_a, color=color_curr, linewidth=1.8,
              linestyle='--', marker='s', markersize=4.0, label='Coil Current (1 U-Core @ 4.5 V)')
ax2.set_ylabel('Coil Current (A)', color=color_curr, fontsize=11, fontweight='bold')
ax2.tick_params(axis='y', labelcolor=color_curr)
ax2.set_ylim(2.50, 2.62)

# Combined legend
lines = l1 + l2
labels = [line.get_label() for line in lines]
ax1.legend(lines, labels, loc='lower right', frameon=True, framealpha=0.95,
           facecolor='white', edgecolor='#CCCCCC', fontsize=10)

ax1.set_title('EERI II Electromagnet: Thermal and Current Stability (1 U-Core @ 4.5 V)',
              fontsize=12, fontweight='bold', pad=12)

plt.tight_layout()
plt.savefig(OUTPUT_PDF, format='pdf', bbox_inches='tight')
plt.close(fig)

print(f"Successfully generated thermal figure at: {OUTPUT_PDF}")
