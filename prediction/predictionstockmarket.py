# -*- coding: utf-8 -*-

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
from subprocess import check_output
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
from pandas.plotting import lag_plot
from pandas import datetime
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error

"""# Preprocessing

# Tesla Stock Market Analyis
"""
#def predictDataSet(df):
def predictDataSet():
    df = pd.read_csv("tsla.us.txt")
    df.head()

    """## ARIMA (AutoRegressive Integrated Moving Average) for Time Series Prediction"""

    train_data, test_data = df[0:int(len(df)*0.80)], df[int(len(df)*0.80):]
    # plt.figure(figsize=(12,7))
    # plt.title('Tesla Prices')
    # plt.xlabel('Dates')
    # plt.ylabel('Prices')
    # plt.plot(df['Open'], 'blue', label='Training Data')
    # plt.plot(test_data['Open'], 'purple', label='Testing Data')
    # plt.xticks(np.arange(0,1857, 300), df['Date'][0:1857:300])
    # plt.legend()

    def smape_kun(y_true, y_pred):
        return np.mean((np.abs(y_pred - y_true) * 200/ (np.abs(y_pred) + np.abs(y_true))))

    train_ar = train_data['Open'].values
    test_ar = test_data['Open'].values

    # https://machinelearningmastery.com/arima-for-time-series-forecasting-with-python/
    history = [x for x in train_ar]
    print(type(history))
    predictions = list()
    for t in range(len(test_ar)):
        model = ARIMA(history, order=(5,1,0))
        model_fit = model.fit(disp=0)
        output = model_fit.forecast()
        yhat = output[0]
        predictions.append(yhat)
        obs = test_ar[t]
        history.append(obs)
        #print('predicted=%f, expected=%f' % (yhat, obs))
    error = mean_squared_error(test_ar, predictions)
    print('Testing Mean Squared Error: %.3f' % error)
    error2 = smape_kun(test_ar, predictions)
    print('Symmetric mean absolute percentage error: %.3f' % error2)

    plt.figure(figsize=(12,7))
    plt.plot(test_data.index, predictions, color='purple', marker='o', linestyle='dashed', 
            label='Predicted Price')
    plt.plot(test_data.index, test_data['Open'], color='blue', label='Actual Price')
    plt.xticks(np.arange(1486,1856,60), df['Date'][1486:1856:60])
    plt.title('Tesla Prices Prediction')
    plt.xlabel('Dates')
    plt.ylabel('Prices')
    plt.legend()

    return plt
