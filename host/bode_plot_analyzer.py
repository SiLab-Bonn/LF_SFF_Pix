import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize

def lin_fit(x,a,b):
    return a*x+b

def const_fit(x,a):
    return x*0+a

def analyse_bode_plot(x,y, title, output_path=None, reset_pulser = False):
    print(x,y)
    x=np.abs(x)
    plt.figure(figsize=(16,9))
    plt.scatter(x,y)
    #plt.show()
    ###### find pleateau
    threshold = 0.05
    if reset_pulser:
        threshold = 0.5
    plateau_max = np.max(y)
    print(plateau_max)
    plateau = [i for i in range(0, len(y)) if y[i]>plateau_max+plateau_max*threshold]
    print(plateau)
    #plt.scatter(x[plateau], y[plateau], color='black')
    print(x[plateau])
    print(y[plateau])
    popt_plateau, perr_plateau =  optimize.curve_fit(const_fit, x[plateau],y[plateau],[plateau_max])
    x_fit_plateau = np.linspace(0, 100, 2)
    plt.plot(x_fit_plateau,const_fit(x_fit_plateau,popt_plateau), color='black')


    ###### find rising/falling region

    left = []
    for i in range(0, len(y)):
        if y[i] not in y[plateau]:
            left.append(i)
        else:
            break
    #plt.scatter(x[left],y[left], color='green')

    right = [i for i in range(np.max(plateau), len(y))]
    #plt.scatter(x[right], y[right], color='peachpuff')

    ###### fit linear functions to sides
    skip_corner = 4
    x_fit = np.linspace(0, 100, 3)

    popt_left, perr_left =  optimize.curve_fit(lin_fit, x[left][:-skip_corner],y[left][:-skip_corner],[0,0])
    plt.plot(x_fit,lin_fit(x_fit,popt_left[0],popt_left[1]), color='red')

    popt_right, perr_right =  optimize.curve_fit(lin_fit, x[right][skip_corner:],y[right][skip_corner:],[0,0])
    plt.plot(x_fit,lin_fit(x_fit,popt_right[0],popt_right[1]), color='orange')

    ###### find f_hp and f_tp
    minus3dB = popt_plateau - 3
    plt.hlines(minus3dB, -10,10, color='black')
    f_hp = (minus3dB-popt_left[1])/popt_left[0]
    f_tp = (minus3dB-popt_right[1])/popt_right[0]

    plt.vlines(f_hp, 0, -30, linestyles='dashed', colors='black')
    plt.vlines(f_tp, 0, -30, linestyles='dashed', colors='black')
    plt.text(f_hp+0.05, minus3dB-3, '$f_{hp}=$'+str(np.round(10**f_hp[0],2))+'Hz')
    plt.text(f_tp-0.8, minus3dB-3, '$f_{tp}=$'+str(np.round(10**f_tp[0],2))+'Hz')
    
    f_hp_hz = np.round(10**f_hp[0],2)
    f_tp_hz = np.round(10**f_tp[0],2)
  
    C_ac = 6*1e-15
    plt.text(f_hp+0.05, minus3dB-3.5, '$R_{off}=\\frac{2\pi}{f_{hp}\cdot C_{ac}}=$'+str(np.round(2*np.pi/f_hp_hz/C_ac*1e-6,2))+'$M\\Omega$')

    C_in = C_ac*(1/(np.exp(lin_fit(f_hp,popt_left[0],popt_left[1])/10))-1)
    plt.text(f_hp-1.5, lin_fit(f_hp,popt_left[0],popt_left[1])+0.5, '$C_{in}=C_{ac}\cdot\\left(\\frac{V_{pp,FreqGen}(f_{hp})}{V_{pp,LFSFF}(f_{hp})}-1\\right)=$'+str(np.round(C_in[0]*1e15,2))+'fF')
    print(C_in*1e15)
    ###### plot everything

    plt.grid()
    plt.xlabel('log10(f)')
    plt.ylabel('$V_{pp}(LF SFF)/V_{pp}(Frequence Generator)$ in dB')
    plt.title(title)
    plt.ylim(np.min(y)-1, np.max(y)+1)
    plt.xlim(np.min(x)-1,np.max(x)+1)
    if output_path!= None:
        plt.savefig(output_path)
    plt.show()



    return  f_hp_hz, f_tp_hz


#data=np.genfromtxt("./data/bodeplot/bode.csv", delimiter=',')
#y = data[1:,1]
#x = data[1:,0]

#analyse_bode_plot(x,y, 'Test')