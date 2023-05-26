import numpy as np

def fast_online_analysis(data, threshold, baseline):
    return data[np.max(np.greater(data-baseline,threshold), initial=-1)]
