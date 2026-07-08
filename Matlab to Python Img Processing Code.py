# practice code for hdf5 extraction :)

import glob
import os
from tkinter.filedialog import askdirectory
import cv2

import h5py
import numpy as np
import skimage
import tifffile

import imageio.v2 as imageio
from skimage.transform import resize
import datetime

#initialize vid counter


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
            subject_ID = notes_split[11]           #MatLab indicated subject ID may be at idex 32 instead of 12 with larger note fields
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
                        file_name = f"{folder}/{subject_ID}_{date_string}_{eye}_{b}.tif"
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

                    gray_frame = gray_frame[8:, :]  #now (472, 640)
                    gray_frame = np.flipud(gray_frame)  # equivilant to the rotate code in matlab

                    frame_rescaled = resize(gray_frame, (Target_height, Width), preserve_range = True).astype(np.uint16)  #optional might remove?

                    #frame_rescaled = skimage.transform.rotate(frame_rescaled, 90)

                    stack[:, :, c] = frame_rescaled

                    frm_mean[c] = np.mean(gray_frame)
                    frm_stddev[c] = np.std(gray_frame.astype(float))

                #-------------------------------------------------------------------------------------------------------
                #Need to fix this to correct frames...
                #import matplotlib.pyplot as plt


                mcount, meanedges = np.histogram(frm_mean, bins= num_frames // 4)
                mean_thresh = meanedges[1]
                scount, stdedges = np.histogram(frm_stddev, bins= num_frames // 4)
                stddev_thresh = stdedges[1]

                low_frames = stack[:, :, (frm_mean < mean_thresh) & (frm_stddev < stddev_thresh)]

                avg_low = np.mean(low_frames,2).astype(np.uint16)
                stack = stack - avg_low[:, :, None]

                #commented out
                '''
                #matplotlib - load frm_mean into a matplotlib histogram
                
                

                 #if len(meanedges) > 1 else meanedges[0]
                 #if len(stdedges) > 1 else stdedges[0]

                mask = (frm_mean < mean_thresh) & (frm_stddev < stddev_thresh)

                

                if low_frames.shape[2] > 0:
                    avg_low = np.mean(low_frames, axis =2).astype(np.uint16)
                else:
                    avg_low = np.mean(stack, axis=2).astype(np.uint16)

                stack =  stack - avg_low[:, :, None] '''

                # correction is weird with python don't know why... it looks snow white when used
                # -------------------------------------------------------------------------------------------------------

                stack_clipped = np.clip(stack, 0, 65535).astype(np.uint16)
                stack_8bit = (stack_clipped / 256).astype(np.uint8)


                # -------------------------------------------------------------------------------------------------------
                '''stack_rescaled = np.zeros_like(stack_8bit)
                for c in range(num_frames):
                    stack_rescaled[:, :, c] = resize(
                        stack_8bit[:, :, c],
                        (Target_height, Width),
                        preserve_range = True
                    ).astype(np.uint8)'''
                #double purpose I think... no needed for now...
                # -------------------------------------------------------------------------------------------------------

                stack_rescaled = stack_8bit.copy()
                #tif_name = file_name.replace(".tif", "v1.tif")
                # -------------------------
                # forming the TIFF file
                # -------------------------
                with tifffile.TiffWriter(file_name) as tif:
                    for ii in range(stack.shape[2]):
                        # stack_clipped = resize(
                        #     stack[:, :,ii],
                        #     (Target_height, Width),
                        #     preserve_range=True
                        # ).astype(np.uint16)

                        tif.write(
                            stack_clipped[:,:,ii],
                            photometric="minisblack",
                            compression = None,
                            planarconfig= "contig",
                            dtype = np.uint16
                        )


                # print(stack.shape)
                # frame_list = np.empty((stack.shape[0], stack.shape[1], stack.shape[2]))
                # print("frame list", frame_list)
                # for aa in range(stack.shape[2]):
                #     frame_list[:, :, aa] = stack[:, :, aa]
                #
                # cv2.imwritemulti(str(tif_name), frame_list.astype(np.uint16))

                # -------------------------
                #Forming the AVI file
                # -------------------------

                #Quantization
                quants = np.quantile(stack.flatten(), [0.001, 0.999])
                stack_norm = stack.astype(float)
                stack_norm = stack_norm - quants[0]
                stack_norm = stack_norm / (quants[1] - quants[0])
                stack_8bit = np.clip(stack_norm * 255, 0, 255).astype(np.uint8)

                # alternate avi formating for saving - test
                #video_data = cv2.VideoCapture(file_name)
                avi_name = file_name.replace(".tif", ".avi")

                # Get the number of frames in the video pairs
                #frate = video_data.get(cv2.CAP_PROP_FPS) # get frame rate using HDF5 file

                # Make the video writer
                code = cv2.VideoWriter.fourcc(*'Y800')
                avi_output = cv2.VideoWriter(avi_name, code, 30, (Width, Target_height), isColor=False)

                for i in range(0, stack.shape[-1]):
                    avi_output.write(stack_8bit[:, :, i].astype(np.uint8))

                avi_output.release()
              
                # #AVI File formatting
                # avi_name = file_name.replace(".tif", ".avi")
                # writer = imageio.get_writer(
                #     avi_name,
                #     fps=30,
                #     format="FFMPEG",
                #     codec = "mjpeg",
                #     macro_block_size = 1
                # )
                #
                # for ii in range(stack_8bit.shape[2]):
                #     frame_rescaled = resize(
                #         stack_8bit[:, :, ii],
                #         (Target_height, Width),
                #         preserve_range=True
                #     ).astype(np.uint8)
                #     writer.append_data(frame_rescaled)
                #
                # writer.close()
                #
