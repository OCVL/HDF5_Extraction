% HDF5 data extractor
% Created by: Jenna Grieshop
% Date created: 3/29/2023
%
% Purpose: Extract data from HDF5 files and save data as uncompressed
% grayscale AVIs


clear all
close all
clc

% initialize the stack matrix

thisfolder = pwd;
thisfolder = uigetdir(thisfolder, 'Select the folder containing the CLight hdf5 data.');
    
[filelist]=read_folder_contents(thisfolder, 'hdf5');

%% load in the files

% h5disp('fef748ff-4fb2-4bcf-958b-eef4bf765240.hdf5');
for file=filelist'
    
    ftgray=[];
    fPath = fullfile(thisfolder, file{1});
    
    % for loop to go through eyes
    for a = 0:1
    
        stack = zeros(448,640,'uint16');
        
        if a == 0
            eye = 'OD';
        else
            eye = 'OS';
        end
        
        % for loop to go through video number
        for b = 0:2
            if b == 0
                vid = 'vid_0';
            elseif b == 1
                vid = 'vid_1';
            else
                vid = 'vid_2';
            end
            
            
            % initialize everything needed to write the tiff stack
            file_name = [eye, '_', vid, '.tif'];
            t = Tiff(file_name, 'w');
            tagstruct.ImageLength = 480;
            tagstruct.ImageWidth = 640;
            tagstruct.BitsPerSample = 16;
            tagstruct.SamplesPerPixel = 1;
            tagstruct.Compression = Tiff.Compression.None;
            tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
            tagstruct.Photometric = Tiff.Photometric.MinIsBlack;
            
    
            meta_name = ['/ScanMetaData_', num2str(a), '_1_', num2str(b)];
    
            frm_metadata = h5read(fPath, meta_name);

            datcontents=cellstr(frm_metadata.Data');
            valcontents=cellstr(frm_metadata.Value');
            
            countind = find(startsWith(datcontents,'FrameCount'));

            numfrms = str2double(valcontents{countind});
    
            % for loop to go through each frame
            % 7 second vid = 209 (210 frames)
            % 10 second vid = 299 (300 frames)
            for c = 0:numfrms-1
                c  
                frame_name = ['/ImageFrame_', num2str(a), '_1_', num2str(b), '_', num2str(c)];
    
                % read in the frame data and convert to uint16
                frame_data = h5read(fPath, frame_name);
                frame_data = uint16(frame_data);
    
    
                % extract and reformat the data
                msb = frame_data(1,:,:);
                msb = squeeze(msb);
    
                msb = (msb - 8);
                msb = msb * 256;
    
                lsb = frame_data(2,:,:);
                lsb = squeeze(lsb);
    
                gray_frame = msb + lsb;
                gray_frame = rot90(gray_frame, -1);

                frm_size = size(gray_frame);
                %padim = double(gray_frame).*(kaiser(size(gray_frame,1))*kaiser(size(gray_frame,2))');
                padim = padarray(gray_frame, size(gray_frame), 0,'post');
                
                % Design a notch filter.
                r = 0:87:size(padim,2);                
                midind = ceil(length(r)/2);
                r = r-r(midind);
                r = [r(1:(midind-1)) r((midind+1):end)];

                noiseangle = 34;

                th = repmat(-noiseangle*(pi/180), 1, length(r));

                [notchx, notchy] = pol2cart(th, r);
                notchx = notchx+ceil(size(padim,2)/2)+1;
                notchy = notchy+ceil(size(padim,1)/2)+1;

                notchfilter = ones(size(padim));
                notchfilter(sub2ind(size(notchfilter), round(notchy), round(notchx))) = 0;
                notchfilter=imerode(notchfilter, strel('disk',10, 0));
                notchfilter = imgaussfilt(notchfilter,2);


                ftgray(:,:,c+1)=fftshift(fft2(padim)).*notchfilter;
                figure(1);
                clf;
                imagesc(log10(abs(mean(ftgray,3)).^2)); colormap gray; hold on;
%                 plot(notchx, notchy, 'r*');
                drawnow;

                figure(2);
                subplot(1,2,1);
                imagesc(gray_frame); colormap gray;
                

                gray_frame = real(ifft2(ifftshift(ftgray(:,:,c+1))));
                gray_frame = gray_frame(1:frm_size(1),1:frm_size(2));
                subplot(1,2,2);
                imagesc( gray_frame ); colormap gray;

                pause(0.01);
                % add frame to stack
                stack(:,:,c+1) = gray_frame(33:end,:);
    
            end
            % write the tiff stack
            for ii=1:size(stack,3)
               setTag(t,tagstruct);
               write(t,stack(:,:,ii));
               writeDirectory(t);
            end
            close(t)
        end
    end
end