#####
# This python module functions to fit fast and reliable while creating beautiful plots
#####
import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize
from scipy import odr

def beauty_plot(create_fig=True,xlabel='', ylabel='',xlim=[0,0], ylim=[0,0],log_x=False, log_y=False, figsize=[16,9], grid=True, grid_linestyle='-', title='', legend=False, nrows=0, ncols=0, tight=True):
    if create_fig:
        plt.figure(figsize=(figsize[0],figsize[1]))
    plt.grid(grid, linestyle=grid_linestyle)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if tight:
        plt.tight_layout()
    if log_x:
        plt.xscale('log',base=10) 
    if xlim != [0,0]:
        plt.xlim(xlim[0],xlim[1])
    if ylim != [0,0]:
        plt.ylim(ylim[0],ylim[1])
    if legend:
        plt.legend()



def func_lin(p,x):
    a,b=p
    return a*x+b

def func_quad(p,x):
    a,b,c=p
    return a*x**2+b*x+c

def func_cub(p,x):
    a,b,c,d = p
    return a*x**3+b*x**2+c*x+d

def func_cos(x,a,b,c,d):
    return a*np.cos(b*x+c)+d

def func_cos_lin(x,a,b,c,d,e):
    return a*np.cos(b*x+c)+d*x+e


def guess_cos_params(y,f):
    ampl_limits = [np.amin(y),np.amax(y)]
    ampl_approx = np.abs(np.abs(ampl_limits[0])-np.abs(ampl_limits[1]))/2
    offset_approx = ampl_approx+ampl_limits[0]
    freq  = f*2*np.pi
    first_max_loc = 0
    slope = 0
    try:
        for i in range(0,len(y)):
            current_max = 0
            if y[i] >= current_max:
                pass_if = 100
                pass_count = 0
                for j in range(0,pass_if):
                    if(y[i]>=y[i+j]):
                        pass_count+=1
                if pass_if == pass_count:
                    current_max = y[i]
                    first_max_loc = i
                    break
    except:
        print('Could not guess all fit parameters')
    else:
        return ampl_approx, freq, -first_max_loc, offset_approx
        
def double_err(function, x, x_error, y, y_error, presets):
    model = odr.Model(function)
    data = odr.RealData(x, y, sx=x_error, sy=y_error)
    out = odr.ODR(data, model, beta0=presets).run()
    popt = out.beta
    perr = out.sd_beta

    return popt,perr

def fit_no_err(function, x, y, presets):
    popt, perr = optimize.curve_fit(function, x, y, presets)
    perr = np.sqrt(np.diag(perr))
    return popt, perr


