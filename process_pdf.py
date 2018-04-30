# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 20:52:46 2018

@author: Ron Rammage

A program to harvest data from NCAA game attendance pdfs located at:
    http://www.ncaa.org/championships/statistics/ncaa-football-attendance

Parses tables contained in the pdfs by using a Regular Expression to match
the data format of the tables for individual teams.
Currently works for data between 2005-2016.

The program expects the pdfs to be stored in a directory named ./pdf_files
"""

import os
import re
import PyPDF2
import pandas as pd


FILEPATH = './pdf_files'
# Get a list of all the sheets in the input data set.
files = os.listdir(FILEPATH)

re_table_entry = re.compile(
    r'\d+\. [A-Z][a-zA-Z\s+.()\-\']+ \d+ \d+,\d+ \d+,\d+ (?!\d+,)')
lst_columns = ['Rank', 'University', 'Games', 'Attendance', 'Average', 'Year']

def parse_lines(lst_table_entries, str_year):
    ''' Split the records into fields, remove extra spaces.
    Clean the data by removing commas in numbers, re-joining University
    names that contain spaces. Return the data in a list of lists
    where each record is a list of field.
    '''
    lst_table = []
    for line in lst_table_entries:
        lst_line_parts = line.replace(
            ',', '').lstrip().rstrip().replace('.', '').split()
        if lst_line_parts:
            while not lst_line_parts[2][0].isdigit():
                lst_line_parts[1] = '{} {}'.format(
                    lst_line_parts[1], lst_line_parts[2])
                lst_line_parts = lst_line_parts[:2] + lst_line_parts[3:]
            lst_line_parts.append(str_year)
            lst_table.append(lst_line_parts)
    return lst_table

df_attendance = pd.DataFrame(columns=lst_columns)

for filename in files:
    pdfFileObj = open(os.path.join(FILEPATH, filename), 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    year = filename[:4]

    for page in range(pdfReader.numPages):
        pageObj = pdfReader.getPage(page)
        pageText = pageObj.extractText()

        pageText = pageText.replace('\n', '').replace('\r', '')
        # Scan through the raw text in the pdf to find patterns that look
        # like the attendance records.
        matches = re_table_entry.findall(pageText)
        table = parse_lines(matches, year)

        df_table = pd.DataFrame(table, columns=lst_columns)

        df_attendance = pd.concat([df_attendance, df_table], ignore_index=True)

# A few rows in the dataset are malformed when they are read by pdfReader.
# These rows show game attendance averages in excess of one-million.
# Filter out these rows.
df_attendance['Average'] = df_attendance['Average'].apply(pd.to_numeric)
df_attendance = df_attendance[df_attendance['Average'] < 1000000]

df_attendance = df_attendance[[
    'University', 'Games',
    'Attendance', 'Average', 'Year']]


df_attendance.to_csv('ncaa_attendance.csv')
