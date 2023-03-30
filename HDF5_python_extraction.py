import h5py
import numpy as np
from PIL import Image
from tifffile import imwrite

def convert_funky_rgb_frame_to_11_bit_frame(frame):
    g = frame[:, :, 1]  # 8 least significant bits
    r = frame[:, :, 0]  # 8 most significant bits

    r = r - 8
    r = r * 256
    combined = r + g

    return combined

frames = np.zeros((480, 640), dtype='uint16')
good_frame = []
alist = []

with h5py.File('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', "r") as f:
    # Print keys
    # print("Keys: %s" % f.keys())

    first = 1
    for i in range(0,210):

        # get first object name/key
        a_group_key = list(f.keys())[i]

        # get the object type for a_group_key
        # print(type(f[a_group_key]))

        # If a_group_key is a group name,
        # this gets the object names in the group and returns as a list
        data = list(f[a_group_key])

        # If a_group_key is a dataset name,
        # this gets the dataset values and returns as a list
        data = list(f[a_group_key])
        # preferred methods to get dataset values:
        ds_obj = f[a_group_key]      # returns as a h5py dataset object
        ds_arr = f[a_group_key][()]  # returns as a numpy array

        good_frame = convert_funky_rgb_frame_to_11_bit_frame(ds_arr)
        # x = good_frame[:,0]
        # y = good_frame[0,:]
        # alist.append(good_frame)


        # img = Image.fromarray(good_frame)
        # Image.fromarray(good_frame.astype('uint16'), mode=None).save('pic2_2.tif')
    imwrite('multipage.tif', alist)
    # img.show()
    print('hi')


