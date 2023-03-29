% HDF5 data extractor
% Created by: Jenna Grieshop
% Date created: 3/29/2023
%
% Purpose: Extract data from HDF5 files and save data as uncompressed
% grayscale AVIs


clear all
close all
clc

stack = [];

%% load in the file

% h5disp('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5');

v = VideoWriter('test.avi', 'Grayscale AVI');
open(v)

for i = 1:209
    
    frame_name = ['/ImageFrame_1_1_1_', num2str(i)];
    
    frame_data = h5read('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', frame_name);

    % extract and reformat the data
    gray_frame = frame_data(2,:,:);
    gray_frame = squeeze(gray_frame);
%     imshow(gray_frame);


    writeVideo(v, gray_frame);

    stack(:,:,i) = gray_frame;
end

close(v)
