
import os 
import pandas as pd
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier
from joblib import dump, load
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score


#* Getting stock list 
# getting currecnt working dirctory
cwd = os.getcwd()
path = cwd + '/LIData'

stocklist = []
for filename in os.listdir(path):
    if filename.endswith('.csv'):
        stocklist.append(filename[3:-4])
print(f'There are {len(stocklist)} stocks in S&P500 \n')

i = 0 
#* Load Data
for filename in stocklist:
    try: 
        cwd = os.getcwd()
        filepath = f'{cwd}/LIData/li_{filename}.csv'
        df = pd.read_csv(f'{filepath}',index_col='Date')
        # df.set_index(['Date'])
        print(f'{filename} stock training data loaded.')
        # print(df.head())

        #*Prapre Training Data
        # training period: 20110208~20180208
        df_train = df[df.index < '2018-02-08' ]
        i += 1
        #* check training data size 
        #! skip the stock whose training data is less than 500 rows 
        if len(df) < 500: 
            continue
        # resample the training data 
        sgn_1 = df_train[df_train['sgn'] == 1]
        sgn_0 = df_train[df_train['sgn'] == 0]
        len_1 = len(sgn_1)
        len_0 = len(sgn_0)
        print(f'Up record has {len_1} row, while the down records have {len_0} row \n')

        #resample
        df_majority = sgn_1
        df_minority = sgn_0

        # Upsample minority class
        df_minority_upsampled = resample(df_minority, 
                                        replace=True,     # sample with replacement
                                        n_samples= len_1,    # to match majority class
                                        random_state=42) # reproducible results
        # Combine majority class with upsampled minority class
        df_train = pd.concat([df_majority, df_minority_upsampled])
        
        # Display new class counts
        print('after resample, the records situation is: \n',df_train.sgn.value_counts())
        df_train_x = df_train.drop(['sgn'], axis=1)
        df_train_y = df_train['sgn']
        print(f'{len(df_train_x)} row training data is prepated.')

        #* Prapre Test Data 
        # testing period: 20180208~20190208
        df_test = df[(df.index > '2018-02-08') & (df.index < '2020-02-08')]
        df_test_x = df_test.drop(['sgn'], axis=1)
        df_test_y = df_test['sgn']
        print(f'{len(df_test_x)} row test data is prepared. \n')

        #* Train Model
        #? runing mutiple algorithm/paramter here, save the model with highest accuracy 
        model_name = os.path.join(f'{cwd}/Model/',f'md_{filename}.joblib')
        clf = RandomForestClassifier(max_depth=2, random_state=42)
        clf_model = clf.fit(df_train_x,df_train_y)
        dump(clf_model, model_name)
        df_test_predict =  clf_model.predict(df_test_x)
        #save prediction results
        df_test['predict'] = df_test_predict  
        df_test.to_csv(f'{cwd}/TPData/tp_{filename}.csv')


        #* checking accuracy rate
        print(f'classification reports \n')
        print(confusion_matrix(df_test_y, df_test_predict))
        print(f'Accuracy rate is {accuracy_score(df_test_y, df_test_predict)}')
        print(f'\n stock {filename} has been trained model \n')

    except Exception as ex:
        print(ex)
        
    print(f'Total {i} stocks processed.')
        
        




