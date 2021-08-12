"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf

import numpy as np
def t_matrix(processed_sched, r_info, tau):
    # initialize rooms as fully available
    T_r = {room: np.ones((tau,len(cf.days))) for room in r_info.keys()}
    T_c = {}
    c_info = {}
    general_viol_courses = []
    
    for row in processed_sched.index:
        # if violated, add to dict
        if processed_sched.loc[row,'Violated']:
            c = processed_sched.loc[row,'Course ID']
            c_info[c] = {'enrl': processed_sched.loc[row, 'Effective Enrollment'],
                         'p':int(processed_sched.loc[row,'Course Priority']),
                         'Course':processed_sched.loc[row, 'Course'],
                         'Component':processed_sched.loc[row, 'Component'],
                         'Specialty':True}
            if processed_sched.loc[row,'Specialty Course']==0:
                general_viol_courses.append(c)
                c_info[c]['Specialty'] = False
            elif processed_sched.loc[row,'Specialty Course']!=1:
                raise Exception([processed_sched.loc[row,'Course ID'],
                                  processed_sched.loc[row,'Specialty Course']],
                                 'Specialty Course entry is not 0 or 1.')
            
            T_c[c] = np.zeros((tau,len(cf.days)))
        # if violated, add schedule to viol_courses, o.w. take from room_avail            
        course_start = int(processed_sched.loc[row, 'Start i'])
        course_end = int(processed_sched.loc[row, 'End i'])
        for j in range(len(cf.days)):
            if processed_sched.loc[row,cf.days[j]]==1: # for every day course meets
                for i in range(course_start, course_end): # for every time period
                    if processed_sched.loc[row,'Violated']: # course is in T_c
                        T_c[c][i,j] = 1
                    else: # room is taken by course
                        T_r[processed_sched.loc[row,'Room']][i,j] = 0

    return T_r, T_c, c_info, general_viol_courses