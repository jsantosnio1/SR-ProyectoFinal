# -*- coding: utf-8 -*-
# import numpy as np # linear algebra
# import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
# import os
# from subprocess import check_output
# import seaborn as sns
# import matplotlib.pyplot as plt
# import warnings
# from pandas.plotting import lag_plot
# from pandas import datetime

# from statsmodels.tsa.arima.model import ARIMA
# #from statsmodels.tsa.arima_model import ARIMA
# #from statsmodels.tsa.arima.model import ARIMA
# from sklearn.metrics import mean_squared_error
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')
plt.style.use("fivethirtyeight")

# For reading stock data from yahoo
from pandas_datareader.data import DataReader

# For time stamps
from datetime import datetime
from keras.models import Sequential
from keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
"""# Preprocessing

# Tesla Stock Market Analyis
"""
#def predictDataSet(df):
def predictDataSet():

    import warnings
    warnings.filterwarnings('ignore')

    df = pd.read_csv("C:/Users/JuanK/Documents/GitHub/SR-ProyectoFinal/prediction/tsla.us.txt")
    print(df.head())


    """## ARIMA (AutoRegressive Integrated Moving Average) for Time Series Prediction"""

    # train_data, test_data = df[0:int(len(df)*0.80)], df[int(len(df)*0.80):]
    # # plt.figure(figsize=(12,7))
    # # plt.title('Tesla Prices')
    # # plt.xlabel('Dates')
    # # plt.ylabel('Prices')
    # # plt.plot(df['Open'], 'blue', label='Training Data')
    # # plt.plot(test_data['Open'], 'purple', label='Testing Data')
    # # plt.xticks(np.arange(0,1857, 300), df['Date'][0:1857:300])
    # # plt.legend()

    # def smape_kun(y_true, y_pred):
    #     return np.mean((np.abs(y_pred - y_true) * 200/ (np.abs(y_pred) + np.abs(y_true))))

    # train_ar = train_data['Open'].values
    # test_ar = test_data['Open'].values

    # # https://machinelearningmastery.com/arima-for-time-series-forecasting-with-python/
    # history = [x for x in train_ar]
    # print(type(history))
    # predictions = list()
    # for t in range(len(test_ar)):
    #     model = ARIMA(history, order=(1,0,0))
    #     #model = ARIMA(history, order=(1,0,0))
    #     model_fit = model.fit(disp=0)
    #     output = model_fit.forecast()
    #     yhat = output[0]
    #     predictions.append(yhat)
    #     obs = test_ar[t]
    #     history.append(obs)
    #     #print('predicted=%f, expected=%f' % (yhat, obs))
    # error = mean_squared_error(test_ar, predictions)
    # print('Testing Mean Squared Error: %.3f' % error)
    # error2 = smape_kun(test_ar, predictions)
    # print('Symmetric mean absolute percentage error: %.3f' % error2)

    # plt.figure(figsize=(12,7))
    # plt.plot(test_data.index, predictions, color='purple', marker='o', linestyle='dashed', 
    #         label='Predicted Price')
    # plt.plot(test_data.index, test_data['Open'], color='blue', label='Actual Price')
    # plt.xticks(np.arange(1486,1856,60), df['Date'][1486:1856:60])
    # plt.title('Tesla Prices Prediction')
    # plt.xlabel('Dates')
    # plt.ylabel('Prices')
    # plt.legend()

    # Escalar los datos

    data = df.filter(['Close'])

    # Visualiza los datos
    plt.figure(figsize=(16,6))
    plt.title('Model')
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close Price USD ($)', fontsize=18)
    plt.plot(data['Close'])
    plt.legend(['Train', 'Val', 'Predictions'], loc='lower right')
    plt.xticks(np.arange(0,1857, 300), df['Date'][0:1857:300])
    plt.show()


    dataset = data.values
    # Obtenga el número de filas en las que entrenar el modelo
    training_data_len = int(np.ceil( len(dataset) * .75 ))

    training_data_len

    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(dataset)

    scaled_data

    # Crea el conjunto de datos de entrenamiento
    # Crea el conjunto de datos de entrenamiento escalado
    train_data = scaled_data[0:int(training_data_len), :]
    # Divida los datos en conjuntos de datos x_train e y_train
    x_train = []
    y_train = []

    for i in range(600, len(train_data)):
        x_train.append(train_data[i-60:i, 0])
        y_train.append(train_data[i, 0])
        if i<= 61:
            print(x_train)
            print(y_train)
            print()
        
    # Convierta el x_train y y_train en matrices numpy
    x_train, y_train = np.array(x_train), np.array(y_train)

    # Remodelar los datos
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))



    # Construye el modelo LSTM
    model = Sequential()
    model.add(LSTM(128, return_sequences=True, input_shape= (x_train.shape[1], 1)))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))

    # Compilar la modelo
    model.compile(optimizer='adam', loss='mean_squared_error')
    # Entrenar al modelo
    model.fit(x_train, y_train, batch_size=1, epochs=1)

    # Cree el conjunto de datos de prueba
    # Cree una nueva matriz que contenga valores escalados desde el índice 1543 hasta 2002
    # test_data = scaled_data[training_data_len - 60: , :]
    # # Cree los conjuntos de datos x_test y y_test
    # x_test = []
    # y_test = dataset[training_data_len:, :]
    # for i in range(60, len(test_data)):
    #     x_test.append(test_data[i-60:i, 0])





    test_data = scaled_data[training_data_len - 60: , :]
    # Cree los conjuntos de datos x_test y y_test
    x_test = []
    y_test = dataset[training_data_len:, :]
    for i in range(60, len(test_data)):
        x_test.append(test_data[i-60:i, 0])

        
    # Convierte los datos en una matriz numpy
    x_test = np.array(x_test)

    # Remodelar los datos
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1 ))


    # Obtenga los valores de precio predichos de los modelos
    predictions = model.predict(x_test)
    predictions = scaler.inverse_transform(predictions)

    # Obtenga la raíz del error cuadrático medio (RMSE)
    rmse = np.sqrt(np.mean(((predictions - y_test) ** 2)))
    rmse

    train = data[:training_data_len]
    valid = data[training_data_len:]
    valid['Predictions'] = predictions
    # Visualiza los datos
    plt.figure(figsize=(10,4))
    plt.title('Predicción')
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close Price USD ($)', fontsize=18)
    plt.plot(train['Close'])
    plt.plot(valid[['Predictions']])
    plt.legend(['Val', 'Predictions'], loc='lower right')
    plt.xticks(np.arange(0,1857, 300), df['Date'][0:1857:300])
    plt.show()

    #valid


    return plt
