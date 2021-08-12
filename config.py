"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""

##############
# Data Files #
##############
data_folder = 'data/'
schedule_file = data_folder+'fall21.csv'
days = ['T','Th'] # how days are labeled in file
ell = 30 # length of a unit of time in minutes in the IP


# we multiply capacities in below file by prop to get new room capacities.
# to use a unique new capacity for each room, set room_cap_file to new room
# capacities and choose room_cap_prop = 1
room_cap_file = data_folder+'rooms.csv'
room_cap_prop = .5
round_new_cap_up = True # take ceiling of prop*old capacity to get new capacity? if True, assumes slightly looser constraint
specialty_room_file = data_folder+'specialty_room_permissions.csv'
#####################
# IP Options #
#####################
time_limit = 300

# set IP objective. if true, maximize in person enrollment, if false, 
# maximize in person courses
enroll_obj = False

# estimate enrollment? 
# to add a new estimation method, add new function to estimate_enroll.py 
# add descriptive string 'str' to estimation_options below
# add option to call function if estimate_enroll=='str' in read.schedule()
estimation_options = ['f19max_rcr','rcr','None'] 
estimate_enroll = estimation_options[0]

# file to estimate enrollment from 2019
f19_file = data_folder+'fall19_enrollment.csv'

# how to prioritize courses to stay in person?
# only option available now is level_component. prioritize by course level/type
# to add a new priority method, add new function to priority.py
# adapt code in read.schedule() in same manner as estimate_enroll above
course_priority_option = 'level_component'

if course_priority_option == 'level_component':
    # specify which course levels should be considered undergrad/grad/masters
    # can uncomment below to add masters designation to prioritization
    ug_levels = {'U':[100,200,300], # 'M':[400,500],
                 'G':[400,500,600,700,800]} # for masters designation, remove 400,500
    ug = 'U/G' #'U/M/G'
    
    # for cross listed courses, specify whether to determine U/M/G by max/min level
    # if max, we assume prioritize less cross-listed & accordingly also
    # choose lower priority course component if more than one
    cross_listed = 'max' # 'min' 

    # specify course priority to stay in person - highest to lowest
    course_priority = [('U','LAB'),#('M','LAB'),
                       ('G','LAB'),
                       ('U','DIS'),('U','REC'),('U','LEC'),
                       #('M','DIS'),('M','REC'),('M','LEC'),
                       ('G','DIS'),('G','REC'),('G','LEC'),
                       ('U','SEM'),#('M','SEM'),
                       ('G','SEM')]
    
    # component priority to stay in person
    comp_priority = ['LAB', 'DIS', 'REC', 'LEC', 'SEM']

# uncomment in p wt if you choose to include master's designation
test_options = {'in person hybrid threshold':[60], # if enrollment below threshold, IPH not available
                'p wt':[[#1.14,1.13,1.12,1.11,1.1,
                         1.09,1.08,1.07,1.06,1.05,
                         1.04,1.03,1.02,1.01,1],[1,1,1,1,1,#1,1,1,1,1,
                         1,1,1,1,1],[1,1,1,1,#1
				   2,1,1,1,1,1#,1,1,1,1]
                                     ]]} 


priority_names = ['Ordered List','None','100-300 Level Lectures']
tests = []
for a in test_options['in person hybrid threshold']:
    for b in test_options['p wt']:
        tests.append({'in person hybrid threshold': a, 'p wt': b, 
                      'p name': priority_names[test_options['p wt'].index(b)]})

#################
# Result Output #
#################
w_folder = 'test/' # folder will be created if does not exist, or overwrite files if it does