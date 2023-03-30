import h5py
import numpy as np
from PIL import Image

def convert_funky_rgb_frame_to_11_bit_frame(frame):
    g = frame[:, :, 1]  # 8 least significant bits
    r = frame[:, :, 0]  # 8 most significant bits

    r = r - 8
    r = r * 256
    combined = r + g
    # combined = r * 256 + g
    # combined = combined // 2
    return combined



with h5py.File('2529f11b-6c60-4bd9-b580-f37d9665ca65.hdf5', "r") as f:
    # Print all root level object names (aka keys)
    # these can be group or dataset names
    print("Keys: %s" % f.keys())
    # get first object name/key; may or may NOT be a group
    a_group_key = list(f.keys())[0]

    # get the object type for a_group_key: usually group or dataset
    print(type(f[a_group_key]))

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
    img = Image.fromarray(good_frame)
    Image.fromarray(good_frame.astype('uint16'), mode=None).save('pic2_2.tif')
    # img.show()
    print('hi')


