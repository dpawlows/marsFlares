# -*- coding: utf-8 -*-
"""
Created on Sun Jun  9 13:22:39 2024

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

# Function to get CDF files from a URL
def get_cdf_files(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    cdf_files = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.cdf')]
    return cdf_files

# Function to match dates in the flare catalog with CDF files
def match_dates_with_cdf(file_path, cdf_urls):
    with open(file_path, 'r') as file:
        lines = file.readlines()[12:]  # Skip the first couple of lines
        matched_dates = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line[-4:].startswith('M'):
                date = stripped_line.split()[0]  # Extract the date part from the line
                month, day, year = date.split('/')
                date_formatted = f"{year}{month.zfill(2)}{day.zfill(2)}"  # Convert to CDF filename format
                for base_url, cdf_url in cdf_urls:
                    if date_formatted in cdf_url:
                        full_url = base_url + cdf_url
                        matched_dates.append((date, line, full_url))
                        break  # No need to check other URLs once a match is found
        return matched_dates

# Function to convert Unix time to human-readable format
def unix_to_datetime(unix_time):
    return datetime.utcfromtimestamp(unix_time)

# Function to convert HH:MM:SS format to Unix time
def convert_hhmmss_to_unix(date, time_str):
    date_time_str = f"{date} {time_str}"
    dt = datetime.strptime(date_time_str, '%m/%d/%Y %H:%M:%S')
    return int(dt.timestamp())

# Function to process CDF files and plot data
def process_cdf(file_url, start_time, end_time):
    try:
        response = requests.get(file_url)
        response.raise_for_status()

        # Save the CDF file content temporarily
        temp_file_path = 'temp.cdf'
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(response.content)

        with CDF(temp_file_path) as cdf:
            filtered_time = []
            filtered_data_diode_a = []
            filtered_data_diode_c = []

            for i in range(len(cdf['time_unix'])):
                current_time = cdf['time_unix'][i]
                if start_time <= current_time <= end_time:
                    if cdf['flag'][i] == 0:
                        filtered_time.append(current_time)
                        filtered_data_diode_a.append(cdf['data'][i, 0])
                        filtered_data_diode_c.append(cdf['data'][i, 2])

            filtered_time = np.array(filtered_time)
            filtered_data_diode_a = np.array(filtered_data_diode_a)
            filtered_data_diode_c = np.array(filtered_data_diode_c)

            # Compute area for Diode A
            area_trapz_a = np.trapz(filtered_data_diode_a, filtered_time)
            area_simps_a = simps(filtered_data_diode_a, filtered_time)

            # Compute area for Diode C
            area_trapz_c = np.trapz(filtered_data_diode_c, filtered_time)
            area_simps_c = simps(filtered_data_diode_c, filtered_time)
            
            # Fit a line between the first and last point in the filtered data
            x0, x1 = filtered_time[0], filtered_time[-1]
            y0, y1 = filtered_data_diode_a[0], filtered_data_diode_a[-1]
            slope_a = (y1 - y0) / (x1 - x0)
            intercept_a = y0 - slope_a * x0
            
            linear_fit_a = slope_a * filtered_time + intercept_a
            
            y0, y1 = filtered_data_diode_c[0], filtered_data_diode_c[-1]
            slope_c = (y1 - y0) / (x1 - x0)
            intercept_c = y0 - slope_c * x0
            
            linear_fit_c = slope_c * filtered_time + intercept_c
            
            # Calculate the area under the curve above the fitted line
            area_trapz_above_line_a = np.trapz(filtered_data_diode_a - linear_fit_a, filtered_time)
            area_simps_above_line_a = simps(filtered_data_diode_a - linear_fit_a, filtered_time)
            
            area_trapz_above_line_c = np.trapz(filtered_data_diode_c - linear_fit_c, filtered_time)
            area_simps_above_line_c = simps(filtered_data_diode_c - linear_fit_c, filtered_time)
    finally:
        # Ensure the temporary file is removed even if an error occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {
        'file': os.path.basename(file_url),
        'filtered_time': filtered_time,
        'filtered_data_diode_a': filtered_data_diode_a,
        'filtered_data_diode_c': filtered_data_diode_c,
        'area_trapz_a': area_trapz_a,
        'area_simps_a': area_simps_a,
        'area_trapz_c': area_trapz_c,
        'area_simps_c': area_simps_c,
        'area_trapz_above_line_a': area_trapz_above_line_a,
        'area_simps_above_line_a': area_simps_above_line_a,
        'area_trapz_above_line_c': area_trapz_above_line_c,
        'area_simps_above_line_c': area_simps_above_line_c
    }


# Function to generate URLs for given years and months
def generate_url_list(start_year, end_year):
    url_template = 'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/{year}/{month:02}/'
    urls = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 12): #yes, this is only for months 1 -11 because there is no data for 2023/12 yet
            urls.append(url_template.format(year=year, month=month))
    return urls

# Main code
file_path = 'flare catalog.txt'
start_year = 2023
end_year = 2023
url_list = generate_url_list(start_year, end_year)

cdf_urls = []
for url in url_list:
    try:
        cdf_files = get_cdf_files(url)
        cdf_urls.extend([(url, cdf_file) for cdf_file in cdf_files])
    except requests.RequestException as e:
        print(f"Failed to retrieve CDF files from {url}: {e}")

matched_dates = match_dates_with_cdf(file_path, cdf_urls)
#print(matched_dates)
output_file = 'energy_analysis_results.csv'
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Date','start_time','end_time', 'duration_of_flare','File', 'area_trapz_diaode_a', 'area_simps_diaode_a', 'area_trapz_diaode_c', 'area_simps_diaode_c','area_trapz_above_line_a','area_simps_above_line_a','area_trapz_above_line_c','area_simps_above_line_c'])

    for date, line, file_url in matched_dates:
        start_time_str = line.split()[1]
        end_time_str = line.split()[3]
        start_time_int= datetime.strptime(start_time_str,  '%H:%M:%S')
        end_time_int=datetime.strptime(end_time_str,  '%H:%M:%S')
        delta_t=end_time_int-start_time_int
        
        # Convert start and end times to Unix time
        start_time_unix = convert_hhmmss_to_unix(date, start_time_str) 
        end_time_unix = convert_hhmmss_to_unix(date, end_time_str) 
        
        print(f"Processing file for date: {date}, start time: {start_time_str}, end time: {end_time_str}")
        
        result = process_cdf(file_url, start_time_unix, end_time_unix)
        
        writer.writerow([
            date, 
            start_time_str,
            end_time_str,
            delta_t,
            result['file'], 
            result['area_trapz_a'], 
            result['area_simps_a'], 
            result['area_trapz_c'], 
            result['area_simps_c'],
            result['area_trapz_above_line_a'],
            result['area_simps_above_line_a'],
            result['area_trapz_above_line_c'],
            result['area_simps_above_line_c']
        ])
    '''    
        # Convert Unix time to human-readable format for plotting
        filtered_time_hr = [unix_to_datetime(t) for t in result['filtered_time']]

        # Plot irradiance vs time for Diode A
        plt.figure()
        plt.plot(filtered_time_hr, result['filtered_data_diode_a'], label='Diode A')
        plt.xlabel('Time (UTC)')
        plt.ylabel('Irradiance')
        plt.title(f'Irradiance vs Time for Diode A - {date}')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        
        # Plot irradiance vs time for Diode C
        plt.figure()
        plt.plot(filtered_time_hr, result['filtered_data_diode_c'], label='Diode C')
        plt.xlabel('Time (UTC)')
        plt.ylabel('Irradiance')
        plt.title(f'Irradiance vs Time for Diode C - {date}')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
'''
print(f"Results have been saved to {output_file}")
