#####
# This python module functions to fit fast and reliable while creating beautiful plots
#####
import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize
from scipy import odr
import pylandau
from scipy.optimize import curve_fit

def beauty_plot(create_fig=True,xlabel='', ylabel='',xlim=[0,0], ylim=[0,0],log_x=False, log_y=False, figsize=[16,9], grid=True, grid_linestyle='-', title='', legend=False, nrows=0, ncols=0, tight=True, fontsize=15, label_size=None):
    plt.rcParams["font.family"] = "serif"
    plt.rcParams['font.size'] = fontsize
    if label_size:
        fontsize = label_size
    if create_fig:
        plt.figure(figsize=(figsize[0],figsize[1]))
    plt.grid(grid, linestyle=grid_linestyle)
    plt.title(title, fontsize=fontsize)
    plt.xlabel(xlabel, fontsize=fontsize)
    plt.ylabel(ylabel, fontsize=fontsize)
    if tight:
        plt.tight_layout()
    if log_x:
        plt.xscale('log',base=10) 
    if log_y:
        plt.yscale('log',base=10)
    if xlim != [0,0]:
        plt.xlim(xlim[0],xlim[1])
    if ylim != [0,0]:
        plt.ylim(ylim[0],ylim[1])
    if legend:
        plt.legend()

def beauty_plot_two_y_scales(x,data1, data2, xlabel, ylabel1, ylabel2, label1, label2, alpha1=1, alpha2=1, legend=True, show=True, xfit1=None, yfit1=None, yfitlabel1=None, xfit2=None, yfit2=None, yfitlabel2=None,image_path=None, title=None):
    fig, ax1 = plt.subplots()
    fig.set_figwidth(16)
    fig.set_figheight(9)
    beauty_plot(create_fig=False,tight=False)
    color = 'tab:red'
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel1, color=color)
    ax1.plot(x, data1, color=color, label=label1, alpha=alpha1)
    if xfit1:
        plt.plot(xfit1, yfit1, color='black', label=yfitlabel1)
    ax1.tick_params(axis='y', labelcolor=color)
    ax2 = ax1.twinx()  
    color = 'tab:blue'
    ax2.set_ylabel(ylabel2, color=color) 
    ax2.plot(x, data2, color=color, label=label2, alpha=alpha2)
    ax2.tick_params(axis='y', labelcolor=color)
    if xfit2:
        plt.plot(xfit2, yfit2, color='black', label=yfitlabel2)
    if title: ax2.set_title(title)
    if legend: fig.legend()
    if image_path: plt.savefig(image_path)
    if show: plt.show()



def func_landau(p, x):
    mpv, eta, sigma, A = p
    return pylandau.langau(x, mpv, eta, sigma, A)

def func_const(p,x):
    a = p[0]
    return 0*x+a

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

def func_gauss(p, x):
    a,b,c,d = p
    return a*np.exp(-(x-b)**2/2/c**2)+d

def func_gauss_no_offset(p, x):
    a,b,c = p
    return a*np.exp(-(x-b)**2/2/c**2)

def func_gauss_no_offset_normed(p, x):
    b,c = p
    return np.exp(-(x-b)**2/2/c**2)

def func_exp(p,x):
    a,b,c,d = p
    return a*np.exp((b*x)+c)+d

def func_log(p,x):
    a,b,c,d = p
    return a*np.log(b*x+c)+d

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

def no_err(function, x, y, presets):
    model = odr.Model(function)
    data = odr.RealData(x, y)
    out = odr.ODR(data, model, beta0=presets).run()
    popt = out.beta
    perr = out.sd_beta

    return popt,perr

def fit_no_err(function, x, y, presets):
    popt, perr = optimize.curve_fit(function, x, y, presets)
    perr = np.sqrt(np.diag(perr))
    return popt, perr


def fit_landau_yerr(x, y, yerr, p, bounds = [1, 10000]):
    mpv, eta, sigma, A = p
    coeff, pcov = curve_fit(pylandau.langau, x, y,
                        sigma=yerr,
                        absolute_sigma=True,
                        p0=(mpv, eta, sigma, A),
                        bounds=(bounds[0], bounds[1]))
    return coeff, pcov

#######
# HISTOGRAM
#######

def rebin(x, y):
    rebin_data = []
    z=0
    for i in range(len(x)):
        for j in range(int(y[i])):
            rebin_data.append(x[z])
        z+=1
    return np.array(rebin_data)

def reshape_x(x):
    new_x = []
    for i in range(len(x)-1):
        new_x.append((x[i]+x[i+1])/2)
    return np.array(new_x)
