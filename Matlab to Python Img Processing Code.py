# practice code for hdf5 extraction :)

import glob
import os
from tkinter.filedialog import askdirectory
import cv2

import h5py
import numpy as np
import tifffile

from skimage.transform import resize
import datetime
import matplotlib.pyplot as plt

#prompt user to locate folder
folder = askdirectory()
fPaths = glob.glob(os.path.join(folder, "*.hdf5"))

#reading/storing HDF5 metadata
file_info = []

# extraxt filename and timestamp from each file and order chronologically
for fp in fPaths:
    f = h5py.File(fp, 'r')                 #read hdf5 files
    meta_data = f["ImagingSessionMetaData"]      #find the image session metadata in the file
    value  = meta_data["Value"][()]              #find the value in the metadata
    value_string =  b''.join(value).decode()     #combine array of bytes into a string and convert to python string
    timestamp = int(value_string[:17])           #take the first 17 characters, this is the datetime

    filename = os.path.basename(fp)              #retrieve filename
    file_info.append({                           #list structure
        "filename": filename,
        "timestamp": timestamp,
        "path": fp
    })

file_info_sorted = sorted(file_info, key=lambda x: x["timestamp"])  # sort list my timestamp for chronological order

#main loop for loading files in

for item in file_info_sorted:
    vid_count = -1
    fp = item["path"]
    filename = item["filename"]
    date_timestamp = os.path.getmtime(fp)
    date_string = datetime.datetime.fromtimestamp(date_timestamp).strftime("%Y_%m_%d")

    #attempt to get notes from the file to obtain subject_ID
    with h5py.File(fp, 'r') as f:
        try:
            notes_data = f["Notes"]["Value"][:]
            notes_string = b''.join(notes_data).decode()
            notes_split =  notes_string.split('"')
            subject_ID = notes_split[21]           #MatLab indicated subject ID may be at idex 32 instead of 12 with larger note fields
            vid_info = notes_split[11]
            notes_success = 1                      #Might try an if statement to address this if applicable

            if subject_ID == "notes":
                print(f"No notes recorded in Notes Field: {fp}")
                notes_success = 0

        except Exception:
            print(f"Notes Field failed for file: {fp}")
            notes_success = 0

        #dimension for the tiff and avi files
        Initial_height = 472
        Width = 640
        square_aspect = Width/480
        Target_height = round(Initial_height * square_aspect)

        #for loop to go through each eye in the scan
        for a in range(2):
            if a == 0:
                eye = "OD"
            else:
                eye = "OS"
            print(f"Processing eye: {eye}")

            #for loop to go through each video
            for b in range(3):
                vid_count += 1
                meta_name = f"ScanMetaData_{a}_1_{b}"       #metadata dataset name structure

                try:
                    from_metadata = f[meta_name][:]
                    print(f"Processing video number {b} for eye {eye}")

                    # Video Exist we continue working!
                    data_contents = from_metadata["Data"].astype(str)  # Gets the Data key from metadata
                    value_contents = from_metadata["Value"].astype(str)  # Gets the Value of each Data key from metadata

                    #debuggger # print(data_contents, value_contents)

                    # use above variables to find the frame count for each video
                    count_index = list(data_contents).index("FrameCount")  # finds index in metadata that holds the frame count number
                    num_frames = int(value_contents[count_index])  # uses the found frame count index to obtain the frame count value

                    # initializing info for tiff stack, prevent colons from breaking code/file naming
                    subject_ID = subject_ID.replace(":", "")

                    # creating file names
                    if notes_success:
                        file_name = f"{folder}/{vid_info}_session_subject_{subject_ID}_{date_string}_{eye}_{b}.tif"
                    else:
                        file_name = f"{folder}/{date_string}_{eye}_{b}.tif"

                except Exception:
                    vid_count -= 1
                    print(f"Video {b} missing for eye {eye} -- skipped.")
                    continue  #don't process anything else for this video

                #frame_list = []   possibly use for debugging purposes to see what is present in frame????

                #initialize stack to store frames
                stack = np.zeros((Target_height, Width, num_frames), dtype=np.uint16)

                frm_mean = np.zeros(num_frames)
                frm_stddev = np.zeros(num_frames)

                #for loop through each frame
                for c in range(num_frames):
                    frame_name = f"/ImageFrame_{a}_1_{b}_{c}"

                    # data is 11 bits and must be converted to 16
                    frame_data = f[frame_name][:].astype(np.uint16)

                    msb = frame_data[:, :, 0].astype(np.uint16)
                    msb = msb - 8
                    msb = msb * 256
                    lsb = frame_data[:, :, 1].astype(np.uint16)

                    gray_frame = msb + lsb

                    gray_frame = np.flipud(gray_frame)  # equivilant to the rotate code in matlab
                    gray_frame = gray_frame[0:Initial_height, :]  #now (472, 640)

                    frame_rescaled = resize(gray_frame, (Target_height, Width), preserve_range = True).astype(np.uint16)

                    #frame_rescaled = skimage.transform.rotate(frame_rescaled, 90)

                    stack[:, :, c] = frame_rescaled

                    #gray_frame480 = resize(gray_frame, (Target_height, Width), preserve_range=True).astype(np.uint16)
                    #gray_frame = gray_frame.astype(np.uint64)
                    frm_mean[c] = np.nanmean(gray_frame)
                    frm_stddev[c] = np.std(gray_frame)

                #-------------------------------------------------------------------------------------------------------
                #Need to fix this to correct frames...
                #import matplotlib.pyplot as plt

                mcount, meanedges = np.histogram(frm_mean, bins=int(np.divide(num_frames, 4)))
                mean_thresh = meanedges[1]
                scount, stdedges = np.histogram(frm_stddev, bins=int(np.divide(num_frames, 4)))
                stddev_thresh = stdedges[1]

                low_frames = stack[:, :, (frm_mean < mean_thresh) & (frm_stddev < stddev_thresh)]

                avg_low = np.nanmean(low_frames, axis=2).astype(np.uint16)

                norm_stack  = stack.astype(int) - avg_low[:,:, None].astype(int)
                norm_stack[norm_stack < 0] = 0
                #a_min = np.amin(temp.astype(np.int16))  # min value of stack
                # min_t = temp - a_min
                # a_max = np.amax(min_t.astype(np.int16))  # max value of stack
                # max_t = min_t / a_max
                norm_stack = norm_stack.astype(np.uint16)
                stack_8bit = norm_stack.astype(np.uint8)

                # normalizing the stack -- Brea's beautiful work
                # norm_stack = np.zeros_like(stack)
                # stack_8bit = np.zeros_like(stack)
                #
                # for i in range(0, num_frames):
                #     # Subtract avg_low from frame and save in new stack
                #     temp = stack[:, :, i].astype(np.int16) - avg_low.astype(np.int16)
                #     a_min = np.amin(temp)  # min value of stack
                #     min_t = temp - a_min
                #     a_max = np.amax(min_t)  # max value of stack
                #     max_t = min_t / a_max
                #     norm_stack[:, :, i] = (max_t * 65535).astype(np.uint16)
                #     stack_8bit[:, :, i] = (max_t * 255).astype(np.uint8)


                # -------------------------
                # Forming the TIFF file
                # -------------------------
                with tifffile.TiffWriter(file_name) as tif:
                    for ii in range(stack.shape[2]):
                        tif.write(
                            norm_stack[:,:,ii],
                            photometric="minisblack",
                            compression = None,
                            planarconfig= "contig",
                            dtype = np.uint16
                        )

                # -------------------------
                # Forming the AVI file
                # -------------------------

                #Quantization
                #quants = np.quantile(stack.flatten(), [0.001, 0.999])
                stack_norm = norm_stack.astype(float)
                stack_8bit = stack_norm /2047
                stack_8bit = (stack_8bit * 255).astype(np.uint8)

                #stack_norm = stack_norm - quants[0]
                #stack_norm = stack_norm / (quants[1] - quants[0])
                #stack_8bit = np.clip(stack_norm * 255, 0, 255).astype(np.uint8)
                # find 2^11... divide stack by that... and multiple by 255
                # alternate avi formating for saving - test
                avi_name = file_name.replace(".tif", ".avi")

                # Get the number of frames in the video pairs
                # Make the video writer
                code = cv2.VideoWriter.fourcc(*'Y800')
                avi_output = cv2.VideoWriter(avi_name, code, 30, (Width, Target_height), isColor=False)

                for i in range(0, stack.shape[-1]):
                    avi_output.write(stack_8bit[:, :, i].astype(np.uint8))

                avi_output.release()
