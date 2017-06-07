process_single_file() extracts features from a single g-code file
fetch_and_process() calls process_single_file() on a list of files
analyze_eric_files calls fetch_and_process() using a CSV containing Eric's simulator regression results and writes feature extraction output and logs to files.