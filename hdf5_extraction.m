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

count = 1;
for i = 0:210
    if ~mod(i,10)
        if ~mod(i, 1)
            range(count) = i/10;
            count = count+1;
        end
    end
    
end

for i = 220:10:1000
    range(count) = i/10;
    count = count+1;
end


for i = 1:length(range)
    
    frame_name = ['/ImageFrame_1_1_1_', num2str(range(i))];
    
    frame_data = h5read('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', frame_name);

    % extract and reformat the data
    gray_frame = frame_data(2,:,:);
    gray_frame = squeeze(gray_frame);
    imshow(gray_frame);


    stack(:,:,i) = gray_frame;
end

% move first dimension to the back
% color_frame = permute(frame_data, [2 3 1]);
% imshow(color_frame);
% 
% gray_frame = im2gray(color_frame);
% imshow(gray_frame);

