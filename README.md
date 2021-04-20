# CS668-2021

This is Bowen Duan's CS668 Project Repo

## Data
1. *OData* Folder stores the orignial price data from yahoo finance
2. *LIData* Folder stores the labeled orginal data labled and added indicators columns
3. *TPData1* Folder stores the LIData plus column named "sgns", containing price miving direction information
4. *BTData1* Folder stores the TPData, but only coutains data from Feb,08, 2020 to Feb, 08,2021 for back testing
5. *Model1* stores the models trained for 494 stocks
6. *OldVersionData* stores all old verion data for later use
7. *OldVersionCode* stores all iteration of codes
8. *Demo_SGLStock* stores all the data and notesbook, containing all the data and code for AAPL singel stock back testing

## Python File
1. Python Script *1DataDownload.py* is used to downlaod the s&p500 2. 10-year price data from yahoo finance. 
2. Python Script *2ML_Label.py* contains is used to label the data. 
3. Python Script *3MLTraining.py* contains codes to training predition model
4. Python Scripy *4Demo_backtesting.py* only tests AAPL sotck 
5. Python Scripy *5PDT.py* is used to predict price moving direction from Feb,2020 to Feb,2021, by applying the model trained  in *3MLTraining.py* 
6. Python Scripy *6SGL_Backtest.py* backtests AAPL sotck
7. Python Scripy *7MTP_Backtest.py* backtests all 494 stocks

## Results
1. *results_log.txt* have all the trading/buying/selling inoformation
2. *Results Analysis.xlsx* is used to analyze trading records
3. *stock_modelv2.csv* is uesd to analyze algorithm performances


