#!/usr/bin/env python
# encoding: utf-8

import pandas as pd
import numpy as np
import math
import os.path
import calendar


DATA_FILE_DIR = "./data/"
DATAFILENAME = "all_data"
OUTPUTFILESSTORE = "./output_files/"


def import_csv_to_df(location, filename):
    """
    Imports a csv file into a Pandas dataframe
    :params: an xls file and a sheetname from that file
    :return: a df
    """
    
    return pd.read_csv(location + filename + '.csv')


def export_to_csv(df, location, filename, index_write):
    """
    Exports a df to a csv file
    :params: a df and a location in which to save it
    :return: nothing, saves a csv
    """

    return df.to_csv(location + filename + '.csv', index=index_write)


def what_years_in_data(df):

    '''
    Get list of the unique years in the df
    '''
    return df['year'].unique().tolist()


def breakdown_into_years(dataframe, unique_years):
    '''
    Breakdown the categorised transactions into years and then write those yearly transactions to spreadsheets
    :params: a dataframe containing categorised transactions
    :return: returns a list of the years that have been written to for later processing
    '''

    # Initialise dict for storage
    annual_dfs = {}

    # Go through the unique years, find the related transactions, add these to any existing
    # transactions, and save the results to XL
    for i in unique_years:
        temp_df = dataframe[dataframe['year'] == i]
        # Name for storing this dataframe into XL
        file_store_name = OUTPUTFILESSTORE + str(i) + '.csv'
        # Check whether a file already exists for the date, if it does, read it into a dataframe
        if os.path.exists(file_store_name) == True:
            # Read in existing data and then append it to temp_df
            existing_data_dataframe = import_csv_to_df(OUTPUTFILESSTORE, str(i))
            temp_df = temp_df.append(existing_data_dataframe)
        # It's possible to accidentally process the same set of transactions, so to prevent
        # duplication, remove any duplicates by finding those with identical 'description'
        # and 'balance'
        temp_df.drop_duplicates(subset = ['description','balance'], inplace=True)
        
        # Save as a dict of dfs
        annual_dfs[i] = temp_df

    return annual_dfs


def monthly_summaries(dataframe, unique_years):
    '''
    Takes the classified dataframe and separates it into years and then months to provide summaries of spend on each classification per month. Write summaries to .xslx files
    :params: A dataframe containing classified transactions, and a list of years that have been affected in the previous classification step (i.e. breakdown_into_years function)
    :return: Nowt
    '''

    # Initialise dict for storage
    monthly_dfs = {}

    # Drop NaNs from the classification column, because it's pointless trying to
    # summarise unclassified transactions
    # Drop the rows with 'ignore' classification (because they're meant to be ignored...)
    dataframe.dropna(subset = ['classification'], inplace = True)
    dataframe = dataframe[dataframe['classification'] != 'ignore']

    # Go through only the years that were updated in 'breakdown_into_years'
    # (pointless doing the others, cos they haven't changed)
    for year in unique_years:
        # Create new df based on only the current year, get a list
        # of the unique classifications from it, sort alphabetically
        # for prettiness reasons
        current_year_df = dataframe[dataframe['year'] == year]
        classifications_list = current_year_df['classification'].unique().tolist()
        classifications_list.sort()
        # Get unique months from dataframe, sort numerically so that
        # everything's in order
        unique_months = current_year_df['month'].unique().tolist()
        unique_months.sort()
        # Create empty summary df
        monthly_summary_df = pd.DataFrame(columns=classifications_list)
        # Add a month col to later on become the df index. Note that the second
        #number in 'range' is the number to generate up to, but not include.
        # That's why to get 1-12 you need to enter 1-13 rather than 1-12. Weird.
        monthly_summary_df['month'] = range(1,13)
        # Convert integers in 'month' to a named month
        monthly_summary_df['month name'] = monthly_summary_df['month'].apply(lambda x: calendar.month_name[x])
        # Set month no. as index
        monthly_summary_df.set_index('month', inplace = True)
        # Go through each month and calculate the transactions
        for month_count in unique_months:
            current_month_df = current_year_df[current_year_df['month'] == month_count]
            # Go through each transaction for the month in question
            for i in classifications_list:
                # Sum all money for each month and each classification
                # Income is the only classification that requires the 'money in' column to be summed
                if i == 'income':
                    monthly_summary_df[i].loc[[month_count]] = current_month_df.loc[current_month_df['classification']== i,'money in'].sum()
                else:
                    monthly_summary_df[i].loc[[month_count]] = current_month_df.loc[current_month_df['classification']== i,'money out'].sum()
        # Store the result to csv
        monthly_dfs[year] = monthly_summary_df

    return monthly_dfs


def save_out_dict_of_dfs(dict_dfs, added_text, subfolder):

    '''
    Save out a dictionary of dataframes to csvs
    '''

    for key in dict_dfs:
        export_to_csv(dict_dfs[key], OUTPUTFILESSTORE + subfolder + '/', str(key) + '_' + added_text, False)

    return


def create_monthly_breakdown_all_years(monthly_dfs):

    # Get list of years from the monthly breakdowns
    years = list(monthly_dfs.keys())
    # Make sure they're in order
    years.sort()
    
    temp_dict_dfs = {}
    
    for curr_year in years:    
        temp_df = monthly_dfs[curr_year]
        # Add a year column
        temp_df['year'] = curr_year
        # Create a new dict of dfs
        temp_dict_dfs[curr_year] = temp_df
    
    # Create the all years df by concatenating the dict of dfs
    all_years_by_month_df = pd.concat(temp_dict_dfs)

    export_to_csv(all_years_by_month_df, OUTPUTFILESSTORE + 'monthly_breakdowns' + '/', 'all_years_by_month', False)

    return all_years_by_month_df


def main():
    """
    Main function to run program
    """
    # I write back to the original dataframe and pandas warns about that, so turning off the warning    
    pd.options.mode.chained_assignment = None

    # Read in data
    df = import_csv_to_df(DATA_FILE_DIR, DATAFILENAME)
    
    # Get unique list of years in df
    unique_years = what_years_in_data(df)

    # Create spreadsheets of transactions by year
    annual_dfs = breakdown_into_years(df, unique_years)

    # Create monthly summaries and save them
    monthly_dfs = monthly_summaries(df, unique_years)
    
    # Save out dict of dfs to csvs
    save_out_dict_of_dfs(annual_dfs, 'annual_summary', 'annual_summaries')
    save_out_dict_of_dfs(monthly_dfs, 'monthly_breakdown', 'monthly_breakdowns')

    all_years_by_month_df = create_monthly_breakdown_all_years(monthly_dfs)

if __name__ == '__main__':
    main()
