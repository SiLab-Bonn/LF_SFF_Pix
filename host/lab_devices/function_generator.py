from basil.dut import Dut

class function_generator(Dut):
    def load_dc_sweep_config(self, voltage_high):
        self['Pulser'].set_pulse_period(1000)
        self['Pulser'].set_voltage_high(voltage_high)
        self['Pulser'].set_voltage_low(voltage_high-0.002)
        self['Pulser'].set_enable(1)

    def load_ac_sweep_config(self, offset, amplitude, frequency):
        self['Pulser'].set_pulse_period(1/frequency)
        self['Pulser'].set_voltage_high(offset+amplitude/2)
        self['Pulser'].set_voltage_low(offset-amplitude/2)
        self['Pulser'].set_enable(1)
