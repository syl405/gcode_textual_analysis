%% Parse in eric data
raw_filename = '../eric_regression/print_time_regression_042317.xlsx';
[~,~,raw_data] = xlsread(raw_filename, 'data_and_analysis', 'A2:AA1001','basic');
gcode_keys = raw_data(:,3);
actual_pt = cell2mat(raw_data(:,4));
sim_pt = cell2mat(raw_data(:,5));
sim_pt_w_accel = cell2mat(raw_data(:,6));
exp_sim_model_guess = cell2mat(raw_data(:,27))*60;

%% Parse in textual analysis output
raw_filename = '../analysis_output_052617.xlsx';
[~,~,headers] = xlsread(raw_filename, 'analysis_output_052617', 'A1:T1','basic');
[~,~,raw_data] = xlsread(raw_filename, 'analysis_output_052617', 'A2:T650','basic');
textual_data = cell2table(raw_data,'VariableNames',headers);

%% Discard duplicate points from textual data
unique_keys = unique(textual_data.filename);
[~,index_to_keep] = ismember(unique_keys,textual_data.filename);
textual_data = textual_data(index_to_keep,:);

%% Get actual print time data for each point in textual analysis
[~,index_in_eric_data] = ismember(textual_data.filename,gcode_keys);
actual_pts_training_set = actual_pt(index_in_eric_data);
textual_data.observed_pt = actual_pts_training_set;

lm = fitlm(textual_data(:,2:end),'interactions');
