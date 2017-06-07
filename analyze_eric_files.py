#!/usr/bin/python

'''
Quick script to automate retrieval and feature extraction on the files Eric used in his original simulation.
- Accesses CSV file containing Eric's simulator regression data
- Retrieves G-code files referenced in simulator regression CSV from S3 bucket
- Runs feature extraction on each file using fetch_and_process()
- Writes extracted features to output CSV file

Package dependencies:
- csv
- fetch_and_process
'''

import csv
from fetch_and_process import fetch_and_process

csv_path = 'eric_regression/print_time_regression_042317.csv'
data_output_path = 'feature_extraction_output/textual_analysis_output_060717.csv'
process_log_path = 'logs/process_log_060717.txt'
access_log_path = 'logs/access_log_060717.txt'

output_tuple = fetch_and_process(csv_path)

output_dicts = output_tuple[0]
process_error_list = output_tuple[1]
access_error_list = output_tuple[2]

output_fs = open(data_output_path,'w')
writer = csv.DictWriter(output_fs,output_dicts[0].keys(),lineterminator = '\n') #force line terminator to also work properly on Windows
writer.writeheader()
writer.writerows(output_dicts)
output_fs.close()

process_log_fs = open(process_log_path,'w')
for item in process_error_list:
	print>>process_log_fs, item
process_log_fs.close()

access_log_fs = open(access_log_path,'w')
for item in access_error_list:
	print>>access_log_fs, item
access_log_fs.close()

