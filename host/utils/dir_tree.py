############
# Script that creates a directory tree for the measurement outputs
############

import os

def create_dir(curr_dir, sub_conf):
    curr_dir = curr_dir+'/'+sub_conf['name']
    # create dir
    print(curr_dir)
    os.mkdir(curr_dir)
    for sub in sub_conf['sub']:
        create_dir(curr_dir, sub)


def create_dir_tree():
    root_dir ='.'
    dir_dict={
        'name':'output',
        'sub': [{
            'name': 'reset_probe',
            'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
        },{
        'name': 'DC_sweeps',
        'sub':[{
                'name':'AC',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            },{
                'name':'comparison',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            },{
                'name':'DC',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            }]
        },{
            'name': 'AC_sweeps',
            'sub':[{
                'name':'AC',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            },{
                'name':'AC_reset_pulse',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            },{
                'name':'AC_R_on',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            },{
                'name':'DC',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            }]
        },{
            'name': 'IR_LED',
            'sub':[{
                'name':'AC',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            },{
                'name':'DC',
                'sub':[{
                    'name':'data',
                    'sub':[]
                    }]
            }]
        }]
    }

    create_dir(root_dir, dir_dict)
