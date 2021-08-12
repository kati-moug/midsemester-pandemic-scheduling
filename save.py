"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf

import numpy as np
import pandas as pd

def schedule(df, r_info, folder):
    # get values to convert discrete time units to datetime in viz_df
    first_i = df['Start i'].min()
    first_DT = df.loc[df['Start i']==first_i]['Start DT'].iloc[0]
    
    df.loc[df['Specialty Course']==1,'Course Type'] = "Specialty"
    df.loc[df['Specialty Course']==0,'Course Type'] = "General"
    
    
    for l in cf.ug_levels.keys():
        df.loc[df[cf.ug]==l,'Course Level'] = str(cf.ug_levels[l][0])+'-'+str(
            cf.ug_levels[l][-1]) 
    df.loc[df['Instr Mode']=='Online','Room'] = 'Online'
    for row in df.index:
        if df.isna().loc[row,'Room']:
            df.loc[row,'Room']=df.loc[row,'Orig Room']
            df.loc[row,'Instr Mode']='In Person'
        df.loc[row,'Time']='/'.join([str(x) for x in 
                range(int(df.loc[row,'Start i']),int(df.loc[row,'End i']))])
    df = df[['Objective','Priority','Course','Section','Component','Subject',
             'Orig Room','Course Type', 'Course Level','Days','Start Time',
             'End Time','Course Priority','Estimate Enrl',
             'Estimate Enrl Method','Effective Enrollment','Instr Mode','Room',
             'Time']]
    # save a file with one course per row for analysis purposes
    df.to_excel(folder+'new_schedule.xlsx',index=False)
    
    # save a file with all subjects for distribution comparison
    sub_df = df.assign(Subject = df['Subject'].str.split('//')).explode('Subject')
    sub_df.to_excel(folder+'assignment_by_subject.xlsx',index=False)

    # save a file with a random subject for the course schedule viz
    viz_df = df
    viz_df = viz_df.reset_index()
    for row in viz_df.index:
        subs = viz_df.loc[row,'Subject'].split('//')
        i = np.random.randint(len(subs))
        viz_df.loc[row,'Subject']=subs[i]
    
    viz_df = viz_df.assign(Room = viz_df['Room'].str.split('+')).explode('Room')
    viz_df['Room'] = viz_df['Room'].str.strip()
    for rm in list(viz_df['Room']):
        if rm != 'Online':
            viz_df.loc[viz_df['Room']==rm,'Bldg'] = r_info[rm]['Bldg']
    viz_df = viz_df.assign(Days = viz_df['Days'].str.split('/')).explode('Days')
    viz_df = viz_df.assign(Time=viz_df['Time'].str.split('/')).explode('Time')
    viz_df = viz_df.reset_index()
    for row in viz_df.index:
        time = first_DT + (int(viz_df.loc[row,'Time'])-first_i)*pd.Timedelta(
            value=cf.ell, unit='m')
        time_h, time_m = time.hour, time.minute
        if time_h >= 13:
            time_h -= 12
        if time_m == 0:
            time_m = '00'
        else:
            time_m = str(int(time_m))
        viz_df.loc[row,'Final Time']=str(int(time_h))+':'+time_m
    viz_df.to_excel(folder+'input_for_Tableau_course_schedule.xlsx',index=False)
    
    return df
    