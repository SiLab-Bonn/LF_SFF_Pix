# Application Scripts

# Requirements
1. Basil
2. LibUSB
3. pyvisa

Measurements:
- ```Script.py``` [command_line_options]: description
* ```LF_SFF_MIO_DAQ.py```: A rudimentary DAQ that allows the user to run all tests and set parameters manually. This will be upgraded to a proper prompt tool
* ```LF_SFF_MIO_DC_Sweep.py``` [AC/DC, load_data, --name]: Measure for different IBNs/IBPs the relation between V_IN and V_Out. Returns DC offset and DC Gain.
* ```LF_SFF_MIO_AC_Sweep.py``` [AC/DC, load_data, --name]: Measure for different IBNs/IBPs the relation between V_IN and V_Out (amplitudes) in depency of the input frequency
* ```LF_SFF_MIO_IR_LED.py``` [AC/DC, load_data, --name]: Investigates induced signals by a IR LED
* ```LF_SFF_MIO_PW_Investigation.py ```  [AC/DC, load_data, --name]: Investigates the behavior of the LF SFF AC sweep for different VRESET voltages
* ```LF_SFF_MIO_Reset_Probe.py ``` [AC/DC, load_data]: Investigates the V_Out behavior for different applied VRESET voltages, while RST=0
* ```bode_plot_analyzer.py ```: Utility that is used by ```LF_SFF_MIO_AC_Sweep.py``` to analyse the bode plots
