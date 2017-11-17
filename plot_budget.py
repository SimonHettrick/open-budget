#!/usr/bin/env python
# encoding: utf-8

import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt


DATA_FILE_DIR = "./data/"
DATAFILENAME = "all_data"
BYMONTHDATA = "all_years_by_month"
MONTHLIESFILESSTORE = "./output_files/monthly_breakdowns/"
MONTHLIESPLOTSTORE = "./output_files/monthly_plots/"
ANNUALSPLOTSTORE = "./output_files/annual_plots/"

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


def calculate_daily_spend(all_data_df):
    
    '''
    The idea here is to find which days of the month we spend money
    If we know there are peaks at the start and, say, on day 20, then
    if we look at our bank balance on day 25, we know that there's not typically
    going to be any big spend after that time, so the month in the bank is the
    money we have.
    
    I need to just look at the previous year's worth of data really, because if I average
    over all years, inflation will skew the figures down
    '''

    # Convert the date to a date type, then create a new col with the number
    # of the month in it
    all_data_df['date'] = all_data_df['date'].astype('datetime64[ns]')
    all_data_df['day'] = all_data_df['date'].dt.day

    # Use this as a storage df
    daily_spend_df = pd.DataFrame(index=range(1,32))

    for day in range(1,32):
        temp_df = all_data_df[all_data_df['day']==day]
        average_daily = temp_df['money out'].mean()
        print(day)
        print(average_daily)
    return


def get_monthly_summaries(unique_years):

    # Initialise dict of dfs
    monthly_dfs = {}

    for year in unique_years:
        # Get monthly summary
        monthly_summary_df = import_csv_to_df(MONTHLIESFILESSTORE, str(year) + '_monthly_breakdown')
        # Use the named months for the index so they appear in the plot
        monthly_summary_df.set_index('month name', inplace = True)
        # Save into dict of dfs
        monthly_dfs[year] = monthly_summary_df

    return monthly_dfs


def create_incomings(monthly_dfs):

    income_dfs = {}

    for key in monthly_dfs:
        income_dfs[key] = monthly_dfs[key][['income']]

    return income_dfs


def create_detailed_outgoings(monthly_dfs):

    '''
    Create the detailed outgoing dfs by taking the monthly dfs and dropping the income
    from them, then re-arranging into size order to make later plotting pretty and pretty
    easy
    '''

    # Initialise
    outgoings_detail_dfs = {}
    
    for key in monthly_dfs:
        current_df = monthly_dfs[key]
        # Don't want income in this df
        current_df.drop('income', axis = 1, inplace = True)
        # Re-order the cols by placing the greatest summed columns first
        current_df = current_df.ix[:, current_df.sum().sort_values(ascending=False).index]
        # Save as a dict of dfs
        outgoings_detail_dfs[key] = current_df

    return outgoings_detail_dfs


def create_summary_outgoings(outgoings_detail_dfs):

    '''
    There are too many cols to make sense when the outgoings are graphed, so I'm going to get the biggest
    10 of them, then combine the remaining ones into an "other" column.
    '''

    # Initialise
    outcome_summary_dfs = {}
    
    for key in outgoings_detail_dfs:
        current_df = outgoings_detail_dfs[key]
        # Get the names of the cols
        orig_cols = list(current_df.columns)
        # The cols are in order of size, so it's easy to get the ten biggest: just
        # take the first ten cols... but first create an "other" col from the
        # sum of the 11th to end col
        current_df['other'] = current_df[orig_cols[11:]].sum(axis=1)
        # We want to keep the first ten columns AND the "other" column
        keep_columns = orig_cols[:10]
        keep_columns.append('other')
        outcome_summary_dfs[key] = current_df[keep_columns]

    return outcome_summary_dfs


def plot_summary_plots(income_dfs, outgoings_detail_dfs, outgoings_summary_dfs):
    
    # Since all of the three dict of dfs share the same keys, we can loop
    # through them all quite easily using the keys from any one of them

    for key in outgoings_summary_dfs:

        # First plot the totals
        # Plot the outgoings as a stacked bar chart
        ax = outgoings_summary_dfs[key].plot(kind='bar', stacked=True)

        # Now use the same axis to plot the incomings as a line
        income_dfs[key].plot(kind='line', color='r', ax=ax)
        
        # Now for some formatting
        # Get the labels round the right way
        ax.set_xticklabels(labels=outgoings_summary_dfs[key].index, rotation=90)
        # Set up legend
        ax.legend(bbox_to_anchor=(1.35, 0),    # Place the legend outside the plot
                   loc='lower right',          # This sets the zero point coordinate against which the bbox bit                                above relates 
                   prop={'size': 8})           # Make legend font small
        # Titles and axis labels
        plt.title('Budget ' + str(key))
        plt.ylabel('Expenditure (£)')
        plt.xlabel('')

        # Save the plot
        plt.savefig(MONTHLIESPLOTSTORE + str(key) + '_monthly_summary.png', format = 'png', dpi = 150, bbox_inches='tight')

        # Start the second plot which shows the detail of the "other" col
        ax2 = outgoings_detail_dfs[key].plot(kind='bar', stacked=True)
        
        # Get the labels round the right way
        ax2.set_xticklabels(labels=outgoings_detail_dfs[key].index, rotation=90)
        # Set up legend
        plt.legend(bbox_to_anchor=(1.35, 0),    # Place the legend outside the plot
                   loc='lower right',           # This sets the zero point coordinate against which the bbox bit                                above relates 
                   prop={'size': 8})            # Make legend font small
        # Titles and axis labels
        plt.title('Full detail of budget ' + str(key))
        plt.ylabel('Expenditure (£)')
        plt.xlabel('')

        # Save the plot
        plt.savefig(MONTHLIESPLOTSTORE + str(key) + '_monthly_detailed.png', format = 'png', dpi = 150, bbox_inches='tight')
#        plt.show()

    return   


def how_costs_change_over_years(all_years_by_month_df, unique_years):

    '''
    Plot the average monthly spend on each of the classifications over each year in the data, and the total spend
    over each year, to see how things have changed over time
    '''

    annual_summaries_dfs = {}

    # Not going to need the month col, and keeping it
    # just causes complication, so let's get rid early
    all_years_by_month_df.drop('month name', axis=1, inplace=True)

    # Need the classifications to create a storage df
    classifications = list(all_years_by_month_df.columns)
    classifications.sort()
    
    # Obviously don't want the year in the storage df as a col name
    classifications.remove('year')
    
    # The storage_df has the years in the data as the index, and the classifications
    # as the col names
    average_spend_df = pd.DataFrame(columns=classifications, index=unique_years)
    total_spend_df = pd.DataFrame(columns=classifications, index=unique_years)
    
    # Now to calculate the average spend per year
    for curr_year in unique_years:
        # Cut df down to specific year
        temp_df = all_years_by_month_df[all_years_by_month_df['year']==curr_year]
        # Go through each classification and store the average monthly
        # spend and the total annual spend in the storage dfs
        for curr_classification in classifications:
            average_spend_df.loc[curr_year,curr_classification] = temp_df[curr_classification].mean()
            total_spend_df.loc[curr_year,curr_classification] = temp_df[curr_classification].sum()

    annual_summaries_dfs['average'] = average_spend_df
    annual_summaries_dfs['total'] = total_spend_df
    return annual_summaries_dfs


def plot_how_costs_change_over_years(average_spend_by_year_df, unique_years):
    
    '''
    Create plots that show how each classification of spending has changed over the years
    '''
    
    # Get list of available classifications
    classifications = list(average_spend_by_year_df.columns)

    # Sort the index so that the years appear in order
    average_spend_by_year_df.sort_index(inplace=True)    

    for curr_classification in classifications:
        # Set a reasonable max y limit as being 10% greater than the max value
        # in the col
        y_limit_max = average_spend_by_year_df[curr_classification].max() * 1.1
        #Plot
        average_spend_by_year_df[curr_classification].plot(kind='line', color='r', xticks=unique_years, ylim=[0,y_limit_max])
        # There's income in there as well as costs, so this is needed
        # to make the plot titles make sense for both eventualities
        if curr_classification == 'income':
            title = 'Average monthly income'
        else:
            title = 'Average monthly spend on ' + curr_classification
        plt.title(title)
        plt.ylabel('Average monthly spend (£)')
        plt.xlabel('')
        plt.savefig(ANNUALSPLOTSTORE + 'annual_spend_' + curr_classification + '.png', format = 'png', dpi = 150, bbox_inches='tight')
        # Clear the frame or everything goes really screwy when the
        # next plot is made
        plt.clf()
#        plt.show()
    return


def calculate_income_and_outgoings(total_spend_by_year_df):

    # Get list of available classifications
    outgoings_cols = list(total_spend_by_year_df.columns)
    outgoings_cols.remove('income')

    total_spend_by_year_df['outgoings'] = total_spend_by_year_df[outgoings_cols].sum(axis=1)

    return total_spend_by_year_df


def plot_income_and_outgoings(income_outgoings_df, unique_years):

    # Sort the index so that the years appear in order
    income_outgoings_df.sort_index(inplace=True)    

    ax = income_outgoings_df['income'].plot(kind='line', color='b', xticks=unique_years)
    income_outgoings_df['outgoings'].plot(kind='line', color='r', ax=ax)

    plt.legend()

    plt.title('Income vs. outgoings')
    plt.ylabel('£s')
    plt.xlabel('')
    plt.savefig(ANNUALSPLOTSTORE + 'total_income_outgoings.png', format = 'png', dpi = 150, bbox_inches='tight')

    return

def main():
    """
    Main function to run program
    """

    # I write back to the original dataframe and pandas warns about that, so turning off the warning    
    pd.options.mode.chained_assignment = None

    # Read in all data
    all_data_df = import_csv_to_df(DATA_FILE_DIR, DATAFILENAME)

    # Create list of the years in the data
    unique_years = what_years_in_data(all_data_df)

    # Calculate daily spend
    calculate_daily_spend(all_data_df)



    # Get the monthly summary data...
    monthly_dfs = get_monthly_summaries(unique_years)
    # ...and use it to create dicts of dfs for each of income, detailed outgoings and summary outgoings
    income_dfs = create_incomings(monthly_dfs)
    outgoings_detail_dfs = create_detailed_outgoings(monthly_dfs)
    outgoings_summary_dfs = create_summary_outgoings(outgoings_detail_dfs)

    # Plot monthly summaries
#    plot_summary_plots(income_dfs, outgoings_detail_dfs, outgoings_summary_dfs)

    # Break down all costs into average cost per classification per year
    all_years_by_month_df = import_csv_to_df(MONTHLIESFILESSTORE, BYMONTHDATA)

    # Calculate average and total costs per classification per year
    annual_summaries_dfs = how_costs_change_over_years(all_years_by_month_df, unique_years)

    # Quickly sum the outgoings into a single col
    income_outgoings_df = calculate_income_and_outgoings(annual_summaries_dfs['total'])

    # Plot average cost per classification per year
#    plot_how_costs_change_over_years(annual_summaries_dfs['average'], unique_years)

    # Plot total income and outgoings per year
#    plot_income_and_outgoings(income_outgoings_df, unique_years)

if __name__ == '__main__':
    main()