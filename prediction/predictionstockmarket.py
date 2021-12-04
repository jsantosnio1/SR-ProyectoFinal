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
from keras.models import load_model
"""# Preprocessing

# Tesla Stock Market Analyis
"""
def trainPredictDataSet(df_route, prefijoEmpresa):
#def predictDataSet():

    import warnings
    warnings.filterwarnings('ignore')
    #df = pd.read_csv(df_route)
    
    df = pd.read_csv("C:\\Users\\Asus\\PycharmProjects\\SR-ProyectoFinal\\prediction\\tsla.us.txt")
    #df=df.rename(columns={"Close/Last":"Close"})
    df=df.replace({'\\$':''}, regex=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime("%Y-%m-%d")
    df= df.sort_values(by="Date", ascending=True)
    #df = pd.read_csv("C:/Users/JuanK/Documents/GitHub/SR-ProyectoFinal/prediction/mcft.us.txt")

    print(df.head())
    # Escalar los datos
    data = df.filter(['Close'])

    dataset = data.values
    # Obtenga el número de filas en las que entrenar el modelo
    training_data_len = int(np.ceil( len(dataset) * .85 ))

    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(dataset)
#### CREACIÓN Y ENTRENAMIENTO DEL MODELO
    # Crea el conjunto de datos de entrenamiento
    # Crea el conjunto de datos de entrenamiento escalado
    train_data = scaled_data[0:int(training_data_len), :]
    # Divida los datos en conjuntos de datos x_train e y_train
    x_train = []
    y_train = []

    for i in range(60, len(train_data)):
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
    model.add(LSTM(168, return_sequences=True, input_shape= (x_train.shape[1], 1)))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dense(65))
    model.add(Dense(1))

    # Compilar la modelo
    model.compile(optimizer='adam', loss='mean_squared_error')
    # Entrenar al modelo
    model.fit(x_train, y_train, batch_size=1, epochs=1)

    nombreModelo = 'prediction/models/prediction_model_'+prefijoEmpresa+'.h5'
    model.save(nombreModelo)
    # Visualiza los datos
    """ plt.figure(figsize=(16,6))
    plt.title('Model')
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close Price USD ($)', fontsize=18)
    plt.plot(data['Close'])
    plt.legend(['Train', 'Val', 'Predictions'], loc='lower right')
    plt.show() """

    return training_data_len
########## FIN CREACIÓN DEL MODELO

#########  LLAMADO DE MODELO ENTRENADO Y PREDICCIÓN
def predictDataSet(df_ruta, prefijoEmpresa):
    
    modelCompilate = load_model('prediction/models/prediction_model_'+prefijoEmpresa+'.h5')
    df = pd.read_csv("C:/Users/JuanK/Documents/GitHub/SR-ProyectoFinal/prediction/mcft.us.txt")
    #df = pd.read_csv(df_ruta)
    #df=df.rename(columns={"Close/Last":"Close"})
    df=df.replace({'\\$':''}, regex=True)
    print(df.head(60))
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime("%Y-%m-%d")
    #df= df.sort_values(by="Date", ascending=True)
    print('-'*600)
    # plt.figure(figsize=(16,6))
    # plt.title('Close Price History')
    # plt.plot(df['Close'])
    # plt.xlabel('Date', fontsize=18)
    # plt.ylabel('Close Price USD ($)', fontsize=18)
    # plt.show()
    print(df.head(60))

    #df1 = pd.read_csv("C:/Users/JuanK/Documents/GitHub/SR-ProyectoFinal/prediction/tsla.us.txt")
    data1 = df.filter(['Close'])
    dataset1 = data1.values    
    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(dataset1)
    # Obtenga el número de filas en las que entrenar el modelo
    training_data_len1 = int(np.ceil( len(dataset1)*.85  ))
    #scaled_data1 = scaler.fit_transform(dataset1)
    test_data = scaled_data[training_data_len1 - 60: , :]

    # Cree los conjuntos de datos x_test y y_test
    x_test = []
    for i in range(60, len(test_data)):
        x_test.append(test_data[i-60:i, 0])

    x_test = np.array(x_test)
    # Remodelar los datos
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1 ))
    # Obtenga los valores de precio predichos de los modelos
    predictions = modelCompilate.predict(x_test)
    predictions = scaler.inverse_transform(predictions)

    # Obtenga la raíz del error cuadrático medio (RMSE)
    # rmse = np.sqrt(np.mean(((predictions - y_test) ** 6)))
    # rmse
    train = data1[:training_data_len1]
    valid = data1[training_data_len1 :]
    valid['Predictions'] = predictions
    # Visualiza los datos
    plt.figure(figsize=(60,4))
    plt.title('Predicción')
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Close Price USD ($)', fontsize=14)
    plt.plot(train['Close'])
    plt.plot(valid['Predictions'])
    plt.legend(['Val', 'Predictions'], loc='lower right')
    aux= int(df.shape[0])
    aux_div=int(aux/10)
    plt.xticks(np.arange(0,aux, aux_div), df['Date'][0:aux-1:aux_div])
    plt.yticks(df['Close'][0:aux-1:aux_div])
    #plt.show()
    pathImage = 'static/graficas/prediction_model_graph_'+prefijoEmpresa+'.png'
    plt.savefig(pathImage)   
    # img = plt.imread(pathImage)
    # print(df.head(5))
    pathImage = pathImage.replace('static/', '')
    #valid
    return pathImage
