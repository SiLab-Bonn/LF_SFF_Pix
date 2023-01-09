
import yaml
import time
import array
import matplotlib.pyplot as plt
import numpy as np
import itertools
import operator

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

vn = 1.2
dut['VNDIODE'].set_voltage(1.2, unit='V')
dut['VNDIODE'].set_enable(pwr_en)

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
dut['IBP_OUT_SF'].set_current(-30, unit='uA')

print 'IBP_CS_AMP:', dut['IBP_CS_AMP'].get_voltage(unit='V'), 'V', dut['IBP_CS_AMP'].get_current(unit='uA'), 'uA'
print 'IBN_COL_DRV:', dut['IBN_COL_DRV'].get_voltage(unit='V'), 'V', dut['IBN_COL_DRV'].get_current(unit='uA'), 'uA'
print 'IBP_OUT_SF:', dut['IBP_OUT_SF'].get_voltage(unit='V'), 'V', dut['IBP_OUT_SF'].get_current(unit='uA'), 'uA'
print ''

dut['AOUT50'].set_align_to_sync( True )
dut['AOUT25'].set_align_to_sync( True )
dut['AOUT50v2'].set_align_to_sync( True )
dut['AOUT100'].set_align_to_sync( True )

###########

dut['SEQ'].set_clk_divide(2)
print "SEQ:div", dut['SEQ'].get_clk_divide()

#############


def take_data(row, col, reset_seq_width = 10, channel = 'AOUT50v2', adc_data = 1000, sample_start=45, sample_period=320, sample_sub_start=320, add_plot = True, show_info = True, set_seq = True):
    
    if set_seq:
        ps = dut.single_pix_sel_seq(row,col,reset_seq_width)
        dut['SEQ'].start()
    
        time.sleep(0.05) #stady state
    
    samples, syncs = dut.take_adc_data(channel, adc_data)
            
    # probably should use NumPy for math like that
    sdata_a = samples[sample_sub_start::sample_period]
    sdata_ax = range(sample_sub_start,len(samples),sample_period)
    
    sdata_b = samples[sample_start::sample_period]
    sdata_bx = range(sample_start,len(samples),sample_period)
    
    size = min(len(sdata_a), len(sdata_b)) # just make the size same
    diff = map(operator.sub, sdata_a[0:size], sdata_b[0:size])

    arr = np.array([diff])
    mean = np.mean(arr)
    stddev = np.std((arr))

    if show_info:
        print 'row=', row, 'col=' , col, " stdev:", stddev, 'samples:', len(diff) ,'mean:', mean
    
    if add_plot:
        plt.plot(samples)
        plt.plot(sdata_ax, sdata_a, 'ro')
        plt.plot(sdata_bx, sdata_b, 'go')
    
    return mean, stddev, np.array(diff)


#dut['IBN_COL_DRV'].set_current(200, unit='uA')
#dut['IBP_OUT_SF'].set_current(-20, unit='uA')

row = 4
col = 4 #18

print "Take pedestals"
mean, stddev, diff = take_data(row, col, 20, 'AOUT50v2', 500000, sample_start=11, sample_period=40, sample_sub_start=44, add_plot=True)
#plt.show()




plt.ion()
how_long = 60*60 #secounds
threshold  = 40

print 'Start Data Take'
found = []
iter = 0
start_time = time.time()
while time.time() - start_time < how_long:
   
    m, s, data = take_data(row, col, 20, 'AOUT50v2', 500000, sample_start=11, sample_period=40, sample_sub_start=44, add_plot=False, show_info=False, set_seq=False)
   
    hits = np.nonzero(np.absolute(data - mean) > threshold)
    for i in hits:
        for j in i:
            val =  abs(data[j] - mean)
            print 'idx=', len(found), ' elem=', j, ' value=', val
            found.append(val);
            plt.clf()
            n, bins, patches = plt.hist(found, 40)
            plt.draw()
            
    iter += 1

print 'Finished after iterations=', iter, 'data_pins=', iter*500000
plt.show()
raw_input("Press Enter to continue...")

print "End."



#1 10 0 001_0010_0001 10_0001_0101
#11000 01 0010 0001 10 0001 0101
