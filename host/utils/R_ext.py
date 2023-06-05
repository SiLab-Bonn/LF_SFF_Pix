import numpy as np
import matplotlib.pyplot as plt

R = np.linspace(1e3,10*1e6, 1000)
C_ac = 6e-15

factor = 2*np.pi/C_ac

#f = 0.5*1e6
f = 1e5
R = factor/f
print(R/1e9)

