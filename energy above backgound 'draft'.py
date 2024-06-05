# -*- coding: utf-8 -*-
"""
Created on Thu May 23 17:52:55 2024

@author: joahb
In this file I am trying to automate the process of looking at the date in flare 
catalog and then finding the matching EUV data file to be able to run further
analysis easily
"""
import requests
from bs4 import BeautifulSoup
import os
import numpy as np
from scipy.integrate import simps
from spacepy.pycdf import CDF
import matplotlib.pyplot as plt
import csv
'''
#we only want to work with high energy flares, so we filter the list for them
def check_flare_classes(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()[16:]  # Skip the first 16 lines (index 0-15)
        results = []
        for line in lines:
            # Strip the line to remove any surrounding whitespace and then check the last four characters
            if line.strip()[-4:].startswith('M'):
                results.append(True)
            else:
                results.append(False)
                
        return results

# Example usage:
file_path = 'flare catalog.txt'
results = check_flare_classes(file_path)
for i, result in enumerate(results, start=17):
    print(f"Line {i}: {result}")
'''

#first function returns true or false, this one returns the number of lines
def check_lines_for_M(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()[16:]  # Skip the first 16 lines (index 0-15)
        matching_lines = []
        for i, line in enumerate(lines, start=17):  # Start line numbering from 17
            # Strip the line to remove any surrounding whitespace and then check the last four characters
            if line.strip()[-4:].startswith('M'):
                matching_lines.append(i)
                
        if matching_lines:
            print("Lines where the last four characters contain an 'M':", matching_lines)
        else:
            print("No lines found where the last four characters contain an 'M'.")

# Example usage:
file_path = 'flare catalog.txt'
check_lines_for_M(file_path)


def get_cdf_files(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    cdf_files = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.cdf')]
    return cdf_files

def match_dates_with_cdf(file_path, cdf_urls):
    with open(file_path, 'r') as file:
        lines = file.readlines()[16:]  # Skip the first 16 lines (index 0-15)
        matched_dates = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line[-4:].startswith('M'):
                date = stripped_line.split()[0]  # Extract the date part from the line
                month, day, year = date.split('/')
                date_formatted = f"{year}{month.zfill(2)}{day.zfill(2)}"  # Convert to CDF filename format
                print(f"Processing date: {date}")
                for base_url, cdf_url in cdf_urls:
                    if date_formatted in cdf_url:
                        full_url = base_url + cdf_url
                        matched_dates.append((date, full_url))
                        print(f"Match found - Date: {date}, CDF URL: {full_url}")
                        break  # No need to check other URLs once a match is found
        return matched_dates

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
for date, full_url in matched_dates:
    print(f"Date: {date}, Full URL: {full_url}")
    
print(matched_dates)

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
        'filtered_time': filtered_time,
        'filtered_data_diode_a': filtered_data_diode_a,
        'filtered_data_diode_c': filtered_data_diode_c,
        'area_trapz_a': area_trapz_a,
        'area_simps_a': area_simps_a,
        'area_trapz_c': area_trapz_c,
        'area_simps_c': area_simps_c
    }

results = []

output_file = 'cdf_analysis_results.csv'
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Date', 'File', 'Area Trapz Diode A', 'Area Simps Diode A', 'Area Trapz Diode C', 'Area Simps Diode C'])

    for date, file_url in matched_dates:
        print(f"Processing file for date: {date}")
        result = process_cdf(file_url)
        results.append(result)
        
        # Write result to the CSV file
        writer.writerow([
            date, 
            result['file'], 
            result['area_trapz_a'], 
            result['area_simps_a'], 
            result['area_trapz_c'], 
            result['area_simps_c']
        ])
        
        # Plot irradiance vs time for Diode A
        plt.figure()
        plt.plot(result['filtered_time'], result['filtered_data_diode_a'], label='Diode A')
        plt.xlabel('Time (Unix)')
        plt.ylabel('Irradiance')
        plt.title(f'Irradiance vs Time for Diode A on {date}')
        plt.legend()
        plt.show()

        # Plot irradiance vs time for Diode C
        plt.figure()
        plt.plot(result['filtered_time'], result['filtered_data_diode_c'], label='Diode C')
        plt.xlabel('Time (Unix)')
        plt.ylabel('Irradiance')
        plt.title(f'Irradiance vs Time for Diode C on {date}')
        plt.legend()
        plt.show()
        
        # Print areas under the curve
        print(f"File: {result['file']}")
        print(f"Area under curve for Diode A (trapz): {result['area_trapz_a']}")
        print(f"Area under curve for Diode A (simps): {result['area_simps_a']}")
        print(f"Area under curve for Diode C (trapz): {result['area_trapz_c']}")
        print(f"Area under curve for Diode C (simps): {result['area_simps_c']}")

# Optionally, save results to a file or further process them
print(f"Results have been saved to {output_file}")

