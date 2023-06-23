import yaml
from lab_devices.LF_SFF_MIO import LF_SFF_MIO
import utils.schematics as sch
#import LF_SFF_MIO_bode_plot as bode_plot
#import LF_SFF_MIO_Reset_Probe as reset_probe
import utils.dir_tree as dir_tree
print('''
            ..::^^^:..                  |      
        .~7?JJJJJJJJJJ?7~:              |
     .~?YYJJJJJJJJJJJJJJYYJ7:           |
   .!JYYJJJJJJJJYJJJJJJJJJJJY?:         |       Welcome to the LFoundry Small Fill Factor Data Aquisition Tool!
  :JJJ?~..     .:~JJJJ! .. :JJY!        |
 ^YJJ7    .::.    .JJY~    .JJJY7       |       Please verify that your setup looks like:
.JJJY:    :!7?^:^^^?JY~    .JJJJY~      |   
!JJJJ?.        .:~?JJY~    .JJJJJ?      |             USB   ----------------------
?JJJJYY?~:.        ~JY~    .JJJJJJ.     |       PC<------->| MIO | GPIO | LF_SFF |
7JJJ?:::.:JYJ?^     JY~    .JJJJJJ      |                   ----------------------
:JJJJ.    .^~^.    ~JY~    .JJJJY~      |
 ~YJJJ~.         :7JJJ~    .JJJJ?       |       If you have any problems, feel free to create an issue on github:   
  ~YJJJJ??77!77?JYJJJJJ?????JJY7        |       https://github.com/SiLab-Bonn/LF_SFF_Pix
   :?YJJJJJJJJJJJJJJJJJJJJJJYJ^         |
     :7JJJJJJJJJJJJJJJJJJJJ?^           |

 ''')

def schematic_check():
    while True:
                schematic_valid = input('Setup is as shown [yes]: ')
                if(schematic_valid == 'yes' or schematic_valid == 'y'):
                    break

commands = {'help':'Prints out all commands',
            'init':'Creates requiered folder structure [first run]',
            'flash':'Flashes firmware',
            'defaults':'Loads the LF_SFF defaults',
            'set':'Sets a channel X to the Value Y',
            'get':'Gets a value of a channel',
            'run':'Runs a preprogrammed test X',
            'exit':'Exits the program'
            }

tests = {'reset_probe':'Reset Probe',
         'bode_plot':'Bode Plot',
         'bode_plot_hack':''
         }


channels ={'VDD':[0.0,1.8],
    'IBP':[-1,-10],
    'IBN':[10,100],
    'VRESET':[0.0,1.8],
    'RESET':[0,1],
    'opAMP_offset':[0,5]}

units ={'VDD':'V',
    'IBP':'uA',
    'IBN':'uA',
    'VRESET':'V',
    'RESET':'d',
    'opAMP_offset':'V'}

stream = open("./lab_devices/LF_SFF_MIO.yaml", 'r')
cnfg = yaml.load(stream, Loader=yaml.Loader)


while True:
    userinput = input('> ')
    inputs = userinput.split()

    if 'help' == inputs[0]:
        print('The following commands are available:')
        for cmd in commands:
            if len(cmd)<=3:
                print(cmd,':  \t\t', commands[cmd])
            else:
                print(cmd,':  \t', commands[cmd])
    if 'init' == inputs[0]:
        try:
            dir_tree.create_dir_tree()
        except:
            print('Folder structure already exists. Please delete the "outputs" folder and rerun this command')
    if 'flash' == inputs[0]:
        try:
            dut = LF_SFF_MIO(cnfg)
            dut.init()
            dut.boot_seq()
            dut.load_defaults(print_out=False)
            dut.set_acquire_state('RUN')
        except:
            print('INITIALIZATION ERROR! PLEASE VERIFY THAT THE DUT IS CONNECTED PROPERLY')
    
    if 'exit' == inputs[0]:
        break

    if 'get' == inputs[0]:
        if len(inputs)>=2:
            channel = inputs[1]
            if inputs[1]=='RESET':
                print('See LED4')
            if inputs[1] in channels:
                if 'V' in units[channel]:
                    print(dut[channel].get_voltage(unit=units[channel]), units[channel])
                if 'uA' in units[channel]:
                    print(dut[channel].get_current(unit=units[channel]), units[channel])

    if 'set' == inputs[0]:
        channel = inputs[1]
        value =  float(inputs[2])
        if (len(inputs)== 1 or len(inputs)>=4):
            print('Wrong use of command: set channel value')
        else:
            if inputs[1] in channels and len(inputs)>=3:
                if (value >= channels[channel][0] and value <= channels[channel][1]):
                    if channel == 'RESET':
                        if value==1:
                            dut['CONTROL']['RESET']=0x1
                            print(channel+' set to 1')
                        else:
                            dut['CONTROL']['RESET']=0x0
                            print(channel+' set to 0')
                        dut['CONTROL'].write()
                    else:
                        if 'V' in units[channel]:
                            dut[channel].set_voltage(value, unit=units[channel])
                        if 'uA' in units[channel]:
                            dut[channel].set_current(value, unit=units[channel])
                        print(channel+' set to '+str(value)+units[channel])        
                else:
                    print("WARNING! Value out of Range! Value didn't change")
            else:
                print('Channel and/or input not found')
    
    if 'run'==inputs[0]:
        try:
            test = inputs[1]
        except:
            test = None
        if(test in tests):
            print('Please verify that your setup looks like:\n')
            if test == 'reset_probe':
                sch.reset_probe_schematic()
                schematic_check()
                reset_probe.reset_probe()
            if test == 'bode_plot':
                sch.bode_plot_schematic()
                schematic_check()
            if test == 'bode_plot_hack':
                sch.bode_plot_schematic(hack=True)
                schematic_check()
            
            
        else:
            print('Test unknwn or not given. The following tests are available:')
            for i in tests:
                print(i,': ', tests[i])

    if inputs[0] not in commands:
        print('Command not found')
