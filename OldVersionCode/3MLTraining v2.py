
import os 
import pandas as pd
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
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
stock_model = {}
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
        models = [
            ('randomforest',RandomForestClassifier(max_depth=2, random_state=6)),
            ('logisticregression',LogisticRegression(random_state=6)),
        ]
        accuracy_model = {}
        for name, clf in models:
            clf_model = clf.fit(df_train_x, df_train_y)
            df_test_predict = clf_model.predict(df_test_x)
            df_test['predict'] = df_test_predict
            print(f'training {name} model for {filename} completed!')
            
            accuracy = round(accuracy_score(df_test_y, df_test_predict),4)*100
            #save model name, model, accuracy rate, predition result into dictionary
            res = {accuracy:[name,clf_model,df_test]}
            accuracy_model.update(res)
        # only save the model, predition result of the highest resluts to file
        max_acu = max(accuracy_model.keys())
        max_name = accuracy_model[max_acu][0]
        max_clf_model = accuracy_model[max_acu][1] 
        max_df_test = pd.DataFrame(accuracy_model[max_acu][2])
        stock_model.update({filename: [max_name, max_acu]})
        
        print(f'\n the highest accuracy algothms for {filename} is {max_name} with accuracy {max_acu} \n')
        model_name = os.path.join(f'{cwd}/Model1/',f'md_{filename}.joblib')
        dump(max_clf_model, model_name)
        #save prediction results
        max_df_test.to_csv(f'{cwd}/TPData1/tp_{filename}.csv')


        #* checking accuracy rate
        # print(f'classification reports \n')
        # print(confusion_matrix(df_test_y, df_test_predict))
        # print(f'Accuracy rate is {accuracy_score(df_test_y, df_test_predict)}')
        print(f'\n stock {filename} has been trained model \n')

    except Exception as ex:
        print(ex)
        
    print(f'\n Total {i} stocks processed. \n')
        
# save model table 
stock_model = pd.DataFrame(stock_model)
stock_model.T.to_csv(f'{cwd}/stock_model.csv')        




