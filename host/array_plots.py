
import yaml
import time
import matplotlib.pyplot as plt
import numpy as np

from xtb01 import xtb01

stream = open("xtb01.yaml", 'r')
cnfg = yaml.load(stream)

dut = xtb01(cnfg)
dut.init()

pwr_en = False # True
pwr_en = True

dut['DVDD'].set_current_limit(10, unit='mA')

dut['DVDD'].set_voltage(1.8, unit='V')
dut['DVDD'].set_enable(pwr_en)

dut['AVDD'].set_voltage(1.8, unit='V')
dut['AVDD'].set_enable(pwr_en)

vn = 1.1
dut['VNDIODE'].set_voltage(vn, unit='V')
dut['VNDIODE'].set_enable(False)

time.sleep(0.1)

print 'DVDD:', dut['DVDD'].get_voltage(unit='V'), 'V', dut['DVDD'].get_current(), 'mA'
print 'AVDD:', dut['AVDD'].get_voltage(unit='V'), 'V', dut['AVDD'].get_current(), 'mA'
print 'VNDIODE:', dut['VNDIODE'].get_voltage(unit='V'), 'V', dut['VNDIODE'].get_current(), 'mA'
print ''

dut['VRESETP'].set_voltage(vn, unit='V')
dut['VRESETN'].set_voltage(vn, unit='V')
dut['FADC_VREF'].set_voltage(1.8, unit='V')

print 'VRESETP:', dut['VRESETP'].get_voltage(unit='V'), 'V', dut['VRESETP'].get_current(), 'mA'
print 'VRESETN:', dut['VRESETN'].get_voltage(unit='V'), 'V', dut['VRESETN'].get_current(), 'mA'
print 'FADC_VREF:', dut['FADC_VREF'].get_voltage(unit='V'), 'V', dut['FADC_VREF'].get_current(), 'mA'
print ''

dut['IBP_CS_AMP'].set_current(-30, unit='uA')
dut['IBN_COL_DRV'].set_current(50, unit='uA')
dut['IBP_OUT_SF'].set_current(-50, unit='uA')

print 'IBP_CS_AMP:', dut['IBP_CS_AMP'].get_voltage(unit='V'), 'V', dut['IBP_CS_AMP'].get_current(unit='uA'), 'uA'
print 'IBN_COL_DRV:', dut['IBN_COL_DRV'].get_voltage(unit='V'), 'V', dut['IBN_COL_DRV'].get_current(unit='uA'), 'uA'
print 'IBP_OUT_SF:', dut['IBP_OUT_SF'].get_voltage(unit='V'), 'V', dut['IBP_OUT_SF'].get_current(unit='uA'), 'uA'
print ''

dut['AOUT50'].set_align_to_sync( True )
dut['AOUT25'].set_align_to_sync( True )
dut['AOUT50v2'].set_align_to_sync( True )
dut['AOUT100'].set_align_to_sync( True )

###

cols = 16
rows = 16
channel = 'AOUT50'
dev = 1

###

def plot_sample(frames):
    data, sync = dut.take_adc_data(channel, frames*seq_size*dev)
    
    frames = len(data)/(seq_size*dev)-1
    for i in range(frames):
        plt.plot(data[i*seq_size*dev:(i+1)*seq_size*dev])
        
    plt.plot(sync[0:seq_size*dev+5]*1000+8000)
    
    sample_x = range(start,seq_size*dev,speriod)
    plt.plot(sample_x, data[sample_x], 'ro')
    
    plt.show()

def plot_column(frames):
    val, sync = dut.take_adc_data(channel, frames*seq_size*dev)
    data = val[start::speriod]
    for i in range(len(data)/(2*col+2)-1):
        plt.plot(data[i*(2*col+2):(i+1)*(2*col+2)])
    plt.show()


def plot_array():
    
    # TAKE DATA
    val, sync = dut.take_adc_data(channel, 10000000) #take some data
    
    # PROCESS DATA
    sample = val[start::speriod] # select sampling points
    sample = sample[:len(sample)-(len(sample)%(seq_size/2))]  # fix the size so is always full n frames
    sample = sample.reshape(-1,cols+1) # make 2D array cut at columns
    
    #sample = np.roll(sample, -1, 1) #this is funny just looks better to put left most to right
    
    # select rows ### and cut the reset/change row sample?
    cut_reset = True
    data_rows = sample[0::2,:cols+1-cut_reset] 
    reset_rows= sample[1::2,:cols+1-cut_reset] 
    
    #make frames (3D array)
    reset_frames = reset_rows.reshape(-1, rows, cols+1-cut_reset)
    data_frames = data_rows.reshape(-1, rows, cols+1-cut_reset)
    
    # to align
    reset_frames = reset_frames[:reset_frames.shape[0]-1,:,:] #remove last frame to match
    data_frames =  data_frames[1:,:,:] #remove first frame which is data from non existing reset 
    
    data =  data_frames - reset_frames #get the real values
    
    mean = np.mean(data, axis=0)
    std = np.std(data, axis=0)
    
    # PLOT 
    print 'Number of frames:', data.shape[0], 'Mean', np.mean(mean), 'Std(mean)', np.mean(std)
    
    #Automatic masking (3 sigma)
    sigma = 3
    mask =  np.abs(std - np.mean(std[1:-1,1:-1])) < sigma*np.std(std[1:-1,1:-1])

    #fix axis so it looks like layout
    axis = [mean.shape[1]-0.5, -0.5, -0.5, mean.shape[0]-0.5]
    
    fig = plt.gcf()
    fig.canvas.set_window_title('XTB01 - ' + channel + ' ('+str(cols)+','+str(rows)+')')

    plt.subplot(2,2,1)
    mean[~mask] = np.nan
    plt.imshow(mean, cmap=plt.cm.jet, interpolation='nearest')
    plt.title('Pedestal [ADU]')
    plt.axis(axis)
    plt.colorbar()
    
    plt.subplot(2,2,2)
    std[~mask] = np.nan
    implot = plt.imshow(std, cmap=plt.cm.jet, interpolation='nearest')
    #implot.set_clim(5.0,40.0)
    plt.title('Noise [ADU]')
    plt.axis(axis)
    plt.colorbar()
    
    plt.subplot(2,2,4)
    implot = plt.imshow(np.mean(data_frames, axis=0), cmap=plt.cm.jet, interpolation='nearest')
    plt.title('Mean (data) [ADU]')
    plt.axis(axis)
    plt.colorbar()
    
    plt.subplot(2,2,3)
    plt.imshow(np.mean(reset_frames, axis=0), cmap=plt.cm.jet, interpolation='nearest')
    plt.title('Mean (reset) [ADU]')
    plt.axis(axis)
    plt.colorbar()
    
    plt.show()
    

dut['SEQ'].set_clk_divide(dev)
seq_size = dut.simple_seq(cols=cols, rows=rows, channels = (channel))
print 'SEQ size:', seq_size

dut['SEQ'].start()

start = 5+dev
speriod = dev*2

#plot_sample(5)
#plot_column(5)
plot_array()


