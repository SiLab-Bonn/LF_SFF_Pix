import sys

def initialize_measurement(measurement):
    if 'DC' in sys.argv[1:]:
        chip_version='DC'
        image_path = './output/'+measurement+'/DC/'
        data_path = image_path+'data/'
    else:
        chip_version = 'AC'
        image_path = './output/'+measurement+'/AC/'
        data_path = image_path+'data/'
    load_data = False
    if 'load_data' in sys.argv[1:]:
        load_data = True  
    return load_data, chip_version, image_path, data_path