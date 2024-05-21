# -*- coding: utf-8 -*-
"""
Created on Mon May 20 21:38:31 2024

@author: joahb
"""

import requests
from bs4 import BeautifulSoup
import os
import numpy as np
from scipy.integrate import simps
from spacepy.pycdf import CDF

# Function to process a single CDF file and compute areas under the curve
def process_cdf(file_url):
    response = requests.get(file_url)
    response.raise_for_status()
    
    # Save the CDF file content temporarily
    temp_file_path = 'temp.cdf'
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(response.content)
    
    # Load and process the CDF file within a context manager
    with CDF(temp_file_path) as cdf:
        # Filter data for good solar conditions (flag == 0)
        filtered_time = []
        filtered_data_diode_a = []
        filtered_data_diode_c = []
        
        for i in range(len(cdf['data'])):
            if cdf['flag'][i] == 0:
                filtered_time.append(cdf['time_unix'][i])
                filtered_data_diode_a.append(cdf['data'][i, 0])
                filtered_data_diode_c.append(cdf['data'][i, 2])
        
        filtered_time = np.array(filtered_time)
        filtered_data_diode_a = np.array(filtered_data_diode_a)
        filtered_data_diode_c = np.array(filtered_data_diode_c)
        
        # Check for and handle negative values
        if np.any(filtered_data_diode_a < 0):
            filtered_data_diode_a = np.abs(filtered_data_diode_a)
        
        if np.any(filtered_data_diode_c < 0):
            filtered_data_diode_c = np.abs(filtered_data_diode_c)
        
        # Compute area for Diode A
        area_trapz_a = np.trapz(filtered_data_diode_a, filtered_time)
        area_simps_a = simps(filtered_data_diode_a, filtered_time)
        
        # Compute area for Diode C
        area_trapz_c = np.trapz(filtered_data_diode_c, filtered_time)
        area_simps_c = simps(filtered_data_diode_c, filtered_time)
    
    # Cleanup temporary file after processing is done
    os.remove(temp_file_path)
    
    return {
        'file': os.path.basename(file_url),
        'area_trapz_a': area_trapz_a,
        'area_simps_a': area_simps_a,
        'area_trapz_c': area_trapz_c,
        'area_simps_c': area_simps_c
    }

# Step 1: Fetch the webpage content and extract CDF file links
url = 'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/08/'  # Replace with the actual URL containing the CDF files
response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, 'html.parser')
file_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.cdf')]

# Step 2: Process each CDF file and collect results
results = []

for file_link in file_links:
    file_url = file_link if file_link.startswith('http') else url + '/' + file_link
    result = process_cdf(file_url)
    results.append(result)

# Step 3: Output results to a file
output_file = 'cdf_analysis_results.txt'
with open(output_file, 'w') as f:
    for result in results:
        f.write(f"File: {result['file']}\n")
        f.write(f"Diode A - Area using trapezoidal rule: {result['area_trapz_a']} Watts*s/m^2\n")
        f.write(f"Diode A - Area using Simpson's rule: {result['area_simps_a']} Watts*s/m^2\n")
        f.write(f"Diode C - Area using trapezoidal rule: {result['area_trapz_c']} Watts*s/m^2\n")
        f.write(f"Diode C - Area using Simpson's rule: {result['area_simps_c']} Watts*s/m^2\n")
        f.write("\n")

print(f"Results have been written to {output_file}")
