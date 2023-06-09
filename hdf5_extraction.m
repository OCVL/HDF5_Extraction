% HDF5 data extractor
% Created by: Jenna Grieshop
% Date created: 3/29/2023
%
% Purpose: Extract data from HDF5 files and save data as uncompressed
% grayscale AVIs


clear all
close all
clc

% known pixel values corresponding to fixation target locaitons
right_edge = "300";
left_edge = "950";
center = "642";

% set default date format
datetime.setDefaultFormats('default', 'yyyyMMdd');

% initialize video number variable
vid_count = -1;

% initialize the stack matrix
thisfolder = pwd;
thisfolder = uigetdir(thisfolder, 'Select the folder containing the CLight hdf5 data.');
    
[filelist]=read_folder_contents(thisfolder, 'hdf5');

% get unix timestamps for each file
for i=1:length(filelist)
    fPath = fullfile(thisfolder, filelist{i});
    meta_data = h5read(fPath, '/ImagingSessionMetaData');
    time_stamp = str2double(convertCharsToStrings(meta_data.Value(1:17,1)));
    filelist{i,2} = time_stamp;
end

% sort filelist based on timestamps
filelist = sortrows(filelist,2);


%% load in the files

for file=filelist'
    
    ftgray=[];
    fPath = fullfile(thisfolder, file{1});
    fstruct = dir(fPath);
    date = datetime(fstruct.date);
    
    try
    % get notes from the file
    notes_data = h5read(fPath, '/Notes');
    notes_string = convertCharsToStrings(notes_data.Value);
    notes_split = notes_string.split('"');
    notes_field = notes_split(12); % if the correct notes entry is a second notes entry the number should be 32
    notes_field_split = notes_field.split("_");
    subject_id = notes_field_split(1);
    fixation_location_px = notes_field_split(2);
   
    catch
        warning('Notes field failed for file: %s', fPath);
        continue;
    end
    
    % for loop to go through eyes
    for a = 0:1
    
        stack = zeros(448,640,'uint16');
        
        if a == 0
            eye = 'OD';
            switch fixation_location_px
                case right_edge
                    fixation_location_deg = "4T";
                case left_edge
                    fixation_location_deg = "4N";
                case center
                    fixation_location_deg = "0";
                otherwise
                    warning("fixation location from notes field is not valid for file: %s", fPath);
                    continue;
            end
        else
            eye = 'OS';
            switch fixation_location_px
                case right_edge
                    fixation_location_deg = "4N";
                case left_edge
                    fixation_location_deg = "4T";
                case center
                    fixation_location_deg = "0";
                otherwise
                    warning("fixation location from notes field is not valid for file: %s", fPath);
                    continue;
            end
        end
        
        % for loop to go through video number
        for b = 0:2
            if b == 0
                vid = 'vid_0';
                vid_count = vid_count + 1;
            elseif b == 1
                vid = 'vid_1';
                vid_count = vid_count + 1;
            else
                vid = 'vid_2';
                vid_count = vid_count + 1;
            end
            
              
            meta_name = ['/ScanMetaData_', num2str(a), '_1_', num2str(b)];
    
            try
                frm_metadata = h5read(fPath, meta_name);

                datcontents=cellstr(frm_metadata.Data');
                valcontents=cellstr(frm_metadata.Value');

                countind = find(startsWith(datcontents,'FrameCount'));

                numfrms = str2double(valcontents{countind});
                                
                % initialize everything needed to write the tiff stack
                file_name = [subject_id, '_', string(date), '_', eye, '_', fixation_location_deg, '_', num2str(vid_count), '.tif'];
                file_name = strjoin(file_name, '');
                t = Tiff(file_name, 'w');
                tagstruct.ImageLength = 480;
                tagstruct.ImageWidth = 640;
                tagstruct.BitsPerSample = 16;
                tagstruct.SamplesPerPixel = 1;
                tagstruct.Compression = Tiff.Compression.None;
                tagstruct.PlanarConfiguration = Tiff.PlanarConfiguration.Chunky;
                tagstruct.Photometric = Tiff.Photometric.MinIsBlack;
                
            catch
                % if the video doesn't exist move to the next possibility
                warning("video doesn't exist");
                continue;
            end
    
            % for loop to go through each frame
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