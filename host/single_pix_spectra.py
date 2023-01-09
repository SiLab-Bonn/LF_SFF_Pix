
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

vn = 1.1
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

### SETTINGS ###

channel = 'AOUT50'
row = 4
col = 3 #18

#print 'start'
#dut['VRESETP'].set_voltage(1, unit='V')
#dut['VM'].set_voltage(1, unit='V')
#val1,sync = dut.take_adc_data( channel, 10)
#print val1, np.mean(val1)
#dut['VRESETP'].set_voltage(1, unit='V')
#dut['VM'].set_voltage(0.8, unit='V')
#val2,sync = dut.take_adc_data( channel, 10)
#print val2, np.mean(val2)
#print 'res', (0.2/(np.mean(val1)-np.mean(val2)))*1000000, 'uA'

how_long = 1*60 #2*60*60 #secounds
threshold  = 80

###########

print "Take pedestals"
for i in range(1):
    dut['SEQ'].set_clk_divide(2)
    mean, stddev, diff = dut.take_single_data(row, col, 20, channel, 10000000, sample_start=11, sample_period=40, sample_sub_start=44, add_plot=True)

#dut['SEQ'].set_clk_divide(1)
#mean, stddev, diff = dut.take_single_data(row, col, 20, 'AOUT50v2', 500000, sample_start=9, sample_period=20, sample_sub_start=24, add_plot=True)
#dut['SEQ'].set_clk_divide(4)
#mean, stddev, diff = dut.take_single_data(row, col, 20, 'AOUT50v2', 500000, sample_start=13, sample_period=40*2, sample_sub_start=82, add_plot=True)

#plt.show()
plt.clf()
plt.ion()

print 'Start Data Take'
found = []
iter = 0

start_time = time.time()
ping_time = time.time()

while time.time() - start_time < how_long:
    
    mean, stdev, data = dut.take_single_data(row, col, 20, channel, 10000000, sample_start=11, sample_period=40, sample_sub_start=44, add_plot=False, show_info=False, set_seq=False)
    
    hits = np.nonzero(np.absolute(data - mean) > threshold)
    for i in hits:
        for j in i:
            val =  abs(data[j] - mean)
            print 'idx=', len(found), ' elem=', j, ' value=', val, "mean", mean, "stdev", stddev
            found.append(float(val));
            plt.clf()
            n, bins, patches = plt.hist(found, 40)
            plt.draw()
            
    iter += 1
    
    if time.time()-ping_time > 60:
        print "Time:", time.time() - start_time, "s"
        ping_time = time.time()

 
print 'Finished after iterations=', iter

plt.ioff()
plt.show()


# Save Data
log = {}
log['DATA'] = found
log['PIXEL'] = {"ROW":row , "COLUMN":col}
log['CHANNEL'] = channel
log['DURATION'] = how_long
log['STATUS'] = dut.get_status()

log_file_name = time.strftime("%Y_%m_%d_%H_%M_%S.yaml")
log_file = file(log_file_name, 'w')
yaml.dump(log, log_file) 

print "End."

