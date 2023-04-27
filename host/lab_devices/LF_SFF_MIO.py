# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------


import time
from basil.dut import Dut
import socket
import numpy as np
import time
import os 

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
                        DIODE_HV = 0.2, DIODE_HV_Unit = 'V',
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
        self['DIODE_HV'].set_voltage(DIODE_HV, unit=DIODE_HV_Unit)

        if print_out:
            print('opAMP_offset:', self['opAMP_offset'].get_voltage(unit='V'), VRESET_Unit, self['opAMP_offset'].get_current(), 'uA')
            print('VRESET:', self['VRESET'].get_voltage(unit='V'), VRESET_Unit, self['VRESET'].get_current(), 'uA')
            print('IBP:', self['IBP'].get_voltage(unit='V'), 'V', self['IBP'].get_current(), 'uA')
            print('IBN:', self['IBN'].get_voltage(unit='V'), 'V', self['IBN'].get_current(), 'uA')
            print('VDD:', self['VDD'].get_voltage(unit='V'), 'V', self['VDD'].get_current(), 'mA')
            print('DIODE_HV:', self['DIODE_HV'].get_voltage(unit='V'), 'V', self['DIODE_HV'].get_current(), 'mA')


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

    def reset(self, sleep=0.01):
        self['CONTROL']['RESET'] = 0x1 
        self['CONTROL'].write()
        time.sleep(sleep)
        self['CONTROL']['RESET'] = 0x0
        self['CONTROL'].write()
    
    def load_config(self, config_path):
        limits = {'VDD': [1.5, 'V'],
            'VRESET': [1.1, 'V'],
            'IBN': [100, 'uA'],
            'IBP':[-10, 'uA'],
            'DIODE_HV': [0.5, 'V']}
        config = np.genfromtxt(config_path, delimiter=',',dtype='str')[1:]
        print('Loading config: ')
        for conf in config:
            if float(conf[1])<=limits[conf[0]][0] and limits[conf[0]][1] in conf[2]:
                if 'A' in conf[2]:
                    self[conf[0]].set_current(float(conf[1]), unit=conf[2])
                    print('Set ',conf[0], ' = ',  round(self[conf[0]].get_current(unit=conf[2]),2), ' ', conf[2])
                elif 'V' in conf[2]:
                    self[conf[0]].set_voltage(float(conf[1]), unit=conf[2])
                    print('Set ', conf[0], ' = ', round(self[conf[0]].get_voltage(unit=conf[2]),2), ' ', conf[2])
    
    def init_adc(self, howmuch=10000):
        self['DATA_FIFO'].reset()
        self.howmuch = howmuch
        self.nmdata_buffer = []

        for ch in ['OUT_0', 'OUT_1', 'OUT_2', 'OUT_3']:
            self[ch].reset()
            self[ch].set_data_count(howmuch)
            self[ch].set_align_to_sync(False)
            self[ch].set_single_data(1)

            
    def start_adc(self):
        for i in range(10):
            pattern = 10 + i * 100
            self['fadc_conf'].enable_pattern(pattern)
        for ch in ['OUT_0', 'OUT_1', 'OUT_2', 'OUT_3']:  
            self[ch].set_en_trigger('1')

            self[ch].start()

    def stop_adc(self):
        self['DATA_FIFO'].reset()
        for ch in ['OUT_0', 'OUT_1', 'OUT_2', 'OUT_3']:        
            self[ch].reset()


    def calibrate_adc(self):#WIP
        user_input = input('Enable external voltage source and enter current max. voltage in V: ')
        V_max = float(user_input)
        print(V_max)
    
    def read_raw_adc(self, nSamples, adc_ch):
        self['sram'].reset()
        self[adc_ch].reset()
        self[adc_ch].set_delay(10)
        self[adc_ch].set_data_count(nSamples)
        self[adc_ch].set_single_data(True)
        self[adc_ch].set_en_trigger(False)
        time.sleep(2)

        self[adc_ch].start()
        while not self[adc_ch].is_done():
            pass

        lost = self[adc_ch].get_count_lost()
        data = self['sram'].get_data() 
        data = data & 0x3fff
        return data

    def get_adc(self):
        pass
        '''self['ADC_REF'].set_voltage(0.5, unit='V')
        self.start_adc()
        single = False
        nmdata = np.array([])
        i=0
        while not (self['OUT_0'].is_done() and self['OUT_1'].is_done() and self['OUT_2'].is_done() and self['OUT_3'].is_done() and self['DATA_FIFO'].get_fifo_size()==0):
            print(self['OUT_0'].is_done(), self['OUT_1'].is_done() ,self['OUT_2'].is_done(),self['OUT_3'].is_done(), self['DATA_FIFO'].get_fifo_size())
            nmdata = np.append(nmdata, self['DATA_FIFO'].get_data())
            i = i + 1
            print(i)
                     
        
        print('out of while')
        val1 = nmdata# np.bitwise_and(nmdata, 0x00003fff)
        #vals = np.right_shift(np.bitwise_and(nmdata, 0x10000000), 28)
        #valc = np.right_shift(np.bitwise_and(nmdata, 0x60000000), 29)

        #if(not single):
        #   val0 = np.right_shift(np.bitwise_and(nmdata, 0x0fffc000), 14)
            #val1 = np.reshape(np.vstack((val0, val1)), -1, order='F')
        # unused variable sync
#             sync = np.reshape(np.vstack((vals, vals)), -1, order='F')
        #    valc = np.reshape(np.vstack((valc, valc)), -1, order='F')
        # return val1
        #val = np.empty([2, len(val1) >> 1], dtype=np.int32)
        #for i in [0, 1]:
        #    val0 = val1[valc == i]
        #    if len(val[i, :]) == len(val0):
        ##        val[i, :] = val1[valc == i]
        #    elif len(val[i, :]) < len(val0):
        #        val[i, :] = val1[valc == i][:len(val[i, :])]
        #        # print "WARN data size: all=",len(val1),"ch%d"%i,len(val[i,:]),"dat=",len(val0)
        #    else:
        #        val[i, :len(val0)] = val1[valc == i]
        #        val[i, len(val0):] = 0
        #        # print "WARN data size: all=",len(val1),"ch%d"%i,len(val[i,:]),"dat=",len(val0)
        #print('val')
        #for val in val1:
        #    print(hex(int(val)))
        print([hex(int(i)) for i in val1])
        return val1'''
    
