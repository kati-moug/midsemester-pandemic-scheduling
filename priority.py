"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""
import config as cf

def level_component(schedule_df):
    schedule_df['Orig Component'] = schedule_df['Component']
    schedule_df['Level'] = schedule_df['Level'].astype(str)
    for row in schedule_df.index:
        levels = schedule_df.loc[row,'Level'].split('//')
        comps = schedule_df.loc[row,'Component'].split('//')
        comp_pri_dict = {c: cf.comp_priority.index(c) for c in comps}
        comp_priority = sorted(comp_pri_dict, key=comp_pri_dict.get)
        if cf.cross_listed == 'max': # if cross listed, make it lower priority
            level = max([int(float(l)) for l in levels])
            schedule_df.loc[row,'Component']=comp_priority[-1]
        elif cf.cross_listed == 'min': # make it the higher priority
            level = min([int(float(l)) for l in levels])
            schedule_df.loc[row,'Component']=comp_priority[0]
        for typ in cf.ug_levels.keys():
            if level in cf.ug_levels[typ]:
                schedule_df.loc[row,cf.ug] = typ
                break
    # add column with course priority
    for i in range(len(cf.course_priority)):
        # set column as i if 'U/G' and 'Component' match course priority[i]
        schedule_df.loc[(schedule_df[cf.ug]==cf.course_priority[i][0])&
                    (schedule_df['Component']==cf.course_priority[i][1]),
                    'Course Priority'] = i
    return schedule_df
