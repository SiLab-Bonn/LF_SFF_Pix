############
# Script that creates a directory tree
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
                'name': 'reset_probe',
                'sub':[]
            },{
                'name': 'scan_vreset',
                'sub':[]
            }]
        },{
            'name': 'bode_plot',
            'sub':[{
                'name':'AC',
                'sub':[]
            },{
                'name':'AC_reset_pulse',
                'sub':[]
            },{
                'name':'AC_R_on',
                'sub':[]
            },{
                'name':'DC',
                'sub':[]
            }
                ]
        }]
    }
    create_dir(root_dir, dir_dict)
