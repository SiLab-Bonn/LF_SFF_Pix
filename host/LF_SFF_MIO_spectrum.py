import numpy as np
import matplotlib.pyplot as plt
from utils.initialize_measurement import initialize_measurement as init_meas
import utils.plot_fit as pltfit


load_data, chip_version, image_path, data_path = init_meas('spectra')

def FE55():
    data_path = image_path+'FE55/'
    data = np.genfromtxt(data_path+'spectrum.csv', delimiter=',')
    x = data[1:,0]
    y = data[1:,1]/np.max(data[1:,1])
    pltfit.beauty_plot(xlabel='Amplitude / mV', ylabel='Counts (normalized)', title=chip_version+': Fe55 spectrum (total counts = %i)'%(len(y)))
    plt.plot(x, y, color='darkred', label='Data')
    lim_alpha = [0.0064, 0.0085]
    lim_min_alpha = np.argmin(np.abs(x - lim_alpha[0]))
    lim_max_alpha = np.argmin(np.abs(x - lim_alpha[1]))
    popt_alpha, perr_alpha = pltfit.no_err(function=pltfit.func_gauss_no_offset_normed, x=x[lim_min_alpha:lim_max_alpha], y=y[lim_min_alpha:lim_max_alpha], presets=[x[np.argmax(y)],0.001])
    
    k_alpha_x = np.linspace(x[lim_min_alpha-10:lim_max_alpha+10][0], x[lim_min_alpha-10:lim_max_alpha+10][-1], 1000)
    k_alpha_gauss = pltfit.func_gauss_no_offset_normed(x=k_alpha_x, p=popt_alpha)
    y_filtered = np.append(y[:lim_min_alpha-10], np.array(y[lim_min_alpha-10:lim_max_alpha+10])-pltfit.func_gauss_no_offset_normed(x=x[lim_min_alpha-10:lim_max_alpha+10], p=popt_alpha))
    y_filtered = np.append(y_filtered, y[lim_max_alpha+10:])
    y_filtered = [y_filtered[i] if y_filtered[i]>=0 else 0 for i in range(len(y_filtered)) ]

    lim_beta = [0.008, 0.01]
    lim_min_beta = np.argmin(np.abs(x - lim_beta[0]))
    lim_max_beta = np.argmin(np.abs(x - lim_beta[1]))
    #plt.fill_between(x[lim_min_beta:lim_max_beta],y_filtered[lim_min_beta:lim_max_beta], color='blue', alpha=0.5)
    k_beta_x = np.linspace(x[lim_min_beta-10:lim_max_beta+10][0], x[lim_min_beta-10:lim_max_beta+10][-1], 1000)
    
    popt_beta, perr_beta = pltfit.no_err(function=pltfit.func_gauss_no_offset, x=x[lim_min_beta:lim_max_beta], y=y_filtered[lim_min_beta:lim_max_beta], presets=[0.05, 0.009,0.0005])
    k_beta_gauss = pltfit.func_gauss_no_offset(x=k_beta_x, p=popt_beta)
    
    plt.plot(k_beta_x, k_beta_gauss, color='black', linestyle='--')
    plt.text(popt_alpha[0], y=np.max(k_alpha_gauss), s = '$k_\\alpha$')
    plt.text(popt_beta[0], y=np.max(k_beta_gauss), s = '$k_\\beta$')
    
    plt.plot(k_alpha_x, k_alpha_gauss, color='black', linestyle='-.')
    plt.vlines(x=popt_alpha[0], ymin=0, ymax=np.max(k_alpha_gauss), color='black', linestyles='-.')

    
    #plt.plot(x, y_filtered)    

   # plt.fill_between(x[lim_min_alpha:lim_max_alpha],y[lim_min_alpha:lim_max_alpha], color='darkred', alpha=0.5)
    plt.fill_between(x,y, color='red', alpha=0.3)
    plt.legend()

    plt.show()


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

def FE55_test():
    data_path = image_path+'FE55/'
    data = np.genfromtxt(data_path+'spectrum.csv', delimiter=',')
    background = np.genfromtxt(data_path+'background.csv', delimiter=',')
    x = data[1:,0]
    y = data[1:,1]
    background_x = background[1:,0]
    background_y = background[1:,1]
    #plt.hist(x=x, weights=y, bins=150)

    #hist_y, hist_x, hist_bins = plt.hist(rebin(x, y), bins=np.linspace(background_x[0],background_x[-1], 150))
    bins = np.arange(0,0.04, 0.0005)
    bg_y, bg_x, bg_bins = plt.hist(rebin(background_x, background_y), bins=bins, alpha=0.5,label='background', density=True)
    plt.close()
    
    #bg_y, bg_x, bg_bins = plt.hist(rebin(background_x, background_y), bins=np.linspace(background_x[0],background_x[-1], 150))
    #print((hist_y-bg_y).shape, hist_x.shape, reshape_x(hist_x).shape)

   # 
    pltfit.beauty_plot(xlabel='Amplitude / mV', ylabel='Counts', title=chip_version+': Fe55 spectrum (total counts = %i)'%(np.sum(y)))
    hist_y, hist_x, hist_bins = plt.hist(rebin(x, y), bins=bins, alpha=0.5, label='Data', density=True)
    
    scaling_factor = hist_y[4]/bg_y[4]
    
    bg_y, bg_x, bg_bins =plt.hist(x=reshape_x(bg_x), weights=bg_y*scaling_factor, bins=bins, label='background', alpha=0.5)
    plt.hist(x=reshape_x(hist_x), weights=hist_y-bg_y, bins=bins, alpha=0.5, label='diff')
    plt.legend()

    '''
    y,x, bins = plt.hist(x=x, weights=y, bins=150)
    lim_alpha = [0.0064, 0.0085]
    lim_min_alpha = np.argmin(np.abs(x - lim_alpha[0]))
    lim_max_alpha = np.argmin(np.abs(x - lim_alpha[1]))
    popt_alpha, perr_alpha = pltfit.no_err(function=pltfit.func_gauss_no_offset, x=x[lim_min_alpha:lim_max_alpha], y=y[lim_min_alpha:lim_max_alpha], presets=[np.max(y),x[np.argmax(y)],0.0005])
    
    background_y, background_x, background_bins = plt.hist(x=background_x, weights=background_y, bins=150)'''

    '''
    k_alpha_x = np.linspace(x[lim_min_alpha-10:lim_max_alpha+10][0], x[lim_min_alpha-10:lim_max_alpha+10][-1], 1000)
    k_alpha_gauss = pltfit.func_gauss_no_offset(x=k_alpha_x, p=popt_alpha)
    plt.plot(k_alpha_x, k_alpha_gauss, color='black', linestyle='-.')'''

    plt.show()

def Cd109(file):
    data_path = image_path+'Cd109/'
    data = np.genfromtxt(data_path+file, delimiter=',')
    x = data[1:,0]
    y = data[1:,1]
    #plt.hist(x, weights=y, bins=500)

    #bg_y, bg_x, bg_bins = plt.hist(rebin(background_x, background_y), bins=np.linspace(background_x[0],background_x[-1], 150))
    #print((hist_y-bg_y).shape, hist_x.shape, reshape_x(hist_x).shape)

    bins = np.arange(np.min(x),np.max(x), 0.0005)
    print(len(bins))
    pltfit.beauty_plot(xlabel='Amplitude / mV', ylabel='Counts', title=chip_version+': Cd109 spectrum (total counts = %i)'%(np.sum(y)))
    hist_y, hist_x, hist_bins = plt.hist(rebin(x, y), bins=bins, alpha=0.5, label='Data')
    
    plt.legend()
    plt.show()

def overlay(sources=[], PWELL=-3, DIODE_HV=0.4, density=True, n_bins=1000):
    x = []
    y = []
    max_x = 0
    for source in sources:
        data_path = image_path+source+'/'
        data = np.genfromtxt(data_path+source+'_%s_%s.csv'%(str(DIODE_HV), str(PWELL)), delimiter=',')
        x.append(data[1:,0])
        y.append(data[1:,1])
        if np.max(data[1:,0])>=max_x:
            max_x = np.max(data[1:,0])

    bins = np.arange(0,max_x, 1/n_bins)
    
    pltfit.beauty_plot(xlabel='Amplitude / V', ylabel='', title=chip_version+' chip\nPW_BIAS=%.1fV, DIODE_HV=%.1fV, %i bins'%(PWELL, DIODE_HV, len(bins)), create_fig=True)
    for i in range(len(sources)):
        data_y, data_x, data_bins = plt.hist(rebin(x[i], y[i]), bins=bins, alpha=0.5, label=sources[i], density=density, edgecolor='black')     
    plt.legend()
    plt.savefig(image_path+'hist_of_multiple_sources.pdf', bbox_inches='tight')
    plt.show()


    if not len(sources)/3%2: num_rows = int(len(sources)/3)
    else: num_rows = int(len(sources)/3+1)
    fig, ax = plt.subplots(num_rows, 3, squeeze=False)
    fig.set_figheight(9)
    fig.set_figwidth(16)
    fig.suptitle(chip_version+' chip\nPW_BIAS=%.1fV, DIODE_HV=%.1fV, %i bins'%(PWELL, DIODE_HV, len(bins)))
    a = ax.ravel()
    for i,ax in enumerate(a):
        if i > len(sources)-1: break
        else:
            ax.hist(rebin(x[i], y[i]), bins=bins, alpha=0.5, label=sources[i], edgecolor='black')
            ax.set_title(sources[i])
            ax.grid()
            ax.set_xlabel('Amplitude / V')
            ax.set_ylabel('Counts')
    for i in range(len(a)-len(sources)):
        fig.delaxes(a[-1-i])
    plt.tight_layout()
    plt.savefig(image_path+'hists_of_multiple_sources.pdf', bbox_inches='tight')
    plt.show()


def overlay_normed(sources=[], PWELL=-3, DIODE_HV=0.4, density=True, n_bins=1000):
    x = []
    xbins = []
    max_x = 0
    for source in sources:
        data_path = image_path+source+'/'
        data = np.genfromtxt(data_path+source+'_%s_%s.csv'%(str(DIODE_HV), str(PWELL)), delimiter=',')
        xdata = data[1:,0]
        ydata = data[1:,1]
        if np.max(data[1:,0])>=max_x:
            max_x = np.max(data[1:,0])
        bins = np.arange(0,max_x, 1/n_bins)
        nx, nxbins, nxpatch = plt.hist(rebin(xdata, ydata), bins=bins, alpha=0.5, density=density, edgecolor='black') 
        x.append(nx)
        xbins.append(nxbins)
        plt.close()
    
    pltfit.beauty_plot(xlabel='Amplitude / V', ylabel='Counts (normalized)', title=chip_version+' chip\nPW_BIAS=%.1fV, DIODE_HV=%.1fV, %i bins'%(PWELL, DIODE_HV, len(bins)), create_fig=True)
    for i in range(len(sources)):
        plt.plot(reshape_x(xbins[i]), x[i]/np.max(x[i]), label=sources[i])
        plt.fill_between(reshape_x(xbins[i]), x[i]/np.max(x[i]), alpha=0.5)
        
    plt.legend()
    plt.savefig(image_path+'hist_of_multiple_sources_normed.pdf', bbox_inches='tight')
    plt.show()

    if not len(sources)/3%2: num_rows = int(len(sources)/3)
    else: num_rows = int(len(sources)/3+1)
    fig, ax = plt.subplots(num_rows, 3, squeeze=False)
    fig.set_figheight(9)
    fig.set_figwidth(16)
    fig.suptitle(chip_version+' chip\nPW_BIAS=%.1fV, DIODE_HV=%.1fV, %i bins'%(PWELL, DIODE_HV, len(bins)))
    a = ax.ravel()
    for i,ax in enumerate(a):
        if i > len(sources)-1: break
        else:
            ax.plot(reshape_x(xbins[i]), x[i]/np.max(x[i]), label=sources[i])
            ax.fill_between(reshape_x(xbins[i]), x[i]/np.max(x[i]), alpha=0.5)
            ax.set_title(sources[i])
            ax.grid()
            ax.set_xlabel('Amplitude / V')
            ax.set_ylabel('Counts (normalized)')
    for i in range(len(a)-len(sources)):
        fig.delaxes(a[-1-i])
    plt.tight_layout()
    plt.savefig(image_path+'hists_of_multiple_sources_normed.pdf', bbox_inches='tight')
    plt.show()

def overlay_different_PWELL(source, PWELL_list=[], DIODE_HV=0.4, density=False, n_bins=1000):
    x = []
    xbins = []
    max_x = 0
    for PWELL in PWELL_list:
        data_path = image_path+source+'/'
        data = np.genfromtxt(data_path+source+'_%s_%s.csv'%(str(DIODE_HV), str(PWELL)), delimiter=',')
        xdata = data[1:,0]
        ydata = data[1:,1]
        if np.max(data[1:,0])>=max_x:
            max_x = np.max(data[1:,0])
        bins = np.arange(0,max_x, 1/n_bins)
        nx, nxbins, nxpatch = plt.hist(rebin(xdata, ydata), bins=bins, alpha=0.5, density=density, edgecolor='black') 
        x.append(nx)
        xbins.append(nxbins)
        plt.close()
    
    pltfit.beauty_plot(xlabel='Amplitude / V', ylabel='Counts (normalized)', title=chip_version+' chip\nPW_BIAS=%.1fV, DIODE_HV=%.1fV, %i bins'%(PWELL, DIODE_HV, len(bins)), create_fig=True)
    for i in range(len(PWELL_list)):
        plt.plot(reshape_x(xbins[i]), x[i]/np.max(x[i]), label='PWELL_BIAS=%.2fV'%(PWELL_list[i]))
        plt.fill_between(reshape_x(xbins[i]), x[i]/np.max(x[i]), alpha=0.5)
        
    plt.legend()
    plt.savefig(image_path+'hist_of_multiple_sources_normed.pdf', bbox_inches='tight')
    plt.show()

    if not len(PWELL_list)/3%2: num_rows = int(len(PWELL_list)/3)
    else: num_rows = int(len(PWELL_list)/3+1)
    fig, ax = plt.subplots(num_rows, 3, squeeze=False)
    fig.set_figheight(9)
    fig.set_figwidth(16)
    fig.suptitle('%s: %s chip\nDIODE_HV=%.1fV, %i bins'%(source, chip_version, DIODE_HV, len(bins)))
    a = ax.ravel()
    for i,ax in enumerate(a):
        if i > len(PWELL_list)-1: break
        else:
            ax.plot(reshape_x(xbins[i]), x[i]/np.max(x[i]), label=PWELL_list[i])
            ax.fill_between(reshape_x(xbins[i]), x[i]/np.max(x[i]), alpha=0.5)
            ax.set_title('PWELL_BIAS=%.2fV'%(PWELL_list[i]))
            ax.grid()
            ax.set_xlabel('Amplitude / V')
            ax.set_ylabel('Counts (normalized)')
    for i in range(len(a)-len(PWELL_list)):
        fig.delaxes(a[-1-i])
    plt.tight_layout()
    plt.savefig(image_path+'hists_of_multiple_sources_normed.pdf', bbox_inches='tight')
    plt.show()

#FE55()
#FE55_test()
#Cd109(file='Tek005ampl.csv')

#overlay(['Fe55','Cd109'], PWELL=-5, DIODE_HV=0.4)
#overlay(['Cd109','Tb', 'Ba','Ag', 'Cu'], PWELL=-3, DIODE_HV=0.4)
#overlay_normed(['Cd109','Tb', 'Ba', 'Cu'], PWELL=-3, DIODE_HV=0.4, density=False, n_bins=1000)
#overlay_different_PWELL('Cd109', PWELL_list=[-3,-6], DIODE_HV=0.4, density=False, n_bins=500)
#overlay_normed(['Cd109', 'Cd109_sum'], PWELL=-6, DIODE_HV=0.4, density=True, n_bins=1000)
#overlay_normed(['Cd109_sum', 'Cd109'], PWELL=-6, DIODE_HV=0.4, density=True, n_bins=1000)
overlay_normed(['Cd109_back', 'Cd109'], PWELL=-3, DIODE_HV=0.4, density=True, n_bins=1000)
