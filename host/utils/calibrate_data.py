import logging
import numpy as np

####
# This class is equal to the functions available in the dut but can be utilized without the dut
####
class data_calibration():
    def load_adc_calib(self, adc_ch):
        #try:
        calib = np.genfromtxt('./output/ADC_Calibration/data/'+adc_ch+'.csv', delimiter=',')
        calib = calib[1:]
        a, a_err, b, b_err = calib[0][0],calib[0][1],calib[1][0],calib[1][1]
        logging.info('Successfully loaded ADC calibratio for %s'%(adc_ch))    
        return a, a_err, b, b_err
        #except:
        logging.error('Calibration for %s not found! Please run LF_SFF_MIO_Calibrate_ADC.py!'%(adc_ch))
        return None, None, None, None
        
    def calibreate_data(self, data, adc_ch):
        a, a_err, b, b_err = self.load_adc_calib(adc_ch)
        if a:
            data = a*data+b
            data_err = np.std(data)
            return data, data_err
        else:
            logging.error('MISSING ADC calibration')
            exit