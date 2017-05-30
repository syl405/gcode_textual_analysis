#!/usr/bin/python

import boto3
import botocore
import csv
from process_single_file import process_single_file

BUCKET_NAME = 'nvbots-production'

def fetch_and_process(list_file_path):
	'''takes a list of S3 object keys pointing to individual g-code files, downloads them from nvbots-production bucket, carry out textual analysis on each file, and outputs a tuple containing:
		-list of dictionaries containing extracted features.
		-list of file keys corresponding to files that failed to process
		-list of file keys corresponding to files that failed to retrieve'''

	output_dicts = []
	process_error_list = []
	access_error_list = []

	#load list file
	list_file_stream = open(list_file_path)

	#transforming into a list for easy enumeration, but could take a lot of memory for longer lists!
	list_file_reader = list(csv.DictReader(list_file_stream))#iterable object containing list of entries

	s3_client = boto3.client('s3', config=botocore.client.Config(signature_version='s3v4')) #create ClientObject, force signature version

	#progress variables
	current_file_index = 0
	num_file_in_list = len(list_file_reader)

	#iterate through list and download + process files
	for entry in list_file_reader:
		current_file_index += 1
		key = entry['submission__gcode'] #retrieve file key (path) from correct column in csv file
		print 'Processing file %d of %d' % (current_file_index, num_file_in_list)
		#try to retrieve file from S3 bucket
		try:
			s3_client.download_file(BUCKET_NAME, key, 'local_copy_gcode.gcode')
		except botocore.exceptions.ClientError as e:
			if e.response['Error']['Code'] == "404": #non-existent file
				print("The object does not exist.")
				access_error_list.append(key)
			else:
				print('Unexpected file access error!') #misc. retrieval error
				access_error_list.append(key)
				continue #skip current file
		
		#try to process retrieved file
		try:
			gcode_stream = open('local_copy_gcode.gcode')
			output = process_single_file(gcode_stream)
			output['filename'] = key #save file key corresponding to current file for ID
			output_dicts.append(output) #append dictionary to list
			gcode_stream.close() #close gcode file stream
		except: #catch errors from processing current g-code file
			process_error_list.append(key) #save list of files that failed to process

	list_file_stream.close()

	return (output_dicts,process_error_list,access_error_list)