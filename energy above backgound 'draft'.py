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
    file_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.cdf')]
    return file_links

def match_dates_with_cdf(file_path, cdf_urls):
    with open(file_path, 'r') as file:
        lines = file.readlines()[16:]  # Skip the first 16 lines (index 0-15)
        matched_dates = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line[-4:].startswith('M'):
                date = stripped_line.split()[0]  # Extract the date part from the line
                day, month, year = date.split('/')
                date_formatted = f"{year}{month.zfill(2)}{day.zfill(2)}"  # Convert to CDF filename format
                print(f"Processing date: {date}")
                for cdf_url in cdf_urls:
                    if date_formatted in cdf_url:
                        matched_dates.append((date, cdf_url))
                        print(f"Match found - Date: {date}, CDF URL: {cdf_url}")
                        break  # No need to check other URLs once a match is found
        return matched_dates

# Example usage:
file_path = 'flare catalog.txt'
url_list = ['https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/01/', 'https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/02/','https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/03/','https://lasp.colorado.edu/maven/sdc/public/data/sci/euv/l2/2023/04/']

cdf_urls = []
for url in url_list:
    cdf_urls.extend(get_cdf_files(url))

print("CDF URLs:")
print(cdf_urls)

matched_dates = match_dates_with_cdf(file_path, cdf_urls)
for date, cdf_url in matched_dates:
    print(f"Date: {date}, CDF URL: {cdf_url}")



