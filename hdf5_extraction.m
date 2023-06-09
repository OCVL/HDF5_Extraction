% HDF5 data extractor
% Created by: Jenna Grieshop
% Date created: 3/29/2023
%
% Purpose: Extract data from HDF5 files and save data as uncompressed
% grayscale AVIs


clear all
close all force
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
    
    % get and print out the session notes from the file
    notes_data = h5read(fPath, '/Notes');       
    notes_string = convertCharsToStrings(notes_data.Value);
    notes_split = notes_string.split('"');
    notes_field = notes_split(12);
    
    disp(notes_field);
    
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
            
            
            
            
    
            meta_name = ['/ScanMetaData_', num2str(a), '_1_', num2str(b)];
    
            try
                frm_metadata = h5read(fPath, meta_name);

                datcontents=cellstr(frm_metadata.Data');
                valcontents=cellstr(frm_metadata.Value');

                countind = find(startsWith(datcontents,'FrameCount'));

                numfrms = str2double(valcontents{countind});
                                
                % initialize everything needed to write the tiff stack
                file_name = [eye, '_', vid, '.tif'];
                t = Tiff(file_name, 'w');
                tagstruct.ImageLength = 448;
                tagstruct.ImageWidth = 640;
                tagstruct.BitsPerSample = 16;
                tagstruct.SamplesPerPixel = 1;
                tagstruct.Compression = Tiff.Compression.None;
                tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
                tagstruct.Photometric = Tiff.Photometric.MinIsBlack;
                
            catch
                % if the video doesn't exist move to the next possibility
                continue;
            end
    
            % for loop to go through each frame
            % 7 second vid = 209 (210 frames)
            % 10 second vid = 299 (300 frames)
            for c = 0:numfrms-1

                c;  
                
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

                % add frame to stack
                stack(:,:,c+1) = gray_frame(33:end,:);    
            end
            
            %% Filter out scanner salt/pepper with an adaptive filter.
            [threshes] = quantile(stack(:),[0.005, 0.995]);
            
            for c = 1:numfrms
                frm=stack(:,:,c);
                
                blurinds = find(frm < threshes(1))'; % | frm > threshes(2))';
                blurinds = [blurinds find( frm > threshes(2))'];
                figure(1);
                subplot(1,2,1);
                imagesc(frm); colormap gray; axis image;
                
                for i=blurinds
                    up = i-1;
                    down = i+1;
                    left = i-size(frm,1);
                    right = i+size(frm,1);
                    
%                     [ii,jj]=ind2sub(size(frm),i);
%                     if ii==189 && jj== 407
%                        ii 
%                     end
%                     [ii,jj]=ind2sub(size(frm),up)
%                     [ii,jj]=ind2sub(size(frm),down)
%                     [ii,jj]=ind2sub(size(frm),right)
%                     [ii,jj]=ind2sub(size(frm),left)
                    
                    frm(i)=0;
                    num=0;
                    
                    if up > 1 && frm(up) > threshes(1) && frm(up) < threshes(2)
                        frm(i) = frm(i)+frm(up);
                        num=num+1;
                    end                    
                    if down < mod(i,size(frm,1)) && frm(down) > threshes(1) && frm(down) < threshes(2)
                        frm(i) = frm(i)+frm(down);
                        num=num+1;
                    end
                    if left > 1 && frm(left) > threshes(1) && frm(left) < threshes(2)
                        frm(i) = frm(i)+frm(left);
                        num=num+1;
                    end
                    if right < length(frm(:)) && frm(right) > threshes(1) && frm(right) < threshes(2)
                        frm(i) = frm(i)+frm(right);
                        num=num+1;
                    end
                    
                    frm(i) = frm(i)/num;                                        
                end
                
                stack(:,:,c)=frm;
                
                subplot(1,2,2);
                imagesc(stack(:,:,c)); colormap gray; axis image;
                drawnow;
               
                
            end
            
            %% write the tiff stack
            for ii=1:size(stack,3)
               setTag(t,tagstruct);
               write(t,stack(:,:,ii));
               writeDirectory(t);
            end
            close(t)
        end
    end
end