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

% v = VideoWriter('test.avi', 'Grayscale AVI');
% open(v)

t = Tiff('testing.tif', 'w');

tagstruct.ImageLength = 480;
tagstruct.ImageWidth = 640;
tagstruct.BitsPerSample = 16;
tagstruct.SamplesPerPixel = 1;
tagstruct.Compression = Tiff.Compression.None;
tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
tagstruct.Photometric = Tiff.Photometric.MinIsBlack; 

setTag(t,tagstruct);

for i = 0:209
    
    frame_name = ['/ImageFrame_1_1_1_', num2str(i)];
    
    frame_data = h5read('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', frame_name);
    frame_data = im2uint16(frame_data);
    

    % extract and reformat the data
    msb = frame_data(1,:,:);
    msb = squeeze(msb);
%     msb = (msb - 8);
%     msb = msb / 256;
    
    msb = (msb - 8);
    msb = msb * 256;
    
    lsb = frame_data(2,:,:);
    lsb = squeeze(lsb);
%     lsb = (lsb - 8);
%     lsb = lsb / 256;
    
    gray_frame = msb + lsb;
    gray_frame = rot90(gray_frame);
    imshow(gray_frame);


%     writeVideo(v, gray_frame);

%     stack(:,:,i+1) = gray_frame;
%     write(t, gray_frame);
end

% stack = im2uint16(stack);





close(t);



% for x = 1:length(stack)
%         imwrite(stack(:,:,:,x),'All_frames.tif', 'Compression', 'none','WriteMode', "append");
% end

% close(v)


%%


stack = zeros(480,640,'uint16');


for i = 0:209
    
    frame_name = ['/ImageFrame_1_1_1_', num2str(i)];
    
    frame_data = h5read('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', frame_name);
%     frame_data = im2uint16(frame_data);
    

    % extract and reformat the data
    g = frame_data(1,:,:);
    g = squeeze(g);
    
    r = frame_data(2,:,:);
    r = squeeze(r);

    
    combined = r * 256 + g;
    combined = rot90(combined);
    combined = floor(combined / 2);
    imshow(combined);

end

