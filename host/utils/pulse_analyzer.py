import numpy as np

def fast_online_analysis(data, baseline):
    #return np.max(np.greater(data-baseline,threshold), initial=-1)
    return np.min(data)

def fast_triggered_signal(data, baseline_end, skip_region, signal_duration):
    baseline = np.average(data[:baseline_end])
    event = np.min(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])#np.average(data[baseline_end+skip_region:baseline_end+skip_region+signal_duration])
    return baseline, event