# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 19:23:11 2024

@author: joahb
"""
'''
this file includes full day plots just to see how the days are looking before and after
flares take place
'''
import requests
from bs4 import BeautifulSoup
import os
import numpy as np
from scipy.integrate import simps
from spacepy.pycdf import CDF
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import pytz
import time

# Function to get CDF files from a URL with retry logic
def get_cdf_files(url, retries=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            cdf_files = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.cdf')]
            return cdf_files
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Handle rate limiting by waiting before retrying
                retry_after = int(response.headers.get("Retry-After", 5))  # Default to 5 seconds if header is missing
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                print(f"HTTP error occurred: {e}")
                break
        except requests.RequestException as e:
            print(f"Request exception occurred: {e}")
            break
        attempt += 1
        # Exponential backoff
        time.sleep(2 ** attempt)
    return []
'''
# Function to get CDF files from a URL
def get_cdf_files(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    cdf_files = [a['href'] for a in soup.find_all('a') if a['href'].endswith('.cdf')]
    return cdf_files
'''
# Function to match dates in the flare catalog with CDF files
def match_dates_with_cdf(file_path, cdf_urls):
    with open(file_path, 'r') as file:
        lines = file.readlines()[12:]  # Skip the first couple of lines
        matched_dates = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line[-4:].startswith(('M','X')):
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
    return datetime.fromtimestamp(unix_time)
# Function to convert HH:MM:SS format to Unix time
def convert_hhmmss_to_unix(date, time_str):
    """
    Convert date and time (in HH:MM:SS format) to Unix timestamp.
    Assumes the input date and time are in UTC.
    """
    date_time_str = f"{date} {time_str}"
    dt = datetime.strptime(date_time_str, '%m/%d/%Y %H:%M:%S')
    return int(dt.timestamp())

# Function to process CDF files and plot data
def process_cdf(file_url, start_time, end_time, day_start_time, day_end_time):
    temp_file_path = 'temp.cdf'
    try:
        response = requests.get(file_url)
        response.raise_for_status()

        # Save the CDF file content temporarily
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(response.content)

        with CDF(temp_file_path) as cdf:
            filtered_time = []
            filtered_data_diode_a = []
            filtered_data_diode_c = []
            full_day_time = []
            full_day_data_diode_a = []
            full_day_data_diode_c = []

            for i in range(len(cdf['time_unix'])):
                current_time = cdf['time_unix'][i]
                if day_start_time <= current_time <= day_end_time:
                    full_day_time.append(current_time)
                    full_day_data_diode_a.append(cdf['data'][i, 0])
                    full_day_data_diode_c.append(cdf['data'][i, 2])

                if start_time <= current_time <= end_time and cdf['flag'][i] == 0:
                    filtered_time.append(current_time)
                    filtered_data_diode_a.append(cdf['data'][i, 0])
                    filtered_data_diode_c.append(cdf['data'][i, 2])

            # Convert lists to numpy arrays
            filtered_time = np.array(filtered_time)
            filtered_data_diode_a = np.array(filtered_data_diode_a)
            filtered_data_diode_c = np.array(filtered_data_diode_c)
            full_day_time = np.array(full_day_time)
            full_day_data_diode_a = np.array(full_day_data_diode_a)
            full_day_data_diode_c = np.array(full_day_data_diode_c)
            '''
            # Debug prints
            print(f"Filtered time: {filtered_time}")
            print(f"Filtered data (Diode A): {filtered_data_diode_a}")
            print(f"Filtered data (Diode C): {filtered_data_diode_c}")
            print(f"Full day time: {full_day_time}")
            print(f"Full day data (Diode A): {full_day_data_diode_a}")
            print(f"Full day data (Diode C): {full_day_data_diode_c}")
            '''
            # Check if the filtered arrays are empty
            if filtered_time.size == 0 or filtered_data_diode_a.size == 0 or filtered_data_diode_c.size == 0:
                print(f"No data found in the specified time range for {file_url}")
                return {
                    'file': os.path.basename(file_url),
                    'filtered_time': [],
                    'filtered_data_diode_a': [],
                    'filtered_data_diode_c': [],
                    'full_day_time': full_day_time,
                    'full_day_data_diode_a': full_day_data_diode_a,
                    'full_day_data_diode_c': full_day_data_diode_c
                }

    finally:
        # Ensure the temporary file is removed even if an error occurs
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {
        'file': os.path.basename(file_url),
        'filtered_time': filtered_time,
        'filtered_data_diode_a': filtered_data_diode_a,
        'filtered_data_diode_c': filtered_data_diode_c,
        'full_day_time': full_day_time,
        'full_day_data_diode_a': full_day_data_diode_a,
        'full_day_data_diode_c': full_day_data_diode_c
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

for date, line, file_url in matched_dates:
    start_time_str = line.split()[1]
    end_time_str = line.split()[3]

    start_time_unix = convert_hhmmss_to_unix(date, start_time_str)
    end_time_unix = convert_hhmmss_to_unix(date, end_time_str)

    # Get the Unix timestamps for the start and end of the day
    day_start_time_unix = convert_hhmmss_to_unix(date, '00:00:00')
    day_end_time_unix = convert_hhmmss_to_unix(date, '23:59:59')

    print(f"Processing file for date: {date}, start time: {start_time_str}, end time: {end_time_str}")

    result = process_cdf(file_url, start_time_unix, end_time_unix, day_start_time_unix, day_end_time_unix)

    # Convert Unix time to human-readable format for plotting
    filtered_time_hr = [unix_to_datetime(t) for t in result['filtered_time']]
    full_day_time_hr = [unix_to_datetime(t) for t in result['full_day_time']]

    # Plot irradiance vs time for Diode A (Flare Period)
    plt.figure()
    plt.plot(filtered_time_hr, result['filtered_data_diode_a'], label='Diode A (Flare Period)')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Irradiance')
    plt.title(f'Irradiance vs Time for Diode A (Flare) - {date}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Plot irradiance vs time for Diode C (Flare Period)
    plt.figure()
    plt.plot(filtered_time_hr, result['filtered_data_diode_c'], label='Diode C (Flare Period)')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Irradiance')
    plt.title(f'Irradiance vs Time for Diode C (Flare) - {date}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Plot irradiance vs time for Diode A (Full Day)
    plt.figure()
    plt.plot(full_day_time_hr, result['full_day_data_diode_a'], label='Diode A (Full Day)')
    plt.axvline(x=unix_to_datetime(start_time_unix), color='r', linestyle='--', label='Flare Start')
    plt.axvline(x=unix_to_datetime(end_time_unix), color='g', linestyle='--', label='Flare End')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Irradiance')
    plt.title(f'Irradiance vs Time for Diode A (Full Day) - {date}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Plot irradiance vs time for Diode C (Full Day)
    plt.figure()
    plt.plot(full_day_time_hr, result['full_day_data_diode_c'], label='Diode C (Full Day)')
    plt.axvline(x=unix_to_datetime(start_time_unix), color='r', linestyle='--', label='Flare Start')
    plt.axvline(x=unix_to_datetime(end_time_unix), color='g', linestyle='--', label='Flare End')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Irradiance')
    plt.title(f'Irradiance vs Time for Diode C (Full Day) - {date}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()