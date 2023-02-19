'''
Submitted 22.04.2022
Author: Aniruddha Jahagirdar

This module predicts future values for Humidity readings.
'''
import pandas as pd
import numpy as np
import keras
import tensorflow as tf
from keras.preprocessing.sequence import TimeseriesGenerator
from keras.models import Sequential
from keras.layers import LSTM, Dense
import plotly.graph_objs as go
import csv

def Humidity_predict():
    # Access csv file from dropbox
    filename = "https://www.dropbox.com/s/7dxu94xytq5zdc0/Readings-main.csv?raw=1"
    df = pd.read_csv(filename)
    # Select column with Time as header
    df['Time'] = pd.to_datetime(df['Time'])
    df.set_axis(df['Time'], inplace=True)
    # Select column with Humidity as header
    close_data = df['Humidity'].values
    close_data = close_data.reshape((-1,1))
    # Split data into 90:10 (90% train and 10% validate)
    split_percent = 0.90
    split = int(split_percent*len(close_data))

    close_train = close_data[:split]
    close_test = close_data[split:]

    date_train = df['Time'][:split]
    date_test = df['Time'][split:]
    # defines previous timesteps in order to predict the subsequent timestep
    look_back = 5

    train_generator = TimeseriesGenerator(close_train, close_train, length=look_back, batch_size=20)     
    test_generator = TimeseriesGenerator(close_test, close_test, length=look_back, batch_size=1)
    # LSTM for time-series analysis
    model = Sequential()
    model.add(
        LSTM(64,
            activation='relu',
            input_shape=(look_back,1))
    )
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    num_epochs = 25
    model.fit(train_generator, epochs=num_epochs, verbose=1)

    prediction = model.predict(test_generator)

    close_train = close_train.reshape((-1))
    close_test = close_test.reshape((-1))
    prediction = prediction.reshape((-1))

    close_data = close_data.reshape((-1))
    # Predict future values
    def predict(num_prediction, model):
        prediction_list = close_data[-look_back:]
        
        for _ in range(num_prediction):
            x = prediction_list[-look_back:]
            x = x.reshape((1, look_back, 1))
            out = model.predict(x)[0][0]
            prediction_list = np.append(prediction_list, out)
        prediction_list = prediction_list[look_back-1:]
            
        return prediction_list
    # Predict time values
    def predict_time(num_prediction):
        last_time = df['Time'].values[-1]
        prediction_time = pd.date_range(last_time, periods=num_prediction+1).tolist()
        return prediction_time
    # Number of future values to be predicted
    num_prediction =10
    forecast = predict(num_prediction, model)
    forecast_time = predict_time(num_prediction)
    # Write generated values in csv file
    program_results = list()
    for i in forecast:
        program_results.append(i)
    header = ['Hum_Value']
    outfile = open(r"C:\Users\meghn\Dropbox/Hum_prediction.csv",'w', newline="")
    out = csv.writer(outfile)
    out.writerow(header)
    out.writerows(map(lambda x: [x], program_results))
    outfile.close()
    # Plot graph of results
    trace1 = go.Scatter(
        x = date_train,
        y = close_train,
        mode = 'lines',
        name = 'Data'
    )
    trace2 = go.Scatter(
        x = forecast_time,
        y = forecast,
        mode = 'lines',
        name = 'Prediction'
    )

    layout = go.Layout(
        title = "Humidity Prediction",
        xaxis = {'title' : "Date"},
        yaxis = {'title' : "Humidity"}
    )
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    #fig.write_image("D:\GraphContextServer-master\static\css/Humidity.png", engine="kaleido")   
    fig.write_html("E:\Meg_Thesis\Thesis__\Ani\IAS_Context-master\IAS_Context-master\static\css/Humidity.html")