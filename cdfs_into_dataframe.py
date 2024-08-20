# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 15:13:53 2024

@author: joahb + Dr. Ross

without referring to the flare catalog,
Loop over each CDF file in the folder we give it (all the 2023 CDFs, and 2022 too probably, and 2024).
	Load up the CDF file, translate it into a Pandas Dataframe, append it to our EUV-dataframe-so-far.
Write out that huge EUV dataframe just so we dont have to create it again.
"""

#make a list of cdf files 

import os
from spacepy.pycdf import CDF
import numpy as np
import pandas as pd

def cdf_to_np(cdfdata,filename):
    npdata = dict()
    npdata['filename'] = filename
    # doing np.array(cdfdata[whatever field]) takes a long time.
    # This page, https://stackoverflow.com/questions/71921517/why-is-numpy-too-slow-when-extracting-data-from-cdf-files-using-pycdf
    # mentions that specifying the data type can help speed it up!
    npdata['time_unix'] = np.array(cdfdata['time_unix'],dtype=np.float64)
    npdata['maven_sun_distance'] = np.array(cdfdata['maven_sun_distance'],dtype=np.float64)
    npdata['flag'] = np.array(cdfdata['flag'],dtype=np.int64) # though we'd probably be ok with int32 or even smaller
    np_data=np.array(cdfdata['data'],dtype=np.float32)
    npdata['data_a']=np.squeeze(np_data[:,0])
    npdata['data_c']=np.squeeze(np_data[:,2])
    #all other lines need squeezing to work
    #np_ddata=np.array(cdfdata['ddata'],dtype=np.float32)
    #npdata['ddata_a']=np_ddata[:,0]
    #npdata['ddata_c']=np_ddata[:,2]
    #npdata['data'] = np.array(cdfdata['data'],dtype=np.float32)
    #npdata['ddata'] = np.array(cdfdata['ddata'],dtype=np.float32)
    #npdata['dfreq'] = np.array(cdfdata['dfreq'],dtype=np.float32)
    #npdata['counts'] = np.array(cdfdata['counts'],dtype=np.float32)
    # We'd like to do:
    # npdata['epoch'] = np.array(cdfdata['epoch']) # TT2000 time, which should be just like unix time except for something like 30 leap seconds
    # but TT2000 times are represented as datetime.datetime objects, so we need to do something like:
    #npdata['epoch'] = np.array([t.timestamp() for t in cdfdata['epoch']],dtype=np.float64)
    npdata['time_unix_min'] = np.min(npdata['time_unix']) # might want that so all time values have the same base value regardless of later filtering
    df=pd.DataFrame(npdata)
    return df

# Get the current directory
current_directory = os.getcwd()

# Get a list of all files in the current directory ending with .cdf
cdf_files = [f for f in os.listdir(current_directory) if f.endswith('r01.cdf')]
print(cdf_files)

npdata_dict = dict()
for filename in cdf_files:
    print(filename)
    cdfdata = CDF(filename)
    #npdata_dict[filename] = cdf_to_np(cdfdata,filename)
    df = cdf_to_np(cdfdata,filename)
    #filter using the flag=0 
    df = df.loc[df['flag'] == 0]
    filename_csv= filename.replace('cdf','csv')
    df.to_csv(filename_csv)
    npdata_dict[filename]=df
    
# Method 1: Using pd.concat()
combined_df = pd.concat(npdata_dict.values(), ignore_index=True)


#np_ddata=np.array(cdfdata['ddata'],dtype=np.float32)
#npdata['ddata_a']=np_ddata[:,0]

