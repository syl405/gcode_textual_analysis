#!/usr/bin/python

import boto3
import botocore
import csv
from process_single_file import process_single_file

BUCKET_NAME = 'nvbots-production'

def fetch_and_process(list_file_path):
	'''takes a list of S3 object keys pointing to individual g-code files, downloads them from nvbots-production bucket, carry out textual analysis on each file, and outputs a tuple containing:
		-list of dictionaries containing extracted features.
		-list of file keys corresponding to files that failed to process'''

	output_dicts = [] #instantiate list of dictionaries for output
	process_error_list = []
	access_error_list = []

	#load list file
	list_file_stream = open(list_file_path)
	list_file_reader = csv.DictReader(list_file_stream) #iterable object containing list of entries

	s3_client = boto3.client('s3', config=botocore.client.Config(signature_version='s3v4'))


	#iterate through list and download + process files
	for entry in list_file_reader:
		key = entry['submission__gcode']
		try:
			print key
			s3_client.download_file(BUCKET_NAME, key, 'local_copy_gcode.gcode')
		except botocore.exceptions.ClientError as e:
			if e.response['Error']['Code'] == "404":
				print("The object does not exist.")
			else:
				print('Unexpected file access error!')
				access_error_list.append(key)
				continue
		try:
			gcode_stream = open('local_copy_gcode.gcode')
			output = process_single_file(gcode_stream)
			output['filename'] = key
			output_dicts.append(output)
			gcode_stream.close()
		except:
			process_error_list.append(key)
			raise
		else:
			print 'successfully processed'

	list_file_stream.close()

	return (output_dicts,process_error_list,access_error_list)