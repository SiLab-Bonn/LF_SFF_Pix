def bode_plot_schematic(hack=False):
    if not hack:
        print('''
                _____________ Function Generator________
                |                        |               |
                | PIX_INPUT              | RS232         |
-----------------------                  |               |
| MIO | GPIO | LF_SFF |      MIO------Computer           |
-----------------------           USB    |               |
      Pixel 10  |                        | RJ45          |
      Matrix 1  |                        |               |
                |______________________Oszi______________|
                            CH2                   CH1
        ''')
    else:
        print('''      
                   __R__
                ___|___|_______ Function Generator________
                |                        |               |
                | PIX_INPUT              | RS232         |
-----------------------                  |               |
| MIO | GPIO | LF_SFF |      MIO------Computer           |
-----------------------           USB    |               |
      Pixel 10  |                        | RJ45          |
      Matrix 1  |                        |               |
                |______________________Oszi______________|
                            CH2                   CH1
        ''')

def reset_probe_schematic():
    print('''
-----------------------                               
| MIO | GPIO | LF_SFF |       MIO------Computer           
-----------------------             USB    |               
        Pixel 10  |                        | RJ45          
        Matrix 1  |                        |               
                  |______________________Oszi
                            CH2              
    ''')
