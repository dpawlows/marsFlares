# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 09:10:48 2024

@author: joahb
"""

import requests
from bs4 import BeautifulSoup
import os
import numpy as np
from scipy.integrate import simps
from spacepy.pycdf import CDF
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# Function to parse the flare catalog and extract M-class flares
def parse_flare_catalog(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()[16:]  # Skip the first 16 lines (index 0-15)
        flares = []
        for line in lines:
            parts = line.split()
            date_str = parts[0]
            start_time_str = parts[1]
            end_time_str = parts[3]
            flare_class = parts[4]
            if flare_class.startswith('M'):
                start_datetime = datetime.strptime(f"{date_str} {start_time_str}", "%m/%d/%Y %H:%M:%S")
                end_datetime = datetime.strptime(f"{date_str} {end_time_str}", "%m/%d/%Y %H:%M:%S")
                flares.append((start_datetime, end_datetime, flare_class))
        return flares

# Function to get CDF files from the URL
def get_cdf_files(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    cdf_files = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.cdf')]
    return cdf_files

# Function to match dates with CDF files
def match_dates_with_cdf(file_path, cdf_urls):
    flares = parse_flare_catalog(file_path)
    matched_dates = []
    for flare in flares:
        date = flare[0].strftime("%Y%m%d")
        for base_url, cdf_url in cdf_urls:
            if date in cdf_url:
                full_url = base_url + cdf_url
                matched_dates.append((flare[0], flare[1], full_url))
                break
    return matched_dates

# Function to process CDF files and compute areas
def process_cdf(file_url, start_time, end_time):
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
        
        for i in range(len(cdf['time_unix'])):
            current_time = datetime.utcfromtimestamp(cdf['time_unix'][i])
            if start_time <= current_time <= end_time and cdf['flag'][i] == 0:
                filtered_time.append(cdf['time_unix'][i])
                filtered_data_diode_a.append(cdf['data'][i, 0])
                filtered_data_diode_c.append(cdf['data'][i, 2])
        
        filtered_time = np.array(filtered_time)
        filtered_data_diode_a = np.array(filtered_data_diode_a)
        filtered_data_diode_c = np.array(filtered_data_diode_c)
        
        # Background subtraction
        if filtered_time.size > 0:
            start_idx = 0
            end_idx = -1
            background_a = np.linspace(filtered_data_diode_a[start_idx], filtered_data_diode_a[end_idx], len(filtered_data_diode_a))
            background_c = np.linspace(filtered_data_diode_c[start_idx], filtered_data_diode_c[end_idx], len(filtered_data_diode_c))
            
            filtered_data_diode_a -= background_a
            filtered_data_diode_c -= background_c
            
            # Check for and handle negative values
            filtered_data_diode_a = np.maximum(filtered_data_diode_a, 0)
            filtered_data_diode_c = np.maximum(filtered_data_diode_c, 0)
        
            # Compute area for Diode A
            area_trapz_a = np.trapz(filtered_data_diode_a, filtered_time)
            area_simps_a = simps(filtered_data_diode_a, filtered_time)
            
            # Compute area for Diode C
            area_trapz_c = np.trapz(filtered_data_diode_c, filtered_time)
            area_simps_c = simps(filtered_data_diode_c, filtered_time)
        else:
            area_trapz_a = area_simps_a = area_trapz_c = area_simps_c = 0
    
    # Cleanup temporary file after processing is done
    os.remove(temp_file_path)
    
    return {
        'file': os.path.basename(file_url),
        'filtered_time': filtered_time,
        'filtered_data_diode_a': filtered_data_diode_a,
        'filtered_data_diode_c': filtered_data_diode_c,
        'area_trapz_a': area_trapz_a,
        'area_simps_a': area_simps_a,
        'area_trapz_c': area_trapz_c,
        'area_simps_c': area_simps_c
    }

file_path = 'flare catalog.txt'
url_list = [
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/01/', 
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/02/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/03/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/04/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/05/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/06/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/07/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/08/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/09/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/10/',
    'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/11/'
]

cdf_urls = []
for url in url_list:
    cdf_files = get_cdf_files(url)
    cdf_urls.extend([(url, cdf_file) for cdf_file in cdf_files])

matched_dates = match_dates_with_cdf(file_path, cdf_urls)

# Print the matched dates with full URLs
for start_time, end_time, full_url in matched_dates:
    print(f"Start Time: {start_time}, End Time: {end_time}, Full URL: {full_url}")

output_file = 'cdf_analysis_results.csv'
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Start Time', 'End Time', 'File', 'Area Trapz Diode A', 'Area Simps Diode A', 'Area Trapz Diode C', 'Area Simps Diode C'])

    for start_time, end_time, file_url in matched_dates:
        print(f"Processing file from {start_time} to {end_time}")
        result = process_cdf(file_url, start_time, end_time)
        
        # Write result to the CSV file
        writer.writerow([
            start_time, 
            end_time, 
            result['file'], 
            result['area_trapz_a'], 
            result['area_simps_a'], 
            result['area_trapz_c'], 
            result['area_simps_c']
        ])
        
        # Plot irradiance vs time for Diode A and Diode C
        plt.figure()
        plt.plot(result['filtered_time'], result['filtered_data_diode_a'], label='Diode A')
        plt.plot(result['filtered_time'], result['filtered_data_diode_c'], label='Diode C')
        plt.xlabel('Time (Unix)')
        plt.ylabel('Irradiance')
        plt.title(f'Irradiance vs Time for Flare starting at {start_time}')
        plt.legend()
        plt.show()

print(f"Results have been saved to {output_file}")

