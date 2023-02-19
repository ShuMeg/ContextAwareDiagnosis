'''
Submitted 22.04.2022
Author: Aniruddha Jahagirdar

This module trains LSTM module for accelerometer readings.
'''

import pandas as pd
import numpy as np
import keras
import tensorflow as tf
from keras.preprocessing.sequence import TimeseriesGenerator
from keras.models import Sequential
from keras.layers import LSTM, Dense
import plotly.graph_objs as go
import plotly

# Access csv file from dropbox
filename = "https://www.dropbox.com/s/7dxu94xytq5zdc0/Readings-main.csv?raw=1"
df = pd.read_csv(filename)
print(df.info())

# Select column with Time as header
df['Time'] = pd.to_datetime(df['Time'])
df.set_axis(df['Time'], inplace=True)
df.drop(columns=['Spin', 'Duration', 'Actual Duration', 'Water Hardness', 'Load Weight', 'Temperature', 'Humidity', 'Noise', 'Humidity', 'Temperature', 'Pressure'], inplace=True)

# Select column with Accelerometer as header
close_data = df['Accelerometer'].values
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
# Train the model
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
model.fit_generator(train_generator, epochs=num_epochs, verbose=1)

prediction = model.predict_generator(test_generator)

close_train = close_train.reshape((-1))
close_test = close_test.reshape((-1))
prediction = prediction.reshape((-1))

prediction = model.predict_generator(test_generator)

close_train = close_train.reshape((-1))
close_test = close_test.reshape((-1))
prediction = prediction.reshape((-1))

# Plot graph of results
trace1 = go.Scatter(
    x = date_train,
    y = close_train,
    mode = 'lines',
    name = 'Data'
)
trace2 = go.Scatter(
    x = date_test,
    y = prediction,
    mode = 'lines',
    name = 'Prediction'
)
trace3 = go.Scatter(
    x = date_test,
    y = close_test,
    mode='lines',
    name = 'Ground Truth'
)
layout = go.Layout(
    title = "Wash Maschine Data",
    xaxis = {'title' : "Date"},
    yaxis = {'title' : "Accelerometer"}
)
fig = go.Figure(data=[trace1, trace2, trace3], layout=layout)
fig.show()
#plotly.offline.plot(fig,filename='D:\GraphContextServer-master\static\css/Accelerometer.html',config={'displayModeBar': False})