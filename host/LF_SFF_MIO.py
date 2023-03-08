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
        for i in range(3):
            self['CONTROL'] = 0x02 << i
            self['CONTROL'].write()
            time.sleep(0.1)
        self['CONTROL']['RESET'] = 0x1 
        self['CONTROL'].write()
        time.sleep(0.1)
        for i in range(0,2):
            self['CONTROL'] = 0x1f
            self['CONTROL'].write()
            time.sleep(0.2)
            self['CONTROL'] = 0x00
            self['CONTROL'].write()
            time.sleep(0.2)
        self['CONTROL'] = 0x00
        self['CONTROL'].write()


    def load_defaults(self, VDD = 1.2,VDD_Unit = 'V',
                        VRESET = 1.2, VRESET_Unit = 'V',
                        opAMP_offset = 0, opAMP_offset_Unit = 'V',
                        IBN =  100, IBN_Unit = 'uA', 
                        IBP = -10, IBP_Unit = 'uA',
                        print_out=False):
        # Voltages
        #VDD = 1.2
        #VDD_Unit = 'V'
        #VRESET = 1.1
        #VRESET_Unit = 'V'
        #opAMP_offset = 0
        #opAMP_offset_Unit = 'V'

        # Currents
        #IBN =  100 
        #IBN_Unit = 'uA'
        #IBP = 10
        #IBP_Unit = 'uA'

        self['VDD'].set_voltage(VDD, unit=VDD_Unit)
        self['VDD'].set_enable(True)

        self['IBN'].set_current(IBN, unit=IBN_Unit)

        self['IBP'].set_current(IBP, unit=IBP_Unit)

        self['VRESET'].set_voltage(VRESET, unit=VRESET_Unit)

        self['opAMP_offset'].set_voltage(opAMP_offset, unit=opAMP_offset_Unit)
        
        if print_out:
            print('opAMP_offset:', self['opAMP_offset'].get_voltage(unit='V'), VRESET_Unit, self['opAMP_offset'].get_current(), 'uA')
            print('VRESET:', self['VRESET'].get_voltage(unit='V'), VRESET_Unit, self['VRESET'].get_current(), 'uA')
            print('IBP:', self['IBP'].get_voltage(unit='V'), 'V', self['IBP'].get_current(), 'uA')
            print('IBN:', self['IBN'].get_voltage(unit='V'), 'V', self['IBN'].get_current(), 'uA')
            print('VDD:', self['VDD'].get_voltage(unit='V'), 'V', self['VDD'].get_current(), 'mA')


    def get_status(self, print_status=True):
            status = {}
            status['Time'] = time.strftime("%d.%M.%Y %H:%M:%S")
            status['Hostname'] = socket.gethostname()

            status['VDD'] = {'voltage(V)': self['VDD'].get_voltage(unit='V'), 'current(mA)':  self['VDD'].get_current() }
            status['IBN'] = {'voltage(V)': self['IBN'].get_voltage(unit='V'), 'current(mA)':  self['IBN'].get_current() }
            status['IBP'] = {'voltage(V)': self['IBP'].get_voltage(unit='V'), 'current(mA)':  self['IBP'].get_current() }
            status['VRESET'] = {'voltage(V)': self['VRESET'].get_voltage(unit='V'), 'current(mA)':  self['VRESET'].get_current() }
            if print_status:
                print_digits = 6
                print('Status ', time.strftime("%d.%M.%Y %H:%M:%S"))
                print('VDD:\t\t', str(self['VDD'].get_voltage(unit='V'))[:print_digits], 'V', str(self['VDD'].get_current())[:print_digits], 'mA')
                print('ISCR1 IBN:\t', str(self['IBN'].get_voltage(unit='V'))[:print_digits], 'V', str(self['IBN'].get_current(unit='uA'))[:print_digits], 'uA')
                print('ISRC0 IBP:\t', str(self['IBP'].get_voltage(unit='V'))[:print_digits], 'V', str(self['IBP'].get_current(unit='uA'))[:print_digits], 'uA')
                print('VRESET:\t\t', str(self['VRESET'].get_voltage(unit='V'))[:print_digits], 'V', str(self['VRESET'].get_current())[:print_digits], 'uA')
                print('opAMP_offset:\t', str(self['opAMP_offset'].get_voltage(unit='V'))[:print_digits], 'V', str(self['opAMP_offset'].get_current())[:print_digits], 'uA')
                print('\n')
            return status

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