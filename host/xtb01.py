#
# ------------------------------------------------------------
# Copyright (c) SILAB , Physics Institute of Bonn University
# ------------------------------------------------------------
#
# SVN revision information:
#  $Rev:: 17                    $:
#  $Author:: themperek          $:
#  $Date:: 2013-09-19 21:55:29 #$:
#

import sys
sys.path.append('../../git/basil/basil/trunk/host/pydaq/')

#from pydaq import Dut
from basil.dut import Dut
import array
import itertools
import socket
import time
import numpy as np
import matplotlib.pyplot as plt

class xtb01(Dut):

    def single_pix_sel_seq(self, row, col, reset_seq_width):
        
        self['SEQ'].clear()

        self['SEQ']['RESET_ROW_CNT'][0] = 1;
        self['SEQ']['RESET_ROW_CNT'][1] = 1;
        
        self['SEQ']['RESET_COL_CNT'][0] = 1;
        self['SEQ']['RESET_COL_CNT'][1] = 1;
        
        self['SEQ']['CLK_COL_50'][0] = 0
        self['SEQ']['CLK_COL_50'][1] = 1
        
        self['SEQ']['CLK_ROW_50'][0] = 0
        self['SEQ']['CLK_ROW_50'][1] = 1

        for i in range(row):
            self['SEQ']['CLK_ROW_50'][2+2*i] = 0
            self['SEQ']['CLK_ROW_50'][2+2*i+1] = 1

        for i in range(col):
            self['SEQ']['CLK_COL_50'][2+2*i] = 0
            self['SEQ']['CLK_COL_50'][2+2*i+1] = 1
                
        done = 2 + 2*max(row, col)
        
        self['SEQ']['ROW_RESET_50'][done+reset_seq_width] = 1;
        
        self['SEQ'].set_size(done+reset_seq_width+2)
        self['SEQ'].set_repaet_start(done+2)
        
        
        self['SEQ']['ROW_RESET_100'] = self['SEQ']['ROW_RESET_50']
        self['SEQ']['ROW_RESET_25'] = self['SEQ']['ROW_RESET_50']
        
        self['SEQ']['CLK_ROW_100'] = self['SEQ']['CLK_ROW_50']
        self['SEQ']['CLK_COL_100'] = self['SEQ']['CLK_COL_50']
        self['SEQ']['CLK_COL_25'] = self['SEQ']['CLK_COL_50']
        self['SEQ']['CLK_ROW_25'] = self['SEQ']['CLK_ROW_50']
        
        self['SEQ']['ADC_SYNC_50'] = self['SEQ']['ROW_RESET_50']
        self['SEQ']['ADC_SYNC_25'] = self['SEQ']['ROW_RESET_50']
        self['SEQ']['ADC_SYNC_100'] = self['SEQ']['ROW_RESET_50']
        
        self['SEQ'].write(done+100)
        
        return done+2
    
    
    def simple_seq(self, rows = 16, cols = 16, channels = ('AOUT50v2') ):
        #TODO: add other channels
        
        self['SEQ']['ADC_SYNC_50'][0] = 1;
        self['SEQ']['ADC_SYNC_50'][1] = 0;
               
        i = 0
        for row in range(rows):
        
            self['SEQ']['RESET_COL_CNT'][i] = 1;
            self['SEQ']['RESET_COL_CNT'][i+1] = 1;
            
            for column in range(cols):
                self['SEQ']['CLK_COL_50'][i] = 0
                i += 1
                self['SEQ']['CLK_COL_50'][i] = 1
                i += 1
                
            
            self['SEQ']['ROW_RESET_50'][i] = 1;
            i += 1
            self['SEQ']['ROW_RESET_50'][i] = 1;
            i += 1
            
            self['SEQ']['RESET_COL_CNT'][i] = 1;
            self['SEQ']['RESET_COL_CNT'][i+1] = 1;
        
            for column in range(cols):
                self['SEQ']['CLK_COL_50'][i] = 0
                i += 1
                self['SEQ']['CLK_COL_50'][i] = 1
                i += 1
                
        
            self['SEQ']['CLK_ROW_50'][i] = 0
            i += 1
            self['SEQ']['CLK_ROW_50'][i] = 1
            i += 1
        
        self['SEQ']['RESET_ROW_CNT'][i-1] = 1;
        self['SEQ']['RESET_ROW_CNT'][i-2] = 1;
        
        
        self['SEQ'].set_size(i)
        self['SEQ'].write(i)
        
        return i

    #@profile
    def take_adc_data(self, channel, how_much = 1000000):
    
        self['DATA_FIFO'].reset()
        self[channel].set_data_count(how_much)
        self[channel].start()
        
        nmdata = self['DATA_FIFO'].get_data()
        
        while self[channel].is_done() == False:
            nmdata = np.append(nmdata, self['DATA_FIFO'].get_data());
        
        nmdata = np.append(nmdata, self['DATA_FIFO'].get_data());
        
        if(how_much/2 != len(nmdata)):
            print ("Error: Data lost!", how_much/2, len(nmdata))
        
        val0 = np.right_shift(np.bitwise_and(nmdata, 0x0fffc000), 14)
        val1 = np.bitwise_and(nmdata, 0x00003fff)
        vals = np.right_shift(np.bitwise_and(nmdata, 0x10000000), 28)
       
        val = np.reshape(np.vstack((val0, val1)), -1, order='F')
        sync = np.reshape(np.vstack((vals, vals)), -1, order='F')

        return val, sync
    
    def set_seq_50():
        
        self['SEQ']['CLK_ROW_25'][0] = 1
        self['SEQ']['ROW_RESET_25'][1] = 1
        
        # setup 50um pattern
        self['SEQ']['RESET_ROW_CNT'][0] = 1;
        self['SEQ']['RESET_ROW_CNT'][1] = 1;
        
        self['SEQ']['RESET_COL_CNT'][0] = 1;
        self['SEQ']['RESET_COL_CNT'][1] = 1;
        
        self['SEQ']['ADC_SYNC_50'][0] = 1;
        self['SEQ']['ADC_SYNC_50'][1] = 1;
        
        i = 0
        for row in range(16):
            for column in range(32):
                self['SEQ']['CLK_COL_50'][i] = 0
                i += 1
                self['SEQ']['CLK_COL_50'][i] = 1
                i += 1
                
            i += 1  
            self['SEQ']['ROW_RESET_50'][i] = 1;
            i += 1
            self['SEQ']['ROW_RESET_50'][i] = 1;
            i += 1
            i += 1
            
            for column in range(32):
                self['SEQ']['CLK_COL_50'][i] = 0
                i += 1
                self['SEQ']['CLK_COL_50'][i] = 1
                i += 1
                
            i += 1  
            self['SEQ']['CLK_ROW_50'][i] = 1
            i += 1
            self['SEQ']['CLK_ROW_50'][i] = 0
            i += 1
            i += 1
        
            self['SEQ'].set_size(i)
            self['SEQ'].write(i)

    def get_status(self):
        staus = {}
        staus['Time'] = time.strftime("%d %M %Y %H:%M:%S")
        staus['Hostname'] = socket.gethostname()

        staus['DVDD'] = {'voltage(V)': self['DVDD'].get_voltage(unit='V'), 'current(mA)':  self['DVDD'].get_current() }
        staus['AVDD'] = {'voltage(V)': self['AVDD'].get_voltage(unit='V'), 'current(mA)':  self['AVDD'].get_current() }
        staus['VNDIODE'] = {'voltage(V)': self['VNDIODE'].get_voltage(unit='V'), 'current(mA)':  self['VNDIODE'].get_current() }
        
        staus['VRESETP'] = {'voltage(V)': self['VRESETP'].get_voltage(unit='V'), 'current(mA)':  self['VRESETP'].get_current() }
        staus['VRESETN'] = {'voltage(V)': self['VRESETN'].get_voltage(unit='V'), 'current(mA)':  self['VRESETN'].get_current() }
        staus['FADC_VREF'] = {'voltage(V)': self['FADC_VREF'].get_voltage(unit='V'), 'current(mA)':  self['FADC_VREF'].get_current() }
        
        staus['IBP_CS_AMP'] = {'voltage(V)': self['IBP_CS_AMP'].get_voltage(unit='V'), 'current(mA)':  self['IBP_CS_AMP'].get_current() }
        staus['IBN_COL_DRV'] = {'voltage(V)': self['IBN_COL_DRV'].get_voltage(unit='V'), 'current(mA)':  self['IBN_COL_DRV'].get_current() }
        staus['IBP_OUT_SF'] = {'voltage(V)': self['IBP_OUT_SF'].get_voltage(unit='V'), 'current(mA)':  self['IBP_OUT_SF'].get_current() }
        
        return staus
        
    #@profile
    def take_single_data(self, row, col, reset_seq_width = 10, channel = 'AOUT50v2', adc_data = 1000, sample_start=45, sample_period=320, sample_sub_start=320, add_plot = True, show_info = True, set_seq = True):
        
        if set_seq:
            ps = self.single_pix_sel_seq(row,col,reset_seq_width)
            self['SEQ'].start()
        
            time.sleep(0.05) #stady state
        
        samples, syncs = self.take_adc_data(channel, adc_data)
        
        sdata_a = samples[sample_sub_start::sample_period]
        sdata_ax = range(sample_sub_start,len(samples),sample_period)

        sdata_b = samples[sample_start::sample_period]
        sdata_bx = range(sample_start,len(samples),sample_period)
        
        size = min(len(sdata_a), len(sdata_b)) # just make the size same

        #diff = map(operator.sub, sdata_a[0:size], sdata_b[0:size])
        diff = sdata_a[0:size] -  sdata_b[0:size]

        mean = np.mean(diff)
        stddev = np.std(diff)

        if show_info:
            print ('row=', row, 'col=' , col, " stdev:", stddev, 'samples:', len(diff) ,'mean:', mean)
        
        if add_plot:
            plt.plot(samples)
            plt.plot(sdata_ax, sdata_a, 'ro')
            plt.plot(sdata_bx, sdata_b, 'go')
        
        return mean, stddev, diff
