#!/usr/bin/python
import re
#TO-DO: Handle autohoming commands (G28s)
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
	output = {'num_lines_gcode':2, #start at 2 for lines used to validate args
			  'num_lines_comment': 2, #start at 2 for lines used to validate args
			  'num_bytes_gcode': 0, #excluding comments
			  'num_lines_move': 0, #number of lines corresponding to G0/G1 motion
			  'num_redundant_lines': 0, #number of G0/G1 motion lines that don't actually move
			  'num_layers': 0, #number of layers in the print !!!!
			  'mean_angle_between_moves': 0, #mean angle between successive linear moves, in radians !!!
			  'median_angle_between_moves': 0, #median angle between successive linear moves, in radians !!!	
			  'total_dist_move': 0, #total vector distance
			  'total_dist_print': 0, #total vector distance moved while extruding
			  'num_temp_changes': 0, #number of temperature sets
			  'total_temp_increment': 0, #total degC increase (heating)
			  'total_temp_decrement': 0, #total degC decreaes (cooling)
			  'num_retract': 0, #number of filament retractions
			  'num_unretract': 0, #number of filament un-retractions
			  'total_length_extruded': 0, #total length of filament extruded
			  'num_temp_checks': 0, #number of temperature checks
			  'num_fan_on': 0, #number of times fan was turned on
			  'num_fan_off': 0, #number of times fan was turned off
			  'num_purges': 0, #number of times purge routine invoked
			  'total_dwell_time': 0, #total time spent in forced waiting in s
			  'naive_print_time': 0} #naive print time estimate from pure movement, assuming constant acceleration

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
					'mode': 0, #current mode, 0 for absolute, 1 for relative
					'T': 0} #current temperature in degsC

	#Pre-compiled regex patterns
	move_pattern = '((?:X|Y|Z|E|F)-?\d+\.?\d*)'
	move_regex = re.compile(move_pattern)
	temp_pattern = 'S(\d+\.?\d*)'
	temp_regex = re.compile(temp_pattern)
	dwell_pattern = 'P(\d+\.?\d*)'
	dwell_regex = re.compile(dwell_pattern)

	#Lists that are updated every iteration
	angles_between_moves = [] #list of angles between moves, in rads
	move_dists = [] #list of move distances, in mm

	cur_line = fs.readline() #read first line

	#Iterate through remainder of lines
	while cur_line: #Exit loop when cur_line is empty, i.e. EOF
		if cur_line.startswith(';'):
			output['num_lines_comment'] += 1
			if cur_line == '; Begin move/purge/wipe gcode\n': #detect start of purge routine
				output['num_purges'] += 1
				in_purge = 1
			elif cur_line == '; End move/purge/wipe gcode\n':
				in_purge = 0
			output['num_bytes_gcode'] -= len(cur_line)
		elif cur_line.startswith('G0 ') or cur_line.startswith('G1 '): #move lines
			motion_params['E'] = 0 #not extruding by default
			deltas ={'X': 0, #x motion this line in mm
					 'Y': 0, #y motion this line in mm
					 'Z': 0} #z motion this line in mm
			deltas_old ={'X': 0, #x motion last line in mm
						 'Y': 0, #y motion last line in mm
					     'Z': 0} #z motion last line in mm
			match_lists = move_regex.findall(cur_line)
			deltas_old = deltas #save previous move vector before updating
			for i in match_lists:
				cur_axis = i[0] #first character in string
				cur_axis_dest = float(i[1:])
				if cur_axis in ('X','Y','Z'):
					deltas[cur_axis] = cur_axis_dest - motion_params[cur_axis] #calculate relative motion
				elif cur_axis == 'E':
					motion_params['E'] = cur_axis_dest
				if motion_params['mode'] == 0:
					motion_params[cur_axis] = cur_axis_dest #update machine position
				elif motion_params['mode'] == 1:
					motion_params[cur_axis] += cur_axis_dest #increment machine position
				else:
					raise NameError('Unexpected motion mode. Expecting 0 (abs) or 1 (rel).')
			prev_move_dist = ((deltas_old['X'])**2+(deltas_old['Y'])**2+(deltas_old['Z'])**2)**0.5 #pythagorean theorem
			cur_move_dist = ((deltas['X'])**2+(deltas['Y'])**2+(deltas['Z'])**2)**0.5 #pythagorean theorem
			output['total_dist_move'] += cur_move_dist
			move_dists.append(cur_move_dist)
			if motion_params['E']:
				output['total_dist_print'] += cur_move_dist
			output['total_length_extruded'] += motion_params['E']
			output['num_lines_move'] += 1

			#calculate naive print time
			if cur_move_dist <= 0:
				output['num_redundant_lines'] += 1
			elif cur_move_dist > motion_params['F']**2 / (2*motion_params['A']): #trapezoidal profile
				print_time_this_move = ((2*motion_params['F'])/motion_params['A'])+((cur_move_dist-((motion_params['F'])**0.5/(motion_params['A'])))/(motion_params['F']))
			else: #triangular profile
				print_time_this_move = (2*cur_move_dist)/((motion_params['A']*cur_move_dist)**0.5)
			output['naive_print_time'] += print_time_this_move
		elif cur_line.startswith('M105 ')or cur_line.startswith('M105\n'): #temp check lines
			output['num_temp_checks'] += 1
		elif cur_line.startswith('M104 ')or cur_line.startswith('M104\n'): #temp set lines
			output['num_temp_changes'] += 1
			temp_target = float(temp_regex.search(cur_line).group(1))
			if motion_params['T'] < temp_target:
				output['total_temp_increment'] += temp_target - motion_params['T']
			else:
				output['total_temp_decrement'] += motion_params['T'] - temp_target
			motion_params['T'] = temp_target
		elif cur_line.startswith('M204 ') or cur_line.startswith('M204\n') : #acceleration set lines
			motion_params['A'] = float(temp_regex.search(cur_line).group(1))
		elif cur_line.startswith('G10 ') or cur_line.startswith('G10\n'): #retract lines
			output['num_retract'] += 1
		elif cur_line.startswith('G11 ') or cur_line.startswith('G11\n'): #unretract lines
			output['num_unretract'] += 1
		elif cur_line.startswith('G4 ') or cur_line.startswith('G4\n'): #waiting lines
			output['total_dwell_time'] += float(dwell_regex.search(cur_line).group(1))/1000
		elif cur_line.startswith('M107 ') or cur_line.startswith('M107\n'): #fan off lines
			output['num_fan_off'] += 1
		elif cur_line.startswith('M106 ') or cur_line.startswith('M106\n'): #fan on lines
			output['num_fan_on'] += 1
		elif cur_line.startswith('G90 ') or cur_line.startswith('G90\n'): #absolute positioning lines
			motion_params['mode'] = 0
		elif cur_line.startswith('G91 ') or cur_line.startswith('G91\n'): #relative positioning lines
			motion_params['mode'] = 1

		output['num_lines_gcode'] += 1
		output['num_bytes_gcode'] += len(cur_line)
		cur_line = fs.readline()
	return output