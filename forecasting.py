import zipfile

import pandas as pd
import os
import matplotlib.pyplot as plt
from sktime.forecasting.base import ForecastingHorizon
from sklearn.linear_model import LinearRegression
from sktime.forecasting.compose import make_reduction
from pmdarima import auto_arima
from sklearn.metrics import mean_squared_error
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import io
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy import text


UPLOAD_FOLDER = 'uploads'
PLOT_FOLDER = 'static/plots'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app = Flask(__name__)
app.secret_key = 'secretkey123'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER

# Ensure upload and plot folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)


class DatabaseConfig:
    def __init__(self, username: str, password: str, host: str, database: str):
        self.username = "root"
        self.password = "Avatar751"
        self.host = "localhost"
        self.database = "mydatabase"

    def get_connection_string(self) -> str:
        return f"mysql+mysqlconnector://{self.username}:{self.password}@{self.host}/{self.database}"


# Helper function what is controlling the file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Finding error measurement.
def find_mse(data, predicted_data):
    """MSE (Ortalama Kare Hata) hesaplar."""
    return mean_squared_error(data, predicted_data)


def dframe_returner(number_of_input_folders):
    if number_of_input_folders < 1:
        raise ValueError("Number of input folders must be at least 1.")
    else:
        base_path = os.getcwd()
        folder_path = os.path.join(base_path, "uploads")
        dataframes = []
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                file_path = os.path.join(folder_path, file_name)
                df = pd.read_excel(file_path)
                if not df.empty:
                    for column in df.columns.tolist():
                        if df[column].isna().any():
                            df[column] = dataframe_completer(df, column)
                    dataframes.append(df)
        return pd.concat(dataframes, ignore_index=True)


def complete_missing_data(df):
    """DataFrame'deki eksik verileri tamamlar."""
    for column in df.columns:
        if df[column].dtype.kind in 'fiuO':  # sayısal veya kategorik sütunlar için
            if df[column].isna().any():
                df[column] = dataframe_completer(df, column)
    return df


def dataframe_completer(df, name_of_the_column_with_NaN):
    """Sütundaki eksik verileri interpolasyon ile doldurur."""
    index_list = df.index.tolist()
    length_of_dataframe = len(index_list)

    if length_of_dataframe == 12:
        return df[name_of_the_column_with_NaN].interpolate(method='linear')
    elif length_of_dataframe == 24:
        return df[name_of_the_column_with_NaN].interpolate(method='quadratic')
    else:
        return df[name_of_the_column_with_NaN].interpolate(method='polynomial', order=3)


def future_forcasting(n, db_config: DatabaseConfig):
    # Load data from multiple Excel files.
    data = dframe_returner(n)  # User will change it.

    # Prepare the data
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%B')
    data = data.set_index('Date').sort_index()

    # Resample to monthly data
    time_series = data[['Sales']].resample('ME').sum()
    time_series['month'] = time_series.index.month     # "month" means that just because it is a time series dataframe, selecting month attribute will show up to index of each month.


    # Forecast duration
    forecast_years = 2
    forecast_months = forecast_years * 12
    if forecast_years == 0:
        forecast_months = 11

    # Ensure data is sufficient for forecasting
    if len(time_series) < 12:
        raise ValueError(f"The length of the time series ({len(time_series)}) is too short for the chosen forecast duration of {forecast_months} months.")

    # Sliding window forecasting with make_reduction
    window_size = 12    # 12 because of 12 months
    
    # Two different approaches
    lr_predictions = [] # Linear Regression
    arima_predictions = []  # ARIMA Model

    # Window Sliding Technique Implementation
    for i in range(len(time_series) - window_size):
        
        train = time_series['Sales'].iloc[i:i + window_size]
        X_exog_train = time_series[['month']].iloc[i:i + window_size]

        fh = ForecastingHorizon([1], is_relative=True)

        # Linear Regression model with make_reduction
        forecaster = make_reduction(LinearRegression(), strategy="recursive")
        forecaster.fit(train, X=X_exog_train)

        # Window Sliding Technique Implementation
        X_exog_next = time_series[['month']].iloc[i + window_size:i + window_size + 1]

        # Predict with the exogenous variable for the next step
        prediction_lr = forecaster.predict(fh, X=X_exog_next)
        lr_predictions.append(prediction_lr.iloc[0])  # Extract scalar prediction

        # ARIMA model with auto-tuning using pmdarima's auto_arima function
        arima_model = auto_arima(
            train, 
            seasonal=True, 
            m=12,  # Monthly seasonality
            stepwise=True,  # To improve the speed of the search
            trace=True,  # Display the progress of the search
            error_action='ignore',  # Ignore errors during the process
            suppress_warnings=True,  # Suppress warnings during model fitting
            d=0,
            D=0,
            start_p=5,
            max_p=9,
            start_q=5,
            max_q=9
        )
            

        # Forecast the next step
        prediction_arima = arima_model.predict(n_periods=1)[0]
        arima_predictions.append(prediction_arima)

    # Ensure we have enough predictions for the forecast duration
    #if len(lr_predictions) < forecast_months or len(arima_predictions) < forecast_months:
    #    raise ValueError(f"Expected {forecast_months} predictions, but got {len(lr_predictions)} (Linear Regression) and {len(arima_predictions)} (ARIMA).")

    # Define forecast index
    forecast_index = pd.date_range(
        time_series.index[-1] + pd.DateOffset(months=1),
        periods=forecast_months,
        freq='M'
    )
    
    # Adjusting the window that will be shown to user.
    min_length = min(len(forecast_index),min(len(arima_predictions), len(lr_predictions)))
    
    # Trying to find if the forecasting is true or not.
    lr_rmse = ((find_mse(time_series['Sales'][:min_length][:-1], lr_predictions[:min_length][:-1]) / len(lr_predictions[:-1])) ** 0.5)    # The dividend part should be the real existing length.
    arima_rmse = ((find_mse(time_series['Sales'][:min_length][:-1], arima_predictions[:min_length][:-1]) / len(arima_predictions[:-1])) ** 0.5)

    # Compute error boundaries for Linear Regression
    lr_upper = [pred + lr_rmse for pred in lr_predictions]
    lr_lower = [pred - lr_rmse for pred in lr_predictions]

    # Compute error boundaries for ARIMA
    arima_upper = [pred + arima_rmse for pred in arima_predictions]
    arima_lower = [pred - arima_rmse for pred in arima_predictions]


    # Crop the prediction to adjust for 2 years forecasting.     
    
    forecast_index = forecast_index[:min_length]
    arima_predictions = arima_predictions[:min_length]
    lr_predictions = lr_predictions[:min_length]
    arima_lower = arima_lower[:min_length]
    arima_upper = arima_upper[:min_length]
    lr_lower = lr_lower[:min_length]
    lr_upper = lr_upper[:min_length]

    
    # Storing RMSE Values

    # The indexes are the values and the values are the month numbers.
    # print(len(forecast_index))
    # print(len(lr_predictions))       # Linear Regression Absolute values
    # print(len(arima_predictions))    # Arima Prediction Absolute values.    

    # print(arima_predictions)
    
    # date_range_for_new_df = pd.date_range(start=(forecast_index.tolist())[-1], periods=len(arima_predictions), freq='M')
    
    # Combining the data with the original data to make function continuous.
    forecast_start_date = time_series.index[-1] + pd.Timedelta(days=1)
    forecast_date_range = pd.date_range(start=forecast_start_date, periods=len(arima_predictions), freq="ME")
    new_df = pd.DataFrame({'Date' : forecast_date_range , 'Sales' : arima_predictions}).set_index('Date')
    
    # Debugging Purpose
    # print(new_df.head())
    
    combined = pd.concat([time_series, new_df])

    # print(time_series.info())   # Values according to months. (Unpredicted values. Original data)

    # Export
    export(time_series=combined, forecasting=new_df, rmse=arima_rmse)

    # Export to database
    export_to_database(time_series=combined, forecasting=new_df, rmse=arima_rmse, db_config= db_config)

    # Plotting
    plotting(time_series=combined, forecast_index=forecast_index, lr_predictions=lr_predictions, arima_predictions=arima_predictions, arima_lower=arima_lower, arima_upper=arima_upper, lr_lower=lr_lower, lr_upper=lr_upper)


def plotting(time_series, forecast_index, lr_predictions, arima_predictions, arima_upper, arima_lower, lr_upper, lr_lower):
    """Tahmin grafiğini oluşturur ve veritabanına kaydeder."""
    plt.figure(figsize=(14, 8))
    plt.plot(time_series.index, time_series['Sales'], label="Actual Sales", color="blue", marker="o")
    plt.plot(forecast_index, lr_predictions, label="Linear Regression Forecast", linestyle="-", color="purple")
    plt.fill_between(forecast_index, lr_lower, lr_upper, color="purple", alpha=0.2)
    plt.plot(forecast_index, arima_predictions, label="ARIMA Forecast", linestyle="--", color="green")
    plt.fill_between(forecast_index, arima_lower, arima_upper, color="green", alpha=0.2)
    plt.title("Sales Forecasting with Linear Regression and ARIMA")
    plt.xlabel("Date")
    plt.ylabel("Sales")
    plt.legend()
    plt.grid()

    # Save the plot to a file
    plot_path = os.path.join(app.config['PLOT_FOLDER'], 'forecast_plot.png')
    plt.savefig(plot_path)
    plt.close()


def export_to_database(time_series, forecasting, rmse, db_config: DatabaseConfig):
    """Tahmin sonuçlarını veritabanına kaydeder."""
    try:
        # 1. Forecast verisini forecasted_with_error_values tablosuna kaydet
        forecasting['RMSE'] = rmse
        store_forecasted_with_error_values_in_sql(forecasting, db_config)
        print("Forecast verisi başarıyla forecasted_with_error_values tablosuna kaydedildi.")

        # 2. Combined veriyi combined_with_past_values tablosuna kaydet
        store_combined_with_past_values_in_sql(time_series, db_config)
        print("Combined veri başarıyla combined_with_past_values tablosuna kaydedildi.")

    except Exception as e:
        print(f"Veritabanına kaydetme sırasında bir hata oluştu: {e}")


def export(time_series, forecasting, rmse):
    """ Tahmin sonuçlarını zip file olarak depolar. """
    # Define the file names
    combined_data_file_name = "combined_time_series.xlsx"
    forecasted_data_set = "prediction.xlsx"

    # Define the path to the forecasted_data folder
    forecasted_data_folder = os.path.join(os.getcwd(), 'forecasted_data')

    # Ensure the folder exists
    if not os.path.exists(forecasted_data_folder):
        os.makedirs(forecasted_data_folder)

    # Indicating the error margin in the forecasting DataFrame
    forecasting['Data With ErrorMargin'] = [f"{sale} ± {rmse}" for sale in forecasting['Sales']]

    # Save the time_series and forecasting data as Excel files in the forecasted_data folder
    combined_data_path = os.path.join(forecasted_data_folder, combined_data_file_name)
    forecasted_data_path = os.path.join(forecasted_data_folder, forecasted_data_set)

    time_series.to_excel(combined_data_path)
    forecasting.to_excel(forecasted_data_path)


# Database connection details
def create_db_engine(db_config: DatabaseConfig):
    # Create SQLAlchemy engine
    engine = sqlalchemy_create_engine(f"mysql+mysqlconnector://{db_config.username}:{db_config.password}@{db_config.host}/{db_config.database}")
    return engine

def clear_table(db_config: DatabaseConfig, table_name):
    engine = create_db_engine(db_config)
    with engine.begin() as connection:  # Begin a transaction
        # Clear the table using DELETE
        connection.execute(text(f'DELETE FROM {table_name}'))

def store_combined_with_past_values_in_sql(df, db_config: DatabaseConfig):
    # Clear table and then store forecasted sales data
    clear_table(db_config, 'combined_with_past_values')
    df.to_sql(name='combined_with_past_values', con=create_db_engine(db_config), if_exists='replace', index=False)

def store_forecasted_with_error_values_in_sql(df, db_config: DatabaseConfig):
    # Clear table and then store forecasted sales data with exogenous variables
    clear_table(db_config, 'forecasted_with_error_values')
    df.to_sql(name='forecasted_with_error_values', con=create_db_engine(db_config), if_exists='replace', index=False)

def sql_table_to_pandas_table(table_name,db_config: DatabaseConfig):
    # Query the table and load it into a Pandas DataFrame
    table_name = table_name
    query = f"SELECT * FROM {table_name}"  # You can modify the query if needed
    df = pd.read_sql(query, con=create_db_engine(db_config))
    return df
