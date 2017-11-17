1. You need a file structure with dirs for "data" (for input files) and "output" (summaries and charts).
1. I haven't tied the scripts together... so you need to run collect_and_classify.py, then analyse_budget.py and then plot_budget.py
1. You classify the transactions in transaction_types.csv
1. It reads .xlsx docs, because that's what my bank produces, but stores all intermediary and output files as csvs
1. It runs in a virtual environment, so there's a requirements file with all the libraries
1. You need to modify the find_bank_statements function in collect_and_classify.py so that it works with your bank's preferred way of producing Excel docs
1. There'll be thousands of other changes, I am sure, just let me know if you can't work anything out
1. Oh yeah... I think something screwy is going on with the re-write back to transaction_types.csv. It might break everything. But hey! This is what sharing code is all about, right? Free Bug fixes.
