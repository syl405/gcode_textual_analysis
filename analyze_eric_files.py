#!/usr/bin/python
import csv
from fetch_and_process import fetch_and_process

csv_path = 'eric_regression/print_time_regression_042317.csv'
data_output_path = 'feature_extraction_output/textual_analysis_output_053017.csv'
process_log_path = 'logs/process_log_053017.txt'
access_log_path = 'logs/access_log_053017.txt'

output_tuple = fetch_and_process(csv_path)

output_dict = output_tuple[0]
process_error_list = output_tuple[1]
access_error_list = output_tuple[2]

output_fs = open(data_output_path,'w')
writer = csv.DictWriter(output_fs,output_dict.keys())
writer.writeheader()
writer.writerows(output_dict)
output_fs.close()

process_log_fs = open(process_log_path,'w')
for item in process_error_list:
	print>>process_log_fs, item
process_log_fs.close()

access_log_fs = open(access_log_path,'w')
for item in access_error_list:
	print>>access_log_fs, item
access_log_fs.close()

