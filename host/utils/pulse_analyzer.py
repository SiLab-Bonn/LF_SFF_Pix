import numpy as np
import utils.plot_fit as pltfit

def fast_online_analysis(data, baseline):
    #return np.max(np.greater(data-baseline,threshold), initial=-1)
    return np.min(data)

def fast_triggered_signal(data, baseline_end, skip_region, signal_duration):
    baseline = np.average(data[:baseline_end])
    event = np.min(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])#np.average(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])
    return baseline, event

def fit_landau(x, y, yerr, p, bounds):
    # p = mpv, eta, sigma, A
    # mpv max
    # eta offset
    # sigma std 
    # A amplitude
    popt, perr = pltfit.fit_landau_yerr(x,y,yerr,p,bounds)  
    return popt, perr

def online_analyser(data, threshold_x, threshold_y):
    data_min_pos = np.argmin(data)
    data_max_pos = np.argmax(data)
    if data_min_pos-data_max_pos <= threshold_x and data_min_pos-data_max_pos>0 and data[data_max_pos]-data[data_min_pos]>threshold_y:
        return np.average(data[:data_max_pos]),data[data_min_pos]
    else:
        return None, None