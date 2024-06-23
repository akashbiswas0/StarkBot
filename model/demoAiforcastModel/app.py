import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load the model
model = load_model('/home/priyanshu/hackaton/starknet/ml/01/demoAiforcastModel/model/lstm_model.h5')

# Load the scaler
with open('/home/priyanshu/hackaton/starknet/ml/01/demoAiforcastModel/model/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Function to create sequences
def create_sequences(data, seq_length):
    xs = []
    for i in range(len(data) - seq_length):
        x = data[i:i+seq_length]
        xs.append(x)
    return np.array(xs)

# Function to predict the next value
def predict_next_value(model, data, scaler, seq_length):
    last_sequence = data[-seq_length:]
    last_sequence = np.expand_dims(last_sequence, axis=0)
    prediction = model.predict(last_sequence)
    prediction = scaler.inverse_transform(prediction)
    return prediction[0]

# Streamlit app
st.title('Demo trade prediction')

# File upload
uploaded_file = st.file_uploader("Upload your time series CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    st.write("Uploaded Data")
    st.write(df.head())
    
    # Convert Timestamp column to datetime type if exists
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp')
    else:
        st.error("Timestamp column not found in the CSV. Please ensure your CSV has a 'Timestamp' column.")
        st.stop()

    # Save timestamp before normalization
    timestamps = df['Timestamp']

    # Prepare data for normalization (exclude Timestamp)
    data_for_scaling = df.drop('Timestamp', axis=1)

    # Normalize the data
    scaled_data = scaler.transform(data_for_scaling)

    # Define sequence length
    SEQ_LENGTH = 3

    # Make predictions
    X_new = create_sequences(scaled_data, SEQ_LENGTH)
    predictions = []
    for i in range(len(X_new)):
        pred = model.predict(np.expand_dims(X_new[i], axis=0))
        pred = scaler.inverse_transform(pred)
        predictions.append(pred[0])
    
    predictions = np.array(predictions)

    # Plot the results
    st.subheader('Predictions')
    st.write("Predicted Values:")
    st.write(pd.DataFrame(predictions, columns=['Open', 'High', 'Low', 'Close', 'Volume']))

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(timestamps[SEQ_LENGTH:], data_for_scaling['Open'][SEQ_LENGTH:], color='blue', label='Actual Open Price')
    ax.plot(timestamps[SEQ_LENGTH:], predictions[:, 0], color='red', label='Predicted Open Price')
    ax.set_title('Open Price Prediction')
    ax.set_xlabel('Time')
    ax.set_ylabel('Price')
    ax.legend()

    # Format x-axis to show dates nicely
    plt.gcf().autofmt_xdate()
    date_formatter = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_formatter)

    st.pyplot(fig)

    # Predict the next value
    next_value = predict_next_value(model, scaled_data, scaler, SEQ_LENGTH)
    st.subheader('Next Predicted Values')
    st.write("Next predicted values (Open, High, Low, Close, Volume):", next_value)

    # Predict the next timestamp
    last_timestamp = timestamps.iloc[-1]
    next_timestamp = last_timestamp + pd.Timedelta(days=1)
    st.write("Predicted for timestamp:", next_timestamp)