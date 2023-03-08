# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
# 
# This script is designed to work with the LF SFF Test Board. For different boards you probably would
# need to change the threshold values, limits,...
# Generally the analyse_bode_plot(...) function expect the y values in dB -> Thresholds
#

import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize

# fit function for the rising and falling edges
def lin_fit(x,a,b):
    return a*x+b

# fit function for the plateau
def const_fit(x,a):
    return x*0+a

IBP_default = -10
IBN_default = 100

def analyse_bode_plot(x,y, title, output_path=None, reset_pulser = True, IBN=IBN_default, IBP=IBP_default):
    try:
        IBP_Gain = np.genfromtxt('./Test_Samples/Reset_Probe/IBP_Gain.csv', delimiter=',')
        IBN_Gain = np.genfromtxt('./Test_Samples/Reset_Probe/IBN_Gain.csv', delimiter=',')
    except:
        print('No Gain measurement found. Please run "python LF_SFF_MIO_RESET_Probe.py ScanVRESET"')
    if (IBN!=IBN_default and IBP==IBP_default):
        G = IBN_Gain[0][0]*IBN+IBN_Gain[0][1]
    elif (IBP!=IBP_default and IBN==IBN_default):
        G = IBP_Gain[0][0]*IBP+IBP_Gain[0][1]
    else:
        G = IBN_Gain[0][0]*IBN+IBN_Gain[0][1]

    y = y/G
    x=np.abs(x)
    plt.figure(figsize=(16,9))
    plt.scatter(x,y)

    ###### find pleateau
    plateau_max = np.max(y)
    threshold = 0.10
    if reset_pulser:
        threshold = 0.30

    plateau = [i for i in range(0, len(y)) if y[i]>plateau_max+plateau_max*threshold]
    popt_plateau, perr_plateau =  optimize.curve_fit(const_fit, x[plateau],y[plateau],[plateau_max])
    x_fit_plateau = np.linspace(0, 100, 2)
    plt.plot(x_fit_plateau,const_fit(x_fit_plateau,popt_plateau), color='black', label='plateau')
    plt.hlines(plateau_max+plateau_max*threshold, 0,10, linestyle='-.', colors='black', label='plateau threshold')
    ###### find rising/falling region
    left = []
    for i in range(0, len(y)):
        if y[i] not in y[plateau]:
            left.append(i)
        else:
            break

    right = [i for i in range(np.max(plateau), len(y))]

    ###### fit linear functions to sides
    skip_corner = 4
    x_fit = np.linspace(0, 100, 3)
    try:
        popt_left, perr_left =  optimize.curve_fit(lin_fit, x[left][:-skip_corner],y[left][:-skip_corner],[0,0])
        plt.plot(x_fit,lin_fit(x_fit,popt_left[0],popt_left[1]), color='red', label='high pass')
    except:
        print('No rising edge found')
    try:
        popt_right, perr_right =  optimize.curve_fit(lin_fit, x[right][skip_corner:],y[right][skip_corner:],[0,0])
        plt.plot(x_fit,lin_fit(x_fit,popt_right[0],popt_right[1]), color='orange',label='low pass')
    except:
        print('No falling edge found')

    ###### find f_hp and f_tp
    f_hp_hz = None
    f_tp_hz = None
    C_in = None
    minus3dB = popt_plateau - 3
    plt.hlines(minus3dB, -10,10, color='gray', label='-3dB')

    try:
        f_hp = (minus3dB-popt_left[1])/popt_left[0]
        plt.vlines(f_hp, 0, -100, linestyles='dashed', colors='black')
        plt.text(f_hp+0.2, minus3dB-4, '$f_{hp}=$'+str(np.round(10**f_hp[0],2))+'Hz')
        f_hp_hz = np.round(10**f_hp[0],2)
    except:
        print('Could not calculate f_hp')

    try:
        f_tp = (minus3dB-popt_right[1])/popt_right[0]
        plt.vlines(f_tp, 0, -100, linestyles='dashed', colors='black')
        plt.text(f_tp-1, minus3dB-4, '$f_{tp}=$'+str(np.round(10**f_tp[0],2))+'Hz')
    except:
        print('Could not calculate f_tp')
        f_tp_hz = np.round(10**f_tp[0],2)

    try:
        C_ac = 6*1e-15
        C_in = C_ac*(1/(np.exp(popt_plateau[0]/10))/G-1)
        plt.text(np.mean(x)-0.5, popt_plateau[0]+2,'$C_{in}=C_{ac}\cdot\\left(\\frac{V_{pp,FreqGen}}{V_{pp,LFSFF}}/G-1\\right)=%.3f fF$'%(C_in*1e15))
        plt.text(f_hp+0.2, minus3dB-6, '$R_{off}=\\frac{2\pi}{f_{hp}\cdot C_{ac}}=$'+str(np.round(2*np.pi/f_hp_hz/C_ac*1e-6,2))+'$M\\Omega$')
    except:
        print('Could not calculate C_in')

    ###### plot everything
    plt.grid()
    plt.xlabel('log10(f)')
    plt.ylabel('$V_{pp}(LF SFF)/V_{pp}(Frequence Generator)/G$ in dB')
    plt.title(title)
    plt.ylim(np.min(y)-1, np.max(y)+5)
    plt.xlim(np.min(x)-1,np.max(x)+1)
    plt.legend()
    if output_path!= None:
        plt.savefig(output_path)
    plt.show()

    return  f_hp_hz, f_tp_hz, C_in


#data=np.genfromtxt("./data/bodeplot/bode.csv", delimiter=',')
#y = data[1:,1]
#x = data[1:,0]

#analyse_bode_plot(x,y, 'Test')