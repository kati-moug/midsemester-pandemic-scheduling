"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf
import priority
import estimate_enroll

import pandas as pd
import numpy as np

def room_data():
    room_df = pd.read_csv(cf.room_cap_file)
    r_info = {}
    general_rooms = []
    for row in room_df.index:
        rm = room_df.loc[row,'Room']
        
        if rm in r_info.keys():
            raise Exception(rm,'Multiple rows in capacity file with the'
                             +' same room.')
        if cf.round_new_cap_up:
            r_info[rm] = {'Capacity':int(np.ceil(cf.room_cap_prop
                                          *room_df.loc[row,'Max Capacity']))}
        else:
            r_info[rm] = {'Capacity':int(cf.room_cap_prop
                                            *room_df.loc[row,'Max Capacity'])}
        
        room_df.loc[row,'New Capacity'] = r_info[rm]['Capacity']
        r_info[rm]['Bldg'] = room_df.loc[row,'Bldg']
        if room_df.loc[row,'Type'] == 'General':
            general_rooms.append(rm)
    room_df.to_excel(cf.w_folder+'new_room_capacity.xlsx',index=False)
    return r_info, general_rooms
        
def schedule(r_info):
    processed_sched = pd.read_csv(cf.schedule_file)
    
    # add datetime column to calculate tau
    for time in ['Start ','End ']:
        processed_sched[time+'DT'] = pd.to_datetime(processed_sched[time+'Time'],
                                                format='%H:%M:%S')
        
    # find length of day and total number of discrete units, tau
    start = processed_sched['Start DT'].min()
    end = processed_sched['End DT'].max()
    minutes = (end-start).seconds/60
    tau = int(minutes/cf.ell)
    
    for row in processed_sched.index:  
        # add discrete time unit index for start time and end time
        for col in ['Start ','End ']:
            processed_sched.loc[row,col+'i'] = int(
                (processed_sched.loc[row,col+'DT']-start).seconds/60/cf.ell)
        days = processed_sched.loc[row,'Days'].split('/')
        # add column for each day - 1 if course meets then, empty otherwise
        for d in days:
            processed_sched.loc[row,d] = 1
            
    # use current enrollment estimate only
    if cf.estimate_enroll == 'None':
        processed_sched['Estimate Enrl'] = processed_sched['Effective Enrollment']
        processed_sched['Estimate Enrl Method'] = 'Current Enrollment Only'
    
    # estimate enrollment using Fall 2019 data
    else:
        if cf.estimate_enroll == 'f19max_rcr':
            processed_sched = estimate_enroll.f19_rcr(processed_sched) 
        elif cf.estimate_enroll == 'rcr':
            processed_sched = estimate_enroll.rcr(processed_sched)
            
        # for final enrollment, take max of current enrollment and estimate
        processed_sched = processed_sched.rename(
            columns={'Effective Enrollment': 'Orig Effective Enrl'})
        processed_sched['Effective Enrollment'] = processed_sched[
            ['Orig Effective Enrl', 'Estimate Enrl']].max(axis=1)
    
    # add course priority column
    if cf.course_priority_option == 'level_component':
        processed_sched = priority.level_component(processed_sched)
        
    # add new room capacities and violated column
    for room in r_info.keys():
        processed_sched.loc[processed_sched['Room']==room,
                    'New Capacity'] = r_info[room]['Capacity']
    processed_sched['Violated'] = 0
    processed_sched.loc[processed_sched['Effective Enrollment']>processed_sched['New Capacity'],
                'Violated'] = 1
    
    # save schedule
    processed_sched.to_csv(cf.w_folder+'old_schedule_input.csv',index=False)
    return processed_sched, tau
    
def specialty_permissions(c_info):
    df = pd.read_csv(cf.specialty_room_file)
    ind = []
    for c in c_info.keys():
        rooms = []
        for c_s in c_info[c]['Course'].split('//'):
            c_df = df[(df['Course']==c_s)&
                  (df['Component']==c_info[c]['Component'])]
            
            if len(c_df.index)>0:
                rooms += list(set(c_df['Room']))
                for rm in rooms:
                    ind.append((c,rm))
        if c_info[c]['Specialty'] and len(rooms)==0:
            raise Exception('Specialty course',c,'does not have any rooms',
                            c_df)
    return ind
        
    
    
        