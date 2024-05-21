# -*- coding: utf-8 -*-
"""
Created on Tue May 14 22:37:13 2024

@author: joahb
this file uses a cdf file and generates plots of irradiance vs time for both 
diode A and C then finds the integrated energy (area under each curve)
"""
import os
os.environ["CDF_LIB"] = "~/CDF/lib"
from spacepy import pycdf
import matplotlib.pyplot as plt
from scipy.integrate import simps
import numpy as np


cdf = pycdf.CDF('myCDF.cdf')
#print all the variables with details about the length
print(cdf)

''' cdfs are basically a dictionary of data, when running print (cdf) or 
print(cdf.keys()) we get all the
essesntial information about the file and the different lists 
to retrieve a specific value from the file we have to specify the index and the name of 
list'''


#how many variables? 
print(len(cdf))
'''
#only print the names of all variables
for k in cdf:
    print (k)
'''
''' 
#prints all the values of 'data' from the file
print(cdf['data'][:]) 
'''
'''
 #print 1st entry of each 3, so this is diode A data
print(cdf['data'][:,0]) 
print(cdf['time_unix'][:])
'''

#print(len(cdf['data']))
#print(cdf['flag'][:])

#filtering data for good solar conditions which is 'flag'=0
filtered_time = []
filtered_data = [] 
for i in range(len(cdf['data'])):
    if cdf['flag'][i] == 0:
        filtered_time.append(cdf['time_unix'][i])
        filtered_data.append(cdf['data'][i,0])
#make lists into numpy arrays for easier access
filtered_time = np.array(filtered_time)
filtered_data = np.array(filtered_data)
'''
#making sure that the number of zeros in 'flag' is the same as the length of 
#both filtered time and filtered data 
zero_count = 0 
for value in cdf['flag']:
    if value == 0:
        zero_count += 1 
print (zero_count)  
print(len(filtered_data))
print(len(filtered_time))
'''

# Check for and handle negative values (negative values not expected)
if np.any(filtered_data < 0):
    print("Warning: Negative irradiance values found, taking absolute values.")
    filtered_data = np.abs(filtered_data)
    
#plot of irradinace vs time for good solar conditions only
plt.scatter(filtered_time,filtered_data)
plt.xlabel('time (s)')
plt.ylabel('irradiance (Watts/m^2)')
plt.title ('irradiance vs time diode A')
plt.show()

#now to find the area under the graph (integrated energy)
area_trapz = np.trapz(filtered_data, filtered_time)
area_simps = simps(filtered_data, filtered_time)
print('diode A:')
print(f"Area using trapezoidal rule: {area_trapz} Watts*s/m^2")
print(f"Area using Simpson's rule: {area_simps} Watts*s/m^2")
filtered_time = []
filtered_data = [] 

#diode c stuff:
for i in range(len(cdf['data'])):
    if cdf['flag'][i] == 0:
        filtered_time.append(cdf['time_unix'][i])
        filtered_data.append(cdf['data'][i,2])

#plot of irradinace vs time for good solar conditions only
plt.scatter(filtered_time,filtered_data)
plt.xlabel('time (s)')
plt.ylabel('irradiance (Watts/m^2)')
plt.title ('irradiance vs time diode C')
plt.show()

#now to find the area under the graph (integrated energy)
area_trapz = np.trapz(filtered_data, filtered_time)
area_simps = simps(filtered_data, filtered_time)
print('diode C')
print(f"Area using trapezoidal rule: {area_trapz} Watts*s/m^2")
print(f"Area using Simpson's rule: {area_simps} Watts*s/m^2")
'''
#plot of irradinace vs time for all conditions (for comparison purposes)
irrad_A = [(cdf['data'][:,0])]
time_insec=[(cdf['time_unix'][:])]
plt.scatter(time_insec,irrad_A)
plt.show()
'''

