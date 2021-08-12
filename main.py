"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf
import read
import calculate
import model

import pandas as pd
import os

# make result folder if needed
if not os.path.exists(cf.w_folder):
    os.mkdir(cf.w_folder)

# save input parameters
with open('config.py') as file:
    config_data = file.read()
    
with open(cf.w_folder+'input_parameters.txt','w') as file:
    file.write(config_data)
    
# read and process data
r_info, gen_r = read.room_data()

processed_sched, tau = read.schedule(r_info)

# get T matrices and violated course info, based on sched & capacity
T_r, T_c, c_info, gen_c = calculate.t_matrix(processed_sched, r_info, tau)

# get indices of allowed course-room assignments
index = read.specialty_permissions(c_info) # specialty room permissions
index += [(c,rm) for c in gen_c for rm in gen_r] # general

# dataframes to store results for all tests, for comparison
results = pd.DataFrame()
scheds = pd.DataFrame()

for test in cf.tests:
    p_wt = test['p wt']
    
    # in current code, this is the same for all tests
    in_person_hybrid_threshold = test['in person hybrid threshold']
    
    # naming convention based on priority wt as only changing parameter.
    # for different kind of tests, change folder naming convention
    folder = cf.w_folder+'Priority_'+test['p name']+'/'
    
    if not os.path.exists(folder):
        os.mkdir(folder)
        
    results, scheds = model.optimize(T_r, T_c, c_info, tau, 
                                 r_info, in_person_hybrid_threshold, 
                                 p_wt, results, index, processed_sched, 
                                 scheds, test['p name'], folder)
    
    # rewrite after each test update. 
    # if code is interrupted, partial results are saved
    results.to_csv(cf.w_folder+'performance.csv',index=False)
    scheds.to_csv(cf.w_folder+'all_schedules.csv',index=False)
