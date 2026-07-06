import glob
import os
from tkinter.filedialog import askdirectory
import datetime

import h5py
import numpy as np
from PIL import Image
from tifffile import imwrite

#obtain path to hdf5 file
def collect_paths(directory):
    folder = askdirectory()
    return glob.glob(os.path.join(folder, "*hdf5"))

#extraxt metadata: filename, timestamp, fPath
def extract_metadata(fPaths):
    file_info = []

    for fp in fPaths:
        try:
            with h5py.File(fp, "r") as f:
                meta_data = f["ImagingSessionMetaData"]
                value = meta_data["Value"][()]
                value_string = b''.join(value).decode()
                timestamp = int(value_string[:17])

                file_info.append({
                    "filename": os.path.basement(fp),
                    "timestamp": timestamp,
                    "path": fp
                })
            print(f"Metadata extracted successfully!")
        except Exception:
            print(f"Metadata extraction failed: {fp}")

    return sorted(file_info, key=lambda x: x["timestamp"])

#extract subject ID
def extract_subject_ID(fp):
    try:
        with h5py.File(fp, 'r') as f:
            notes_data = f["Notes"]["Value"][()]
            notes_string = b''.join(notes_data).decode()
            notes_split =  notes_string.split('"')
            subject_ID = notes_split[11]          #MatLab indicated subject ID may be at idex 32 instead of 12 with larger note fields
            notes_success = 1                           #Might try an if statement to address this if applicable

            if subject_ID == "notes":
                print(f"No notes recorded in Notes Field: {fp}")
                notes_success = 0
            return subject_ID

    except Exception:
        print(f"Notes Field failed for file: {fp}")
        notes_success = 0
        return None
def loop_eyes():
    return [0, 1] #OD, OS

def loop_vid():
    return [0, 1, 2]

def loop_frame(num_frames):
    return range(num_frames)

#extraxt msb and lsb
def extract_msb_and_lsb(fp, a, b, c):
    frame_name = f"/ImageFrame_{a}_1_{b}_{c}"

    with h5py.File(fp, 'r') as f:
        frame_data = f[frame_name][()].astype(np.uint16)

    msb = frame_data[:, :, 0].astype(np.uint16) - 8
    msb = msb * 256
    lsb = frame_data[:, :, 1].astype(np.uint16)

    gray_frame = msb + lsb
    gray_frame = np.flipud(gray_frame)
    gray_frame = gray_frame[8:, :]  # now (472, 640)

    return gray_frame

 # data is 11 bits and must be converted to 16

#reconstuct frames from funky rgb to 11-bit frames

#apply invert to frames


#frame subtraction, autodetection: detects dark frames, averages the frames, and subtract the average from the entire video


#save tiff file

#save avi file

#run the main process








folder = askdirectory()
fPaths = glob.glob(os.path.join(folder, '*.hdf5'))
file_info =  []

#defines info extraction from files
def extract_info_chronologically():
    file_info.clear()

    for fp in fPaths:
        with h5py.File(fp, 'r') as f:              #read hdf5 file
            try:
                meta_data = f["ImagingSessionMetaData"]       #find the image session metadata in the file
                value = meta_data["Value"][()]                #find the value in the metadata
                value_string = b''.join(value).decode()       #combine array of bytes into a string and convert to python string
                timestamp = int(value_string[:17])            #take the first 17 character, this is the datetime

                filename = os.path.basename(fp)               #retrieve filename
                #list structure
                file_info.append({
                    "filename" : filename,
                    "timestamp" : timestamp,
                    "path" : fp
                })
            except:
                print("Extraction failed. Imaging Session Meta Data not found. ")

    file_info_sorted = sorted(file_info, key=lambda x: x["timestamp"]) #sort by timestamp
    print("Extraction completed successfully.")
    return file_info_sorted

extract_info_chronologically()

def load_files():
    file_info_sorted = extract_info_chronologically()
    for item in file_info_sorted:
        fp = item["path"]
        filename = item["filename"]

        date_timestamp = os.path.getmtime(fp)
        date_string = datetime.datetime.fromtimestamp(date_timestamp).strftime('%Y_%m_%d')

        print(fp, filename, date_string)

def subject_ID():
    file_info = load_files()
    with h5py.File(fp, 'r') as f:
        try:
            notes_data = f["Notes"]["Value"][()]
            notes_string = b''.join(notes_data).decode()
            notes_split = notes_string.split('"')
            subject_ID = notes_split[11]  # MatLab indicated subject ID may be at idex 32 instead of 12 with larger note fields
            notes_success = 1  # Might try an if statement to address this if applicable

            if subject_ID == "notes":
                print(f"No notes recorded in Notes Field: {fp}")
                notes_success = 0

        except Exception:
            print(f"Notes Field failed for file: {fp}")
            notes_success = 0

#defines conversion function for the frame
def convert_funky_rgb_frame_to_11_bit_frame(frame):
    frame = frame.astype('uint16')

    g = frame[:, :, 1]  # 8 least significant bits, all rows/columns but green channel
    r = frame[:, :, 0]  # 8 most significant bits, all rows/columns bur red channel

    r = r - 8
    r = r * 256
    combined = r + g

    return combined

frames = np.zeros((480, 640), dtype='uint16')
good_frame = []
alist = []

with h5py.File('ec00615c-fa36-4732-b9dc-72c7901e7f5e.hdf5', "r") as f:
    # Print keys
    # print("Keys: %s" % f.keys())
    """ instead of hardcoding the 210 frames
    have the system read the number of frames present in the file first
    then range will be this variable
    num_frames = lens(f.keys)
    for i in range(num_frames):
"""
    first = 1
    for i in range(0,210):

        # get first object name/key
        a_group_key = list(f.keys())[i]

        # get the object type for a_group_key
        # print(type(f[a_group_key]))

        # If a_group_key is a group name,
        # this gets the object names in the group and returns as a list
        #data = list(f[a_group_key])

        # If a_group_key is a dataset name,
        # this gets the dataset values and returns as a list
        #data = list(f[a_group_key])
        # preferred methods to get dataset values:
        #ds_obj = f[a_group_key]      # returns as a h5py dataset object
        ds_arr = f[a_group_key][()]  # returns as a numpy array

        good_frame = convert_funky_rgb_frame_to_11_bit_frame(ds_arr)
        # x = good_frame[:,0]
        # y = good_frame[0,:]
        alist.append(good_frame)


        img = Image.fromarray(good_frame)
        Image.fromarray(good_frame.astype('uint16'), mode=None).save('pic2_2.tif')
    imwrite('multipage.tif', alist)
    # img.show()
    print('hi')


