#
#-------------------------------------
# 
#   Author: Sonia Fernandez-Perez
#   Date: 2014-02-13   
#-------------------------------------


#Summary:
#  This script powers the system and allow to measure iv curves with SHQ 122M power supply. 
#  When the read voltage and the set voltage is the same, current & voltage
#  are read 4 consecutive times. The average and standard deviation is calculated for each value, which
#  allows make a plot with error bars in x-y axis. The iv plot is shown in linear and logarithmic scale.
 
 
import yaml
import time

from xtb01 import xtb01
import Queue
import iseg_shq
import math
from math import sqrt
import matplotlib.pyplot as plt
import pylab
from pylab import *




#########################################################
#########  FUNTIONS DEFINITIONS #########################
#########################################################
def average(self):
        suma=0.0
        for i in range(0,len(self)):
            suma=suma+self[i]  
        prom=suma/float(len(self))
        return prom
    
def sdesviation(self):
        suma=0.0
        for i in range(0,len(self)):
            suma=suma+self[i]
        prom=suma/float(len(self))
        #print prom
        suma_dif_cuadrado=0
        for i in range(0,len(self)):
            suma_dif_cuadrado=suma_dif_cuadrado + (self[i]-prom)**2
            #print suma_dif_cuadrado
        varianza=suma_dif_cuadrado/float(len(self))
        return sqrt(varianza)
    
 
 
#####################################################################################
####################### POWERING THE SYSTEM #########################################
#####################################################################################
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
    
time.sleep(1)





#############################################################
################# IV MEASUREMENT ############################
#############################################################


com_message_q = Queue.Queue()

iseg = iseg_shq.IsegShqCom(com_message_q, '/dev/tty.usbserial-FTVNFS0AA', read_timeout=10)
print 'init_iseg', iseg.init_iseg()

print 'read_identifier', iseg.read_identifier()
print 'read_status_word', iseg.read_status_word()
print 'get_max_voltage',iseg.get_max_voltage()
print 'get_max_current',iseg.get_max_current()
print 'read_i_trip_ua',iseg.read_i_trip_ua()
print 'read_v_set', iseg.read_v_set(), 'V'
print 'read_current', iseg.read_current()*(10**6), 'uA'
print 'read_voltage', iseg.read_voltage(), 'V'  

error = 0.1

values_current_average=[]
values_voltage_average=[]
values_sd_current=[]
values_sd_voltage=[]


print '--- RAMPING UP ---'

for hv in range(10,200,10):
    
    print ' HV=', hv, 'V'
    print 'read_status_word', iseg.read_status_word()
    print 'write_v_set', iseg.write_v_set(voltage=hv)
    print 'write_start_ramp', iseg.write_start_ramp()
    time.sleep(6)

time.sleep(10)
print "--- SCAN: RAMPING DOWN ---"

r=range(10,210,10)
r.reverse()
for hv in r:
    print ' HV=', hv, 'V'
    print 'read_status_word', iseg.read_status_word()
    print 'write_v_set', iseg.write_v_set(voltage=hv)
    print 'write_start_ramp', iseg.write_start_ramp()
    time.sleep(1)
    while iseg.read_status_word() != 'ON' or abs(iseg.read_voltage()+hv) > error or math.isnan(iseg.read_current()):
        print '-wait status=', iseg.read_status_word()
        print '-read_current=', iseg.read_current()
        print '-read_voltage=', iseg.read_voltage()
        print '-error=', abs(iseg.read_voltage()+hv)
        time.sleep(1)
       
       
    print'----waiting to current stabilization------'    
    time.sleep(15)
    print '-----Starting to read the current & voltage-----'
    current= []
    voltagev=[]
    for i in range(0,4,1):
        voltagev.append(abs(iseg.read_voltage()))
        current.append(iseg.read_current()*(10**9))
        print 'read_status_word', iseg.read_status_word(), 'reading current & voltage'
        #print 'write_v_set', iseg.write_v_set(voltage=hv)
        #print 'write_start_ramp', iseg.write_start_ramp()
        time.sleep(1)
    print 'current:',current 
    print 'voltage:',voltagev
       
       
    ##############################################
    #####CURRENT & VOLTAGE AVERAGES ##############
    ##############################################
    average_current=0
    average_current=average(current)
    values_current_average.append(average_current)
    print 'values_current average', values_current_average
       
    average_voltage=0
    average_voltage=average(voltagev)
    values_voltage_average.append(average_voltage)
    print 'values_voltage average', values_voltage_average 
       
    ##########################################################
    ######CURRENT & VOLTAGE STANDARD DEVIATION################
    ##########################################################
    sd_current=0
    sd_current=sdesviation(current)
    values_sd_current.append(sd_current) 
    print 'standard deviation_current', values_sd_current    
       
    sd_voltage=0
    sd_voltage=sdesviation(voltagev)
    values_sd_voltage.append(sd_voltage) 
    print 'standard deviation_voltage', values_sd_voltage 
      
print '----- TOTAL VALUES -------:'   
print 'values_current_average:', values_current_average
print 'values_voltage_average:', values_voltage_average
print 'standard deviation_current', values_sd_current
print 'standard deviation_voltage', values_sd_voltage
 
hv=0    
print 'write_v_set', iseg.write_v_set(voltage=hv)
print 'write_start_ramp', iseg.write_start_ramp()
print 'test end'

# 
########################################
########SAVE DATA IN A TEXT FILE########
########################################
  
f = open("chip2_100.txt", "w+")
print >> f, "<V>", "<I>, sd_V, sd_I\n"
for f1, f2, f3, f4 in zip(values_voltage_average,values_current_average, values_sd_voltage, values_sd_current):
    print >> f, f1, f2, f3, f4
f.close()
  
  
   
##########################################################################
#############TO PLOT IN LINEAR AND LOGARITHMIC SCALE######################
##########################################################################
  
####linear
plt.figure('test')
plt.suptitle('test')
plt.errorbar(values_voltage_average,values_current_average,yerr=values_sd_current,xerr=values_sd_voltage,label="ring_total", color="blue", linewidth=2.0, marker='o', linestyle='-')
plt.xlabel('-Voltage [V]')
plt.ylabel('Currrent [nA]')
plt.legend()
  
plt.minorticks_on()
plt.savefig(time.strftime("%Y_%m_%d_%H_%M_chip2_100.png"))
  
######logarithmic
plt.figure('iv curve in logarithmic scale_matrix100')
plt.suptitle('iv curve in logarithmic scale_matrix100')
plt.errorbar(values_voltage_average,values_current_average,yerr=values_sd_current,xerr=values_sd_voltage,label="ring_total", color="blue", linewidth=2.0, marker='o', linestyle='-')
semilogy()
plt.xlabel('-Voltage [V]')
plt.ylabel(' log Currrent [nA]')
plt.legend()
plt.minorticks_on()
plt.savefig(time.strftime("%Y_%m_%d_%H_%M_chip2_100.png"))
  
plt.show()