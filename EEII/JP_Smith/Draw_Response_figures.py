import pandas as pd
import numpy
import matplotlib.pyplot as plt

Off = pd.read_csv('EEII/JP_Smith/Plate_OFF_Response.csv')
On = pd.read_csv('EEII/JP_Smith/Plate_ON_Response.csv')

Off_T = Off['TIME'].to_numpy(copy=True).flatten()
Off_V = Off['CH1'].to_numpy(copy=True).flatten()
On_T = On['TIME'].to_numpy(copy=True).flatten()
On_V = On['CH1'].to_numpy(copy=True).flatten()

# filter the data and align the 2 measurements.
# V is the output voltage of a 30A current sense unit.
plt.figure()
plt.plot(Off_T, Off_V)
plt.plot(On_T, On_V)
plt.legend(('Off', 'On'))
plt.savefig('EngineeringDesign_Group18_Report/figures/JP_Magnet_response.pdf', format='pdf')