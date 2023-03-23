import numpy as np
def save_sweep(IBX, IBX_name, output_path, iterator, iterator_err, IBX_VIN, IBX_VIN_err, IBX_VOUT, IBX_VOUT_err):
    for j in range(0, len(IBX)):
        file_name = IBX_name+'_'+str(IBX[j])+'.csv'
        with open(output_path+file_name, 'w') as f:
                f.write('frequency, frequency_error, IBX_VIN, IBX_VIN_err, IBX_VOUT, IBX_VOUT_err\n')
                for i in range(0, len(iterator)):
                    f.write(str(iterator[i])+', '+str(iterator_err[i]*0.05)+', '+str(np.abs(IBX_VIN[j][i]))+', '+str(np.abs(IBX_VIN_err[j][i]))+', '+str(np.abs(IBX_VOUT[j][i]))+', '+str(np.abs(IBX_VOUT_err[j][i])))
                    f.write('\n')

def load_sweep(data_path, IBX, IBX_name='IBN'):
    IBX_VIN = [[] for i in range(0, len(IBX))]
    IBX_VIN_err = [[] for i in range(0, len(IBX))]
    IBX_meas = [[] for i in range(0, len(IBX))]
    IBX_VOUT = [[] for i in range(0, len(IBX))]
    IBX_VOUT_err = [[] for i in range(0, len(IBX))]
    for i in range(0, len(IBX)):
        data = np.genfromtxt(data_path+IBX_name+'_'+str(IBX[i])+'.csv', delimiter=',')
        IBX_VIN[i] = data[1:,2]
        IBX_VIN_err [i] = data[1:,3]
        IBX_VOUT[i] = data[1:,4]
        IBX_VOUT_err[i] = data[1:,5]
    return IBX_VIN, IBX_VIN_err, IBX_VOUT, IBX_VOUT_err


def save_data(data, output_path, header=None):
    width = len(data)
    try:
        length = len(data[0])
    except:
        length = None
    with open(output_path, 'w') as f:
        if header:
            f.write(header+'\n')
        if length:
            for i in range(0, length):
                line = ''
                for j in range(0, width):
                    if j != width-1:
                        line = line + str(data[j][i]) + ', '
                    else:
                        line = line + str(data[j][i])
                f.write(line+'\n')
        else:
            line=''
            for j in range(0, width):
                if j != width-1:
                    line = line + str(data[j]) + ', '
                else:
                    line = line + str(data[j])
            f.write(line+'\n')

def success_message(data_path, image_path):
    print('###### Data Analysis successfull ######')
    print('Data has been stored in:', data_path)
    print('Plots have been stored in:', image_path)
    print()

def success_message_data_taking():
    print('###### Measurement successfull ######')