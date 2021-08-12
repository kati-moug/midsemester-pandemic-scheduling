"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf

import pandas as pd
import numpy as np

def f19_rcr(schedule_df):
    f19 = pd.read_csv(cf.f19_file)
    schedule_df['Room Cap Request'] = schedule_df['Room Cap Request'].astype(str)
    for row in schedule_df.index:
        courses = schedule_df.loc[row,'Course'].split('//')
        cmpnt = schedule_df.loc[row,'Component']
        method = 'f19 max'
        enroll, f19_sections = 0, []
        for course in courses:
            c_enroll, c_list = get_course_enroll(f19, course, cmpnt)
            if c_enroll > enroll:
                enroll, f19_sections = c_enroll, c_list
        # if a room cap req is made that requests smaller enrollment this
        # year, honor it (consider max request if cross listed course)
        rcrs = schedule_df.loc[row,'Room Cap Request'].split('//')
        rcr = max([int(v) for v in rcrs])
        if rcr > 0 and rcr < enroll:
            enroll, f19_sections = 0, []
        if enroll==0 and rcr > 0: # if no historical estimate, take RCR
            enroll, method = rcr, 'max rcr'
        # if RCR is 0 and enroll is 0 or Capacity < enrollment, make capacity
        elif enroll==0 or enroll > schedule_df.loc[row,'Capacity']:
            enroll, method = schedule_df.loc[row,'Capacity'],'Capacity'

        schedule_df.loc[row,'Estimate Enrl'] = enroll
        schedule_df.loc[row,'Estimate Enrl Method'] = method
        schedule_df.loc[row,'Estimate Enrl Crses'] = '//'.join(f19_sections)
    return schedule_df

def get_course_enroll(df, course, cmpnt, how='max'):
    c_df = df[(df['Course']==course)&(df['Component']==cmpnt)]
    if c_df.empty:
        return 0, []
    if how=='max':
        return c_df['Section Enrl'].max(),[str(x) for x in c_df.index] 

def rcr(schedule_df):
    for row in schedule_df.index:
        vals = schedule_df.loc[row,'Room Cap Request'].split('//')
        
        # find smallest nonzero rcr (or 100000 if does not exist)
        val = min([int(v) for v in vals if int(v)>0]+[100000])
        method = 'min nonzero rcr'
        if val == 100000:
            val = schedule_df.loc[row,'Capacity']
            method='Capacity'
        schedule_df.loc[row,'Estimate Enrl'] = val
        schedule_df.loc[row,'Estimate Enrl Method'] = method
    return schedule_df