#!/usr/bin/python
import re
#TO-DO: Handle autohoming commands (G28s)
#TO-DO: Record filament length extruded during purge separately from filament deposited on part
def process_single_file(fs):
	'''Takes an NVPRO g-code file and outputs list of textual attributes. Also returns a naive estimate of print time based purely on moves.

	Inputs: 
	- NVPRO g-code file with .gcode suffix

	Outputs:
	- dictionary containing features (aka predictor vars.), including a naive print time estimate for this observation
		- keys: feature names
		- values: value of feature for this observation
	'''

	#Validate argument
	if not type(fs) is file:
		raise TypeError('Argument fs wrong datatype. Expecting file')
	if not fs.name.endswith('.gcode'):
		raise NameError('Argument fs refers to non-gcode file. Expecting .gcode suffix.')
	if fs.readline() != '; generated by NVBOTS\n':
		raise NameError('G-code file is missing NVBOTS-generated header')

	#Raw textual features
	output = {'num_lines_gcode':0, #ok
			  'num_lines_comment': 0, #ok
			  'num_lines_move': 0, #ok
			  'total_dist_move': 0, #ok
			  'total_dist_print': 0, #ok
			  'num_temp_changes': 0, #ok
			  'num_retract': 0, #ok
			  'num_unretract': 0, #ok
			  'total_length_extruded': 0, #ok
			  'num_temp_checks': 0, #ok
			  'num_fan_on': 0, #ok
			  'num_fan_off': 0, #ok
			  'num_purges': 0, #ok
			  'total_dwell_time': 0, #ok
			  'naive_print_time': 0} #ok

	#Raft and print parameters
	seam_position = 0
	fill_angle = 0
	fill_density = 0
	fill_pattern = 0
	retract_length = 0
	nozzle_diameter = 0
	bottom_solid_layers = 0
	top_solid_layers = 0
	external_perimeter_speed_multiplier = 0
	small_perimeter_speed_multiplier = 0
	gap_fill_speed_multiplier = 0
	infill_speed_multiplier = 0
	solid_infill_speed_multiplier = 0
	top_solid_infill_speed_multiplier = 0
	support_material_interface_speed_multiplier = 0
	support_material_speed = 0
	base_travel_speed = 0
	default_acceleration = 0
	infill_acceleration = 0
	perimeter_acceleration = 0

	#Toggle variables to handle blocks of codes
	in_purge = 0
	in_header = 0
	in_footer = 0

	#Variables to store current axis position
	motion_params ={'X': 0, #current x position in mm
					'Y': 0, #current y position in mm
					'Z': 0, #current z position in mm
					'F': 0, #current feedrate in mm/s
					'E': 0, #current extrusion length in mm
					'A': 3000, #current acceleration in mm/s^2, 3000 default
					'T': 0} #current temperature in degsC

	#Pre-compiled regex patterns
	move_pattern = '((?:X|Y|E|F)\d+\.?\d*)'
	move_regex = re.compile(move_pattern)
	temp_pattern = 'S(\d+\.?\d*)'
	temp_regex = re.compile(temp_pattern)
	dwell_pattern = 'P(\d+\.?\d*)'
	dwell_regex = re.compile(dwell_pattern)

	#Read in header
	cur_line = fs.readline() #read first line
	while cur_line.startswith(';'): #exit when past initial block of comments
		output['num_lines_gcode'] += 1
		output['num_lines_comment'] += 1
		cur_line = fs.readline() #read next line

	#Iterate through remainder of lines
	while cur_line: #Exit loop when cur_line is empty, i.e. EOF
		if cur_line.startswith(';'):
			output['num_lines_comment'] += 1
			if cur_line == '; Begin move/purge/wipe gcode\n': #detect start of purge routine
				output['num_purges'] += 1
				in_purge = 1
			elif cur_line == '; End move/purge/wipe gcode\n':
				in_purge = 0
		elif cur_line.startswith('G0 ') or cur_line.startswith('G1 '): #move lines
			motion_params['E'] = 0 #not extruding by default
			deltas ={'X': 0, #x motion this line in mm
					 'Y': 0, #y motion this line in mm
					 'Z': 0} #z motion this line in mm
			match_lists = move_regex.findall(cur_line)
			for i in match_lists:
				cur_axis = i[0] #first character in string
				cur_axis_dest = float(i[1:])
				if cur_axis in ('X','Y','Z'):
					deltas[cur_axis] = cur_axis_dest - motion_params[cur_axis] #calculate relative motion
				elif cur_axis == 'E':
					motion_params['E'] = cur_axis_dest
				motion_params[cur_axis] = cur_axis_dest #update machine position
			cur_move_dist = ((deltas['X'])**2+(deltas['Y'])**2)**0.5 #pythagorean theorem
			output['total_dist_move'] += cur_move_dist
			if motion_params['E']:
				output['total_dist_print'] += cur_move_dist
			output['total_length_extruded'] += motion_params['E']
			output['num_lines_move'] += 1

			#calculate naive print time
			if cur_move_dist <= 0:
				print 'redundant move line'
			elif cur_move_dist > motion_params['F']**2 / (2*motion_params['A']): #trapezoidal profile
				print_time_this_move = ((2*motion_params['F'])/motion_params['A'])+((cur_move_dist-((motion_params['F'])**0.5/(motion_params['A'])))/(motion_params['F']))
			else: #triangular profile
				#cusp_speed = (motion_params['A']*cur_move_dist)^0.5 (for reference only, close form solution)
				print_time_this_move = (2*cur_move_dist)/((motion_params['A']*cur_move_dist)**0.5)
			output['naive_print_time'] += print_time_this_move
		elif cur_line.startswith('M105 '): #temp check lines
			output['num_temp_checks'] += 1
		elif cur_line.startswith('M104 '): #temp set lines
			output['num_temp_changes'] += 1
			motion_params['T'] = float(temp_regex.search(cur_line).group(1))
		elif cur_line.startswith('M204 '): #acceleration set lines
			motion_params['A'] = float(temp_regex.search(cur_line).group(1))
		elif cur_line.startswith('G10 '): #retract lines
			output['num_retract'] += 1
		elif cur_line.startswith('G11 '): #unretract lines
			output['num_unretract'] += 1
		elif cur_line.startswith('G4 '): #waiting lines
			output['total_dwell_time'] += float(dwell_regex.search(cur_line).group(1)*1000)
		elif cur_line.startswith('M107 '): #fan off lines
			output['num_fan_off'] += 1
		elif cur_line.startswith('M106 '): #unretract lines
			output['num_fan_on'] += 1

		output['num_lines_gcode'] += 1
		cur_line = fs.readline()
	return output