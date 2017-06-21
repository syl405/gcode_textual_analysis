clear

%% Parse in eric data
raw_filename = '../eric_regression/print_time_regression_042317.xlsx';
[~,~,raw_data] = xlsread(raw_filename, 'data_and_analysis', 'A2:AA1001','basic');
gcode_keys = raw_data(:,3);
actual_pt = cell2mat(raw_data(:,4));
sim_pt = cell2mat(raw_data(:,5));
sim_pt_w_accel = cell2mat(raw_data(:,6));
exp_sim_model_guess = cell2mat(raw_data(:,27))*60;

%% Parse in textual analysis output
raw_filename = '../feature_extraction_output/textual_analysis_output_053017.xlsx';
[~,~,headers] = xlsread(raw_filename, 'textual_analysis_output_053017', 'A1:T1','basic');
[~,~,raw_data] = xlsread(raw_filename, 'textual_analysis_output_053017', 'A2:T650','basic');
textual_data = cell2table(raw_data,'VariableNames',headers);

%% Discard duplicate points from textual data
unique_keys = unique(textual_data.filename);
[~,index_to_keep] = ismember(unique_keys,textual_data.filename);
textual_data = textual_data(index_to_keep,:);

%% Get actual print time data for each point in textual analysis
[~,index_in_eric_data] = ismember(textual_data.filename,gcode_keys);
actual_pts_training_set = actual_pt(index_in_eric_data);
textual_data.observed_pt = actual_pts_training_set;

lm = fitlm([textual_data(:,1:12) textual_data(:,14:end)],'linear');

%% Preliminary comparison between textual analysis model and simulator regression
%(currently based only on in-set prediction, need validation set)
sim_abs_errors = abs(exp_sim_model_guess-actual_pt)/60; % in mins
textual_abs_errors = abs(lm.Residuals.Raw)/60; % in mins

sim_rel_errors = sim_abs_errors*60./actual_pt;
textual_rel_errors = textual_abs_errors*60./textual_data.observed_pt;

