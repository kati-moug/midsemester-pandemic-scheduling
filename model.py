"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf
import save
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

def optimize(T_r, T_c, c_info, tau, r_info, in_person_hybrid, p_wt, 
             all_results, ind, old_schedule, all_schedules,
             p_name, folder):
    all_courses = T_c.keys()
    all_rooms = T_r.keys()

    m = gp.Model(name='Scheduling Update')
    m.setParam('OutputFlag',0)
    m.setParam('TimeLimit',cf.time_limit)
    
    x = m.addVars(ind, name='x', vtype=GRB.BINARY)
    y = m.addVars(ind, name='y', vtype=GRB.BINARY)
    
    if cf.enroll_obj:
        m.setObjective(gp.quicksum(c_info[c]['enrl']*p_wt[c_info[c]['p']]
                                   *(x[c,rm]+.5*y[c,rm]) 
                               for (c,rm) in ind), GRB.MAXIMIZE)
        obj = 'Maximize In Person Enrollment'
    else:
        m.setObjective(gp.quicksum(p_wt[c_info[c]['p']]*(x[c,rm]+.5*y[c,rm]) 
                               for (c,rm) in ind), GRB.MAXIMIZE)
        obj = 'Maximize In Person Courses'

    for i in range(tau):
        for j in range(len(cf.days)):
            m.addConstrs(gp.quicksum(T_c[c][i,j]*
                (x[c,rm]+y[c,rm]) for (c,r) in ind if r==rm)
                             <= T_r[rm][i,j] for rm in all_rooms)
    for (c, rm) in ind:
        m.addConstr(np.floor(.5*c_info[c]['enrl'])*y[c,rm]<= r_info[rm]['Capacity']) 
        m.addConstr(c_info[c]['enrl']*x[c,rm]<=r_info[rm]['Capacity'])
               
                
    for c in all_courses:
        # each course should be assigned to one room or up to two hybrid rooms
        if c_info[c]['enrl']>=in_person_hybrid:
            m.addConstr(gp.quicksum(x[c,rm]+.5*y[c,rm] for (cs,rm) in ind 
                                    if cs==c)<=1)
        # if below certain enrl, assigned to a room or one hybrid room
        else:
            m.addConstr(gp.quicksum(x[c,rm]+y[c,rm] for (cs,rm) in ind 
                                    if cs==c)<=1)
    m.optimize()
    rt = m.Runtime
    mg = m.MIPGap
    m.write(folder+'model.lp')
    pri = '/'.join([str(p_wt[i]) for i in range(len(cf.course_priority))])

    results = pd.DataFrame({'Objective':[obj],'Priority Weight':[pri],
                            'Priority':[p_name],
                            'Runtime':[rt],'MIPGap':[mg]})
    
    new_schedule = old_schedule.rename(columns={'Room':'Orig Room'})
    new_schedule['Objective'], new_schedule['Priority'] = obj, p_name
    
    # create a dataframe with opt soln values
    sol_df = pd.DataFrame(columns=['Course','Room','x','y'], 
                          index=range(len(ind)))
    for i in range(len(ind)):
        sol_df.loc[i,'Course'] = ind[i][0]
        sol_df.loc[i,'Room'] = ind[i][1]
        sol_df.loc[i,'x'] = x[ind[i]].x
        sol_df.loc[i,'y'] = y[ind[i]].x
        
    for c in all_courses:
        c_df = sol_df.loc[(sol_df['Course']==c)&
                          ((sol_df['x']>.9)|(sol_df['y']>.9))]
        if c_df['x'].sum() > .9:
            delivery = 'In Person'
            if len(c_df.index)!=1:
                raise Exception('Course is in person with != 1 assignment',c_df)
        elif c_df['y'].sum() > 1.8:
            delivery = 'In Person Hybrid'
            if len(c_df.index)!=2:
                raise Exception('Course is IPH without 2 assignments',c_df)
        elif c_df['y'].sum() > .9:
            delivery = 'Online Hybrid'
            if len(c_df.index)!=1:
                raise Exception('Course is OH with != 1 assignment',c_df)
        else:
            delivery = 'Online'
            if not c_df.empty:
                raise Exception('Course is online with assignment',c_df)
        c_rooms = list(c_df['Room']) 

        new_schedule.loc[new_schedule['Course ID']==c,
                         'Instr Mode']=delivery
        new_schedule.loc[new_schedule['Course ID']==c,
                         'Room']=' + '.join(c_rooms)
        
    new_schedule = save.schedule(new_schedule, r_info, folder)

    all_schedules = all_schedules.append(new_schedule)
    all_results = all_results.append(results)
    return all_results, all_schedules
    
            
            
        
    
    