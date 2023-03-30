% HDF5 data extractor
% Created by: Jenna Grieshop
% Date created: 3/29/2023
%
% Purpose: Extract data from HDF5 files and save data as uncompressed
% grayscale AVIs


% clear all
% close all
% clc

stack = zeros(480,640,'uint16');

%% load in the file

% h5disp('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5');

t = Tiff('testing.tif', 'w');

tagstruct.ImageLength = 480;
tagstruct.ImageWidth = 640;
tagstruct.BitsPerSample = 16;
tagstruct.SamplesPerPixel = 1;
tagstruct.Compression = Tiff.Compression.None;
tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
tagstruct.Photometric = Tiff.Photometric.MinIsBlack; 


for i = 0:209
    
    frame_name = ['/ImageFrame_1_1_1_', num2str(i)];
    
    frame_data = h5read('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', frame_name);
    frame_data = uint16(frame_data);
    

    % extract and reformat the data
    msb = frame_data(1,:,:);
    msb = squeeze(msb);
    
    msb = (msb - 8);
    msb = msb * 256;
    
    lsb = frame_data(2,:,:);
    lsb = squeeze(lsb);

    gray_frame = msb + lsb;
    gray_frame = rot90(gray_frame, 3);

    stack(:,:,i+1) = gray_frame;

end



for ii=1:size(stack,3)
   setTag(t,tagstruct);
   write(t,stack(:,:,ii));
   writeDirectory(t);
end
close(t)






