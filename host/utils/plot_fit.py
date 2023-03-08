#####
# This python module functions to fit fast and reliable while creating beautiful plots
#####
import matplotlib.pyplot as plt

def beauty_plot(xlabel='', ylabel='',log_x=False, log_y=False, figsize=[16,9], grid=True, grid_linestyle='-', title='', legend=True):
    plt.figure(figsize=(figsize[0],figsize[1]))
    plt.grid(grid, linestyle=grid_linestyle)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    if legend:
        plt.legend()



