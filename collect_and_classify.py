#!/usr/bin/env python
# encoding: utf-8

import pandas as pd
import numpy as np
import math
import os.path

from pandas import ExcelWriter
from lookup import trans_dict_lookup

HOME_DIR = "./"
DATA_FILE_DIR = "./data/"
UNPROCESSED_STATEMENTS = "./data/unprocessed_statements/"
ARCHIVED_STATEMENTS = "./data/archived_statements/"
TRANSACTIONTYPES = "transaction_types"
OUTPUTFILESSTORE = "./output_files/"


def import_xls_to_df(filename,want_header):
    """
    Imports an Excel file into a Pandas dataframe
    :params: get an xls file and a want_header string that's either None or 
    :return: a df
    """
    return pd.read_excel(filename,sheetname = 'Sheet1', header=want_header)


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


def find_bank_statements():

    '''
    Search for bank statements that haven't been processed, read them
    clean them and add them to a dataframe
    '''

    def clean_santanders_crap(dataframe):
        """
        Takes the df that is created from Santander's data and gets rid of the crap to change it into a nice uniform df
        :params: a santander dataframe
        :return: a clean dataframe
        """

        # Get account name
        account_no = dataframe[1][1][-6:-2]
        if account_no == '1983':
            account_name = 'joint'
        elif account_no == '5688':
            account_name = 'simons'
        elif account_no == '1586':
            account_name = 'dellas'
        else:
            account_name = 'unknown'
    
        # Get rid of cols and rows:
        # 1. Remove first four rows
        # 2. Remove all rows, then cols, that contain only NaNs
        dataframe.drop([0,1,2,3], inplace=True)
        dataframe.dropna(how='all', inplace=True)
        dataframe.dropna(how='all', axis=1, inplace=True)  # 'axis=1' means columns

        # Sometime the [8] col contains "GBP" and very occassionally, it doesn't
        # which means it doesn't exist, and that throws everything off
        # Hence remove the [8] col if it exists, and do nothing if it doesn't
        if len(dataframe.columns) == 6:
            dataframe.drop([8], axis=1, inplace=True)

        # Reset the index
        dataframe.reset_index(drop=True, inplace = True)

        # Rename the current columns
        dataframe.columns = ['date', 'description', 'money in', 'money out', 'balance']

        # Add new cols for account name, user classification of expenditure, vendor, short description and keyword
        dataframe["account name"] = account_name
        dataframe["short description"] = np.nan
        dataframe["vendor"] = np.nan
        dataframe["trans type"] = np.nan
        dataframe["classification"] = np.nan
        dataframe["keyword"] = np.nan

        # Add date column with year only, and one for month only
        dataframe['year'] = dataframe['date'].dt.year 
        dataframe['month'] = dataframe['date'].dt.month

        # Clean number cols by filling NaNs, then removing leading underscore from numbers
        # Do this by converting to string, removing first char, then removing commas
        # (which appear in things like 1,000), then converting back to float
        cols_to_clean = ['money in', 'money out', 'balance']
        for cleaning in cols_to_clean:
            dataframe[cleaning] = dataframe[cleaning].fillna('_0')
            dataframe[cleaning] = dataframe[cleaning].astype(str).str[1:].str.replace(',','').astype(np.float64)

        # Make description lowercase
        dataframe['description'] = dataframe['description'].str.lower()

        return dataframe
        

    # Start looking for unprocessed bank statements
    new = 'yes'
    for file in os.listdir(UNPROCESSED_STATEMENTS):
        if file.endswith('.xlsx'):
            #Need this if loop because the first iternation has to be a straight read rather than an append
            if new == 'yes':
                # Import data without headers
                dataframe = import_xls_to_df(UNPROCESSED_STATEMENTS + str(file), None)
                # Clean up the crappy organisation of Santander's data
                dataframe = clean_santanders_crap(dataframe)
                new = 'no'
            else:
                # Import data without headers
                temp_df = import_xls_to_df(UNPROCESSED_STATEMENTS + str(file), None)
                # Clean up the crappy organisation of Santander's data
                temp_df = clean_santanders_crap(temp_df)
                dataframe = dataframe.append(temp_df)
    # Re-index data frame because the appending multiple dataframes creates a new dataframe with multiple rows that share the same index numbe
    dataframe.reset_index(drop = True, inplace = True)
#           Turn this back on to move files once read
#            os.rename(DATA_FILE_DIR + str(file), ARCHIVED_STATEMENTS + str(file))

    return dataframe
    
    
def split_out_data(dataframe):
    """
    Takes a dataframe. Splits the 'description' col by commas and puts
    the bit before the first comma into the 'short description'. Then
    gets the vendor from the first part of the short description
    :params: a dataframe and a named column in that dataframe
    :return: a new dataframe
    """ 

    # Take everything in the description up to the first comma and use it to populate the short description column
    dataframe['short description'] = dataframe['description'].apply(lambda x: x.split(',')[0])

    # Get the vendor name by taking the bit in the short description before the 'at' or 'to'
    # (or taking everything if those words don't exist)
    dataframe['vendor'] = dataframe['short description'].str.split('(at |to ) *').str[-1]

    return dataframe


def create_trans_types(dataframe):
    '''
    Takes the first word of the 'short description' and uses it to
    create a transaction type. It does this by using a dict that
    translates the first word into a more general transaction type
    :params: a dataframe
    :return: a dataframe
    '''
    trans_dict = trans_dict_lookup
    
    
    # Takes the first word (i.e. the bit before the first space) and add it to the
    # 'trans type' col
    dataframe['trans type'] = dataframe['short description'].apply(lambda x: x.split(' ', 1)[0])

    # Go through the dict, and replace the first word in the 'trans type'
    # col with a more meaningful transaction type. The key of the dict
    # is the first words I've collected from all transaction to date
    # and the value is the more meaningful type
    for key in trans_dict:
            dataframe['trans type'] = dataframe['trans type'].replace(to_replace=key, value=trans_dict[key])

    return dataframe


def get_classifications(dataframe, search_col, class_col, keyword_col, trans_df, keyword, classification):
    '''
    Classify the payments in dataframe based on the infomation in the trans_dataframe
    :params: a dataframe in which there is a searchcol with payments to be classified and
    a classcol into which the classifications will be placed;
    a trans_dataframe which holds information about how payments have been classified in the
    past. In that df there is a user-generated keyword which can identify a payment, and an
    associated user-generated classification (groceries, house, cats, etc.)
    :return: a dataframe with classified payments
    '''

    # Read all the keywords in as a list, and then sort them by number of words
    # Why you ask? Well, there's a few instances like Tesco, and another, like
    # Tesco Bank. If I search on the longest phrases first, I'll pick up Tesco
    # Bank, and then (as long as I prevent overwriting) I'll pick up the plain
    # ol' Tesco at the second iteration
    keyword_list = trans_df[keyword].dropna().tolist()
    keyword_list.sort(key=lambda x: len(x.split(' ')), reverse=True)
    
    # Read in a dict of keywords and the classification they represent
    keyword_dict = dict(zip(trans_df[keyword], trans_df[classification]))

    # Go through the keywords, find matches in the search col and mark them up in the class_col
    for current_keyword in keyword_list:
        current_description = keyword_dict[current_keyword]
        # This is the clever bit. It's a Boolean mask based on a logical AND of
        # the keyword existing in the search col AND the class col not being populated already
        # (hence the short keywords like "Tesco" don't overwrite the long ones like "Tescos bank")
        # The regex bit simply tells the contains function that it's looking for a match, not a regex
        mask = dataframe[search_col].str.contains(current_keyword, regex=False) & dataframe[class_col].isnull()
        dataframe.loc[mask, class_col] = current_description
        dataframe.loc[mask, keyword_col] = current_keyword

    return dataframe


def update_trans_df(dataframe, class_col, trans_df):
    '''
    Takes the unclassified transactions and adds them back to transactions_types.xlsx
    Removes duplicate entries and then sorts so that the unclassified transactions,
    which need user classification, are placed at the top of the file.
    :params: a dataframe with transactions, a col to locate where the classifications
             are, and a transactions df in which to store the unclassified transactions
    :return: Nothing. Saves the trans df back to XL
    '''

    # Create a dataframe by taking all the rows without a keyword
    # from the super dataframe. Drop three columns that I don't need
    unclass_df = dataframe[dataframe[class_col].isnull()]
    unclass_df = unclass_df.drop(['balance','year', 'month'], axis=1)
    
    # Append the unclassified dataframe onto the trans one
    trans_df.dropna(subset = [class_col], inplace=True)
    trans_df = trans_df.append(unclass_df)

    # Take the resulting dataframe, remove duplicates of vendor,
    # remove all transactions relating to cash withdrawals (which don't
    # need classified). Then sort, so that all the NaNs are at the top
    trans_df.drop_duplicates('vendor', inplace=True)
    trans_df = trans_df[trans_df['trans type'] != 'cash']
    trans_df.sort_values(by='keyword', na_position='first', inplace=True)

    # Want a list of all the classifications used to make life simpler
    # Get the classifications, drop the blanks and duplicates, then sort
    # alphabetically
    classifications = trans_df['classification']
    classifications_df = pd.DataFrame(data=classifications.values, columns=['classification'])
    classifications_df.dropna(inplace=True)
    classifications_df.drop_duplicates(inplace=True)
    classifications_df.sort_values(by='classification', na_position='first', inplace=True)

    #Write result to csv
    export_to_csv(trans_df, HOME_DIR, 'transaction_types', False)
    export_to_csv(classifications_df, HOME_DIR, 'classifications', False)

    return


def main():
    """
    Main function to run program
    """
    # I write back to the original dataframe and pandas warns about that, so turning off the warning    
    pd.options.mode.chained_assignment = None

    # Read in statement data
    df = find_bank_statements()   
    
    # Import dataframe from transaction type xlsx, 0 reverts header to default action
    df_class = import_csv_to_df(HOME_DIR, TRANSACTIONTYPES)

    # Get vendor and short descriptions
    df = split_out_data(df)
    
    # Get transaction types
    df = create_trans_types(df)
    
    # Classify the transactions
    df = get_classifications(df, 'short description', 'classification', 'keyword', df_class, 'keyword', 'classification')

    # Save super dataframe with all info into 
    
    export_to_csv(df, DATA_FILE_DIR, 'all_data', False)

    # Update transaction dataframe
    update_trans_df(df, 'classification', df_class)    

if __name__ == '__main__':
    main()
