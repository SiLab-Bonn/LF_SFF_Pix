from basil.dut import Dut

class function_generator(Dut):
    def load_dc_sweep_config(self, voltage_high):
        self['Pulser'].set_pulse_period(1000)
        self['Pulser'].set_voltage_high(voltage_high)
        self['Pulser'].set_voltage_low(voltage_high-0.002)
        self['Pulser'].set_enable(1)

    def load_ac_sweep_config(self, offset, amplitude, frequency):
        self['Pulser'].set_sin(frequency)
        self['Pulser'].set_voltage_high(offset+amplitude/2)
        self['Pulser'].set_voltage_low(offset-amplitude/2)
        self['Pulser'].set_enable(1)
        
    def load_IR_LED_config(self, voltage_high, frequency, pulse_width):
        self['Pulser'].set_pulse(frequency)
        self['Pulser'].set_pulse_width(pulse_width)
        self['Pulser'].set_voltage_high(voltage_high)
        self['Pulser'].set_voltage_low(0)
        self['Pulser'].set_enable(1)    
        self['Pulser'].set_burst_state('ON')
        self['Pulser'].set_burst_mode('TRIGgered')
        self['Pulser'].set_trigger_source('BUS')

    def send_trigger(self):
        self['Pulser'].trigger()