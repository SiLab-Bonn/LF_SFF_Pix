# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------


import time
from basil.dut import Dut
import socket
import numpy as np


class LF_SFF_MIO(Dut):
    
    def boot_seq(self):
        for i in range(4):
            self['CONTROL']['LED'] = 0x01 << i
            self['CONTROL'].write()
            time.sleep(0.1)
        for i in range(0,2):
            self['CONTROL']['LED'] = 0x1f
            self['CONTROL'].write()
            time.sleep(0.5)
            self['CONTROL']['LED'] = 0x00
            self['CONTROL'].write()
            time.sleep(0.5)
        self['CONTROL']['LED'] = 0x1f
        self['CONTROL'].write()


    def get_status(self):
            staus = {}
            staus['Time'] = time.strftime("%d %M %Y %H:%M:%S")
            staus['Hostname'] = socket.gethostname()

            staus['VDD'] = {'voltage(V)': self['VDD'].get_voltage(unit='V'), 'current(mA)':  self['VDD'].get_current() }
            staus['IBN'] = {'voltage(V)': self['IBN'].get_voltage(unit='V'), 'current(mA)':  self['IBN'].get_current() }
            staus['IBP'] = {'voltage(V)': self['IBP'].get_voltage(unit='V'), 'current(mA)':  self['IBP'].get_current() }
            staus['VRESET'] = {'voltage(V)': self['VRESET'].get_voltage(unit='V'), 'current(mA)':  self['VRESET'].get_current() }

            return staus

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