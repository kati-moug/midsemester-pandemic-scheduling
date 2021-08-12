# midsemester-pandemic-scheduling
"""
@author: Kati Moug
version: 1.0
updated: Aug 12, 2021
"""

Built with:
	Python 3.8
	Gurobi 9.1.2
	Numpy 1.19.2
	Pandas 1.1.3

Usage:
Set input parameters in config.py, including location of input data files. Example data files
included in ‘data/‘. Run main.py.

File Documentation:
Each function can take inputs from the function or from the config file. Outputs can be from the function
or to saved file locations.

calculate.py
	function: t_matrix(processed_sched, r_info, tau)
	inputs (function):
		processed_sched: Pandas data frame with current courses and following columns:
	⁃	‘Effective Enrollment’ - enrollment estimate to use in IP
	⁃	‘Course Priority’ - in person priority ranking to use in IP objective
	⁃	‘Course’: name of academic course (e.g., Calculus I)
	⁃	‘Component’: part of course (e.g., lecture, discussion, lab)
	⁃	‘Specialty Course’: 0 if general, can be assigned to any general room, 1 if specialty
	⁃	‘Course ID’: unique ID associated with this course section
	⁃	in our example data, it is Course + Section
	⁃	‘Start i’ and ‘End i’ - discrete time unit of [start, end) for course 
	⁃	‘Violated’ - 1 if enrollment violates new capacity, 0 otherwise
	⁃	‘Room’ - original room assignment
		r_info: dictionary with rooms as keys
		tau: integer. Number of total discrete time units.
	inputs (config):
		days — a list of the days of the week included in schedule
	outputs (function):
		T_r — dictionary. Each key is a room, with np.array value of size tau x len(days).
		There are 0s for each discrete time unit when the room is unavailable, 1 otherwise.
		T_c — dictionary. Each key is a violated course section, with np.array value
		of size tau x len(days). There is a 1 for each discrete time unit when the course is
		in session, and 0 for all other entries.
		c_info — dictionary. Each key is a violated course section, with dictionary value,
		that includes keys
	⁃	‘enrl’: enrollment estimate to be used in IP
	⁃	‘p’: course priority ranking, to be used in IP
	⁃	‘Course’, ‘Component’, ‘Specialty Course’ (True or False)
		general_viol_courses — list of violated courses that are general and can be
		assigned to any general room.
	outputs (config): none
	description:
		This function creates dictionaries for T matrices for all rooms and for courses
		that violate capacity constraints. It also creates a dictionary with info about
		courses that violate capacity constraints to use in the IP, including enrollment
		estimate and other features that can be used to define the objective.
		It also creates a list of general courses to be used in creating the (course, room)
		index for the IP. 


estimate_enroll.py
	function: f19_rcr(schedule_df)
	inputs (function):
		schedule_df: Pandas data frame with current courses and following columns:
	⁃	‘Component’ - lecture, lab, etc. (Must be a single component to get historical estimate.
				If entry is a list, joined by ‘//‘, will be treated as if no historical estimate exists.)
	⁃	‘Course’ - if cross listed, joined by ‘//‘
	⁃	‘Room Cap Request’ - string of numbers (joined by ‘//‘) representing different 
				request for room size (if not cross-listed, single number)
	⁃	‘Capacity’ - Original capacity of the original room assigned
	inputs (config):
		f19_file: .csv file with historical data used to create estimate. In this file,
		unlike schedule_file, a single cross-listed course should be in multiple rows, with each row
		having a single entry for ‘Course’, ‘Component’, etc. Because we take the maximum over
		all sections of a course, we do not have to know which rows represent the same class.
		The following columns are required:
	⁃	‘Course’: name of academic course (e.g., Calculus I)
	⁃	‘Component’: part of course (e.g., lecture, discussion, lab)
	⁃	‘Section Enrl’: historical enrollment
	outputs (function): schedule_df with new columns ‘Estimate Enrl’ with enrollment estimate,
		‘Estimate Enrl Method’ describing how that row was calculated, and ‘Estimate Enrl Crses’
		with indices from historical data frame that were used to calculate.
	outputs (saved files): none
	description:
		Read historical data to Pandas data frame.
		For each current course section, determine all corresponding courses (e.g., for
		cross-listed course, MATH 500, BUS 520). Then, find max section enrollment over 
		all sections of all corresponding courses in historical data. Compare with room capacity
		request. If the largest request (more than one can exist for cross-listed) is positive
		and less than historical estimate, honor that smaller request. If no historical data is available,
		take room capacity request if available. Otherwise, take capacity of assigned room.

	function: get_course_enroll(df, course, cmpnt, how=‘max’)
	inputs (function): 
		df — Pandas data frame with ‘Course’ and ‘Component’ columns. Each row has only
			a single entry for ‘Course’ and ‘Component’, no lists.
		course — string. Name of the course to find enrollment for.
		cmpnt — string. Name of component to find enrollment for.
		how — ‘max’. How to compare multiple section enrollment values. Only max available now.
	inputs (config): none.
	outputs (function): enrollment estimate (number), list of df indices of course sections used to estimate
	outputs (saved files): none
	description:
		Find all rows of df with course and component. If there are none, return estimate 0 and [ ].
		Otherwise, return the max over ‘Section Enrl’ column, and the df indices associated with
		all rows used to calculate the estimate.

	function: rcr(schedule_df)
	inputs (function): 
		schedule_df: Pandas data frame with current courses and following columns:
	⁃	‘Room Cap Request’ - string of numbers (joined by ‘//‘) representing different 
				request for room size (if not cross-listed, single number)
	⁃	‘Capacity’ - Original capacity of the original room assigned
	inputs (config): none
	outputs (function): schedule_df with new ’Estimate Enrl’ and ‘Estimate Enrl Method’ columns
	outputs (saved files): none
	description:
		For each course section in schedule_df, estimate enrollment using smallest nonzero 
		room capacity request. (At least that many could take the course.) We compare this
		eventually with current enrollment, so if it is closer to the larger RCR, this is considered. 
		If nonzero room capacity request does not exist, take original capacity of original room. 

model.py
	function: optimize(T_r, T_c, c_info, tau, r_info, in_person_hybrid, p_wt, 
             			all_results, ind, old_schedule, all_schedules,
             			p_name, folder)
	inputs (function):
		T_r — dictionary. Each key is a room, with np.array value of size tau x len(days).
		There are 0s for each discrete time unit when the room is unavailable, 1 otherwise.
		T_c — dictionary. Each key is a violated course section, with np.array value
		of size tau x len(days). There is a 1 for each discrete time unit when the course is
		in session, and 0 for all other entries.
		c_info — dictionary. Each key is a violated course section, with dictionary value,
		that includes keys
	⁃	‘enrl’: enrollment estimate to be used in IP
	⁃	‘p’: course priority ranking, to be used in IP
	⁃	‘Course’, ‘Component’, ‘Specialty Course’ (True or False)
		tau - total number of discrete time units
		r_info — dictionary with room keys. The value of each room is a dictionary with keys
	⁃	‘Capacity’
	⁃	‘Bldg’
	⁃	‘Type’
		in_person_hybrid — integer. Only allow course sections to be in person hybrid if their 
		enrollment is at least this number.
		p_wt — list of numbers. For index i=0,…,len(cf.course_priority)-1, p_wt[i]  is the priority 
		weight associated with level/component course_priority[i].
		all_results — Pandas data frame. Empty if this is the first test. Otherwise, each row is a 
		previous test result. Columns are:
	⁃	‘Objective’: ‘Maximize In Person Enrollment’ or ‘Maximize In Person Courses’
	⁃	‘Priority Weight’: string of weights in descending priority order, joined by ‘/‘
	⁃	‘Priority’: p_name - string describing how prioritization weights were chosen
	⁃	‘Runtime’: runtime of the Gurobi IP for that test.
	⁃	‘MIPGap’ : MIP Gap for Gurobi IP for that test.
		ind — list of (c,r) tuples. (Course, room) index for all specialty rooms.
		old_schedule — Pandas data frame. Schedule with old room assignments, processed with
		read.schedule(). Required columns:
	⁃	‘Room’: original room assignment
	⁃	‘Course ID’: unique ID associated with this course section
	⁃	in our example data, it is Course + Section
	⁃	Columns required for save.schedule()
		all_schedules — Pandas data frame. Contains all previous test new schedules. Columns
		‘Objective’ and ‘Priority’ designate which test each row is associated with.
		p_name — string. Describes how prioritization weights were chosen.
		folder — string. Location to save results. Folder should already exist.
	inputs (config):
		time_limit — number. Time limit for the Gurobi solver.
		enroll_obj — Boolean. If True, objective is to maximize (weighted) in person enrollment. False, 
		maximize (weighted) in person courses.
		course_priority — list of (ug, component) tuples in descending in person priority
			We assume that for a fixed ug, course_priority honors comp_priority ranking
			and for a fixed component, course_priority honors ug ranking.
	outputs (function):
		all_results — Pandas data frame. Updated from input to include a new row for this test.
		all_schedules — Pandas data frame. Concatenated with input to include new schedule for this 
		test.
	outputs (saved files): see save.schedule(), which is called by this function.
	description:
		IP is implemented using Gurobi. The weight for each course section in the objective is either
		the priority weight of its in person priority ranking (if enroll_obj = False) or the priority weight
		times the estimated enrollment (if enroll_obj = True). Note that we take the floor of half of
		enrollment in the hybrid feasibility constraints to make them slightly looser. After optimization,
		we find the delivery mode for each course, given by the IP, and send the new schedule to 
		save.schedule() to save it. We update all_results and all_scheds to include this test, and 
		output.
priority.py
	function: level_component(schedule_df)
	inputs (function):
		schedule_df: Pandas data frame with columns (if cross-listed, options joined by ‘//‘):
	⁃	‘Level’ - numeric level of course (e.g., 100, 200)
	⁃	‘Component’ - part of course (e.g., lecture, discussion, lab)
		Index should not include any duplicates.
	inputs (config):
		ug_levels — dictionary with keys that describe type of levels (e.g., ‘U’ for undergrad, ‘G’ grad)
			The value for each key is a list of all levels of that type (e.g., ‘U’:[100,200,300])
		ug — keys of ug_levels, joined by ‘/‘
		comp_priority — list of components in descending in person priority
		course_priority — list of (ug, component) tuples in descending in person priority
			We assume that for a fixed ug, course_priority honors comp_priority ranking
			and for a fixed component, course_priority honors ug ranking.
		cross_listed — ‘max’ or ‘min’. If a course is cross-listed as 300/400, take max (or min) of the
			two to determine ‘U’, ‘G’, etc. 
			If ‘max’, we assume we are choosing lowest priority of the cross-listed (since ‘U’ 
			generally should be in person before ‘G’). Thus, we also choose lowest priority
			of the cross-listed components. If ‘min’, we choose highest priority cross-listed comp.
	outputs (function): schedule_df with ‘Component’ updated to single component of interest,
				new ug column, and in person priority ranking column ‘Course Priority’.
	outputs (saved files): none
	description:
		Add column to schedule_df with in person priority ranking, using course_priority list.
		If there is more than one level or component listed (due to cross-listed course), 
		sort the levels or components and then choose max/min based on config. 
		Add column with ug type.
		
		

read.py
	function: room_data()
	inputs (function): none
	inputs (config): 
		w_folder — string with result folder location
		room_cap_prop — number in (0,1]. If all room capacities are reduced to a
			specific proportion of original capacity, this should be set to that proportion.
			Otherwise, this should be set to 1, and new capacities should be 
			written in room_cap_file, column ‘Max Capacity’
		round_new_cap_up — Boolean. If True, when calculating new room capacities,
			by multiplying room_cap_prop times column ‘Max Capacity’, take ceiling.
			This leads to slightly looser feasibility constraints. Otherwise, take floor.
		room_cap_file — a string of location of .csv file that describes classrooms,
			with a room in each row, and columns 
	⁃	‘Room’: unique name of room
	⁃	‘Max Capacity’: 
	⁃	capacity of the room before reduction, if room_cap_prop<1
	⁃	capacity of the room after reduction, otherwise
	⁃	‘Bldg’: where room is located
	⁃	‘Type’: 
	⁃	‘General’: a room that any general course is permitted to use
	⁃	‘Specialty’: a room that only specific courses (general or specialty) can use
	outputs (function): 
		r_info — dictionary with room keys. The value of each room is a dictionary with keys
	⁃	‘Capacity’
	⁃	‘Bldg’
	⁃	‘Type’
		general_rooms — list of all general rooms
	outputs (saved files):
		new_room_capacity.csv — .csv with added ‘New Capacity’ column
	description:
		creates a Pandas data frame of room capacity info from .csv file, calculates new
		room capacities based on room_cap_prop, round_new_cap_up, and ‘Max Capacity’
		column in .csv. Puts info from data frame and new capacity into r_info dictionary,
		to be used for capacities in IP as well as prioritization weights in the objective
		(for example, weight can be added to (course, room) indices that put a course 
		in a preferred building). Creates a list of general_rooms to use in creating index for IP. 

	function: schedule(r_info)
	inputs (function): 
		r_info — dictionary with room keys. The value of each room is a dictionary with keys
	⁃	‘Capacity’
	⁃	‘Bldg’
	⁃	‘Type’
	inputs (config):
		w_folder — string. Folder to save results.
		ell — positive integer. The length of a unit of time in the schedule in minutes (e.g., 15, 30).
		estimate_enroll — ‘None’ or ‘f19max_rcr’. Method to estimate enrollment.
		course_priority_option — ‘level_component’. Method to determine in person priority ranking for 
			course.
		schedule_file — .csv file with each row representing a unique course section. 
		Required columns (if cross-listed course, multiple joined by ‘//‘ unless otherwise stated):
	⁃	‘Course’: name of academic course (e.g., Calculus I)
	⁃	‘Component’: part of course (e.g., lecture, discussion, lab)
	⁃	‘Level’ - numeric level of course (e.g., 100, 200)
	⁃	‘Section’: unique number associated with this particular section of course
	⁃	‘Course ID’: unique ID associated with this course section
	⁃	in our example data, it is Course + Section
	⁃	‘Start Time’ and ‘End Time’ of the course section in HH:MM:SS, 24-hour format
	⁃	‘Days’ that course section meets, joined by ‘/‘
	⁃	‘Effective Enrollment’ - current enrollment. 
	⁃	If estimate_enroll_option=‘None’ this is assumed enrollment
	⁃	Otherwise this enrollment is taken as input to estimate_enroll method
	⁃	‘Room’ - original room assignment
	⁃	‘Specialty Course’: 0 if general, can be assigned to any general room, 1 if specialty
	outputs (function):
		processed_sched - Pandas data frame with new, processed columns
		tau - total number of discrete time units
	outputs (saved files):
		old_schedule_input.csv - processed schedule with original rooms and whether violated
	description:
		Read .csv file with schedule information, including current room assignment,
		time, and enrollment as Pandas data frame. Add columns: 
	⁃	‘Start i’/‘End i’ - conversion of ‘Start Time’/‘End Time’ to discrete time units
	⁃	‘M’, ’T’, ‘W’, etc - 1 if course section meets that day, empty otherwise
	⁃	‘Course Priority’ - in person priority ranking (1=highest)*
	⁃	‘Estimate Enroll Method’
	⁃	‘Current Data Only’ if no estimation is done. 
	⁃	Other possibilities determined by enrollment estimation function*
	⁃	(Optional) ‘Orig Effective Enroll’ 
	⁃	new title of input ‘Effective Enrollment’ if enrollment is estimated
	⁃	‘Effective Enrollment’ becomes the title of estimate to be used in IP
	⁃	‘New Capacity’ - the new capacity of original room assignment
	⁃	‘Violated’ - 1 if ‘Effective Enrollment’ > ‘New Capacity’, 0 otherwise.
		* new methods to determine priority and enrollment estimation can be added as
		functions in the priority.py or estimate_enroll.py file, & added as options to config.
		Save processed_sched and output.

	function: specialty_permissions(c_info)
	inputs (function): c_info
	inputs (config): 
		specialty_room_file — .csv file with columns ‘Course’, ‘Component’, ‘Room’.
		Each row contains a specialty room (under ‘Room’) and a single course/component
		pair allowed to use that room. There should be a row for each course/component 
		with permissions to use the specialty room.
	outputs (function):
		index — list of (c,r) tuples. (Course, room) index for all specialty rooms.
	outputs (saved files): none
	description:
		Read specialty_room_file as Pandas data frame. For each violated course section, see if 
		its course/component pair has permission to use any specialty rooms. General courses may 
		or may not have permission to use a specialty room. Specialty courses must have permission 
		to use at least one, since they cannot use general rooms. Include any allowed (course, room) 
		pairs in the index output by function.
		
save.py
	function: schedule(df, r_info, folder)
	inputs (function): 
		df — Pandas data frame with schedule from IP to save. Includes columns:
	⁃	‘Objective’ and ‘Priority’ associated with current test
	⁃	-      ‘Course’: name of academic course (e.g., Calculus I)
	⁃	‘Component’: part of course (e.g., lecture, discussion, lab)
	⁃	‘Section’: unique number associated with this particular section of course
	⁃	‘Start Time’ and ‘End Time’ of the course section in HH:MM:SS, 24-hour format
	⁃	‘Start DT’: Start time of course in pd.datetime() format
	⁃	‘Start i’ and ‘End i’: discrete time unit of [start, end) for course 
	⁃	‘Days’ that course section meets, joined by ‘/‘
	⁃	‘Subject’ — subjects of course (e.g., MATH, BUS) joined by ‘//‘
	⁃	‘Orig Room’ - original room assignment
	⁃	‘Specialty Course’: 0 if general, can be assigned to any general room, 1 if specialty
	⁃	config.ug (e.g., ‘U/G’)
	⁃	‘Course Priority’
	⁃	‘Section Enrl’ — original enrollment
	⁃	‘Estimate Enrl’ — historical estimate
	⁃	‘Estimate Enrl Method’ — string describing method for historical estimate
	⁃	‘Effective Enrollment’ — final enrollment estimate used in IP
	⁃	‘Instr Mode’ — mode of delivery
