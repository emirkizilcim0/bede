# User Manual for BEDE

---

## 1. Installation and Deployment Instructions

### Technical Specifications

- **Programming Language**: Python (Flask Framework)
- **Database**: MySQL
- **Dependencies**: Listed in `requirements.txt`
- **Port**: Default is `localhost:5000`

### Prerequisites

1. **Python**: Ensure Python 3.8+ is installed.
2. **MySQL Server**: Install and configure MySQL.
3. **Pip**: Install Python package manager.
4. **Google OAuth**: Requires a `client_secret.json` file for Google login.

Those are the requirements that you need to instantiate your program.
```python
Flask==2.2.5
Flask-SQLAlchemy==2.5.1
mysql-connector-python==8.0.33
SQLAlchemy==1.4.47
Werkzeug==2.2.3
pandas==1.5.3
matplotlib==3.7.1
pmdarima==2.0.3
sktime==0.14.1
scikit-learn==1.2.2
Google-Auth==2.20.0
Google-Auth-OAuthlib==1.0.0
Google-Auth-Transport-Requests==2.0.0
numpy==1.26.4
```

### Steps to Deploy

1. **Clone the Repository**
    
    ```bash
    git clone <repository_url>
    cd <repository_folder>
    ```
    
2. **Install Dependencies**
    
    ```bash
    pip install -r requirements.txt
    ```
    
3. **Configure MySQL Database**
    
    - Login to MySQL and create the `mydatabase` database:
        
        ```sql
        CREATE DATABASE mydatabase;
        ```
        
    - Update MySQL credentials in `app.py` and `forecasting.py` if needed.
4. **Run Initial Setup**
    
    - Start the database initialization and table creation:
        
        ```bash
        python app.py
        ```
        
5. **Run the Application**
    
    - Start the Flask server:
        
        ```bash
        flask run
        ```
        
    - Access the app in your browser at `http://localhost:5000`.

---

## 2. System Features Overview

### Main Features

- **User Authentication**:
    - Login via Google OAuth or email/password.
    - Admin and user roles.
- **Data Forecasting**:
    - Upload Excel files containing sales data.
    - Forecast future sales using Linear Regression and ARIMA models.
- **Data Visualization**:
    - Displays actual and forecasted sales with detailed graphs.
- **Export Features**:
    - Download all forecasted files in a single ZIP file.
- **User Management**:
    - Secure registration with validation.
    - Profile management.
- **Settings & Help**:
    - Settings page for configuration.
    - Contact page for support.

---

## 3. Walkthrough: Main Scenario

### Goal: Forecast Sales from Uploaded Data

1. **Login**
    
    - Open the app and log in via Google or email/password.
2. **Navigate to Form Elements**
    
    - Click "Form Elements" in the navigation bar.
    - Upload one or more Excel files.
3. **Initiate Forecasting**
    
    - Click "Submit" after uploading.
    - Wait for the process to complete.
    - A confirmation message will appear.
4. **View Results**
    
    - Navigate to the "Table" page.
    - View the forecasted data and graph.
5. **Download Results**
    
    - Click "Download All Forecasted Files" to save the results.

### Screenshot Examples

**Login Page:**![[Pasted image 20241228143247.png]]


**Form Elements:** ![[Pasted image 20241228143043.png]]

**Forecast Graph:** ![[Pasted image 20241228143136.png]]


This is demo version. The Front-End will get some upgrades. But the main logic behind the code will stay still.

---

## 4. Additional Scenarios

### Scenario 1: User Registration

1. Go to the registration page.
2. Fill in the details:
    - Name
    - Email
    - Password (must meet the complexity requirements).
3. Submit the form.
4. Receive a confirmation and proceed to login.

### Scenario 2: Data Management for Admins

1. Log in as an admin.
2. Navigate to the "Settings" page.
3. View and manage uploaded files and generated forecasts.
4. Clear old data if needed using provided options.


---

## 5. Personas Integration

### Jade: The Data Analyst

- **Pain Point**: Resistance to new tools due to time constraints.
- **Solution**: BEDE’s intuitive interface ensures a seamless transition with minimal training required.
- **Feature Highlight**: Familiar UI and easy-to-follow workflows.

### Elif Demir: The Systems Administrator

- **Pain Point**: Streamlining user onboarding.
- **Solution**: Centralized settings and straightforward user registration.
- **Feature Highlight**: Robust user management tools and clear documentation.

### Dexter Morgan: The Hospital Manager

- **Pain Point**: Managing complex accounting tasks with limited experience.
- **Solution**: Simple forecasting tools and easy access to graphs and data exports.
- **Feature Highlight**: Detailed yet accessible graphs to aid decision-making.

---

## 6. Logic of the Code

# Sales Forecasting Application Documentation

## Overview
This application is a web-based sales forecasting system that combines time series analysis with user authentication and data visualization. The system uses both Linear Regression and ARIMA models to predict future sales based on historical data.

## Core Components

### 1. Forecasting Module (forecasting.py)

#### Key Features:
- Time series analysis using both Linear Regression and ARIMA models
- Window sliding technique for improved prediction accuracy
- Error margin calculation and visualization
- Database integration for storing results
- Export functionality for forecast results

#### Main Functions:

a) `future_forcasting(n, db_config)`
- Core forecasting function
- Parameters:
  - n: Number of input data files
  - db_config: Database configuration object
- Process:
  1. Loads data from Excel files
  2. Processes time series data
  3. Applies both Linear Regression and ARIMA models
  4. Calculates error margins
  5. Generates visualizations
  6. Exports results

b) `dataframe_completer(df, name_of_the_column_with_NaN)`
- Handles missing data in the input
- Uses different interpolation methods based on data length:
  - 12 months: Linear interpolation
  - 24 months: Quadratic interpolation
  - Others: Polynomial interpolation (order 3)

c) `plotting()`
- Creates visualization of forecasts
- Shows:
  - Actual sales data
  - Linear Regression predictions
  - ARIMA predictions
  - Confidence intervals for both models

d)`find_mse(data, predicted_data)`
- Calculates the boundaries of the predicted data.

e)`find_mse(data, predicted_data)`
- Calculates the boundaries of the predicted data.

f) **`allowed_file(filename)`**

This function checks whether a file is allowed for processing based on its extension.
- It ensures that the filename contains a period (`.`), indicating it has an extension.
- It then extracts the extension by splitting the filename at the last period and checks if it’s in the allowed list of extensions (e.g., `.xlsx`, `.xls`).
- Returns `True` if the extension is allowed, `False` otherwise.

This function is useful for filtering the files that users upload to ensure only supported file types are processed.

g) **`dframe_returner(number_of_input_folders)`**

This function reads and returns data from Excel files uploaded to a specific folder.

- The function checks if the number of input folders is valid (at least 1).
- It constructs the path to the "uploads" folder and iterates through all files in the folder.
- It selects files with extensions `.xlsx` or `.xls`, reads them into a pandas DataFrame using `pd.read_excel`, and handles missing data in the columns using the `dataframe_completer` function.
- All DataFrames are concatenated into one large DataFrame and returned.

This function is useful when users upload multiple Excel files for processing, and it consolidates the data into a single DataFrame for further analysis.

h) **`complete_missing_data(df)`**

This function handles missing values in a DataFrame.

- It checks each column in the DataFrame to see if it contains missing values (`NaN`).
- If a column has missing values and is numeric or categorical, it will use the `dataframe_completer` function to fill in the missing values.
- The modified DataFrame is returned with missing data filled.

This function is essential for preparing data for analysis or forecasting, ensuring that missing values do not affect the results.

i) **`dataframe_completer(df, name_of_the_column_with_NaN)`**

This function completes missing values in a specific column of the DataFrame using different interpolation methods based on the length of the DataFrame.

- The function checks the length of the DataFrame. If the length is:
    - 12, linear interpolation is used.
    - 24, quadratic interpolation is used.
    - For other lengths, cubic polynomial interpolation is used.
- It interpolates missing values using the appropriate method for the column `name_of_the_column_with_NaN`.

This function is critical for filling in missing values in a way that maintains data trends. Different interpolation methods are used based on the structure of the data, which helps in forecasting or analysis.

##### Connection with `app.py`:

- In the Flask application (`app.py`), these functions would be used within routes that handle file uploads, data processing, and model forecasting.
- For example, when a user uploads a file, the `dframe_returner` and `complete_missing_data` functions would be called to process the data before performing any forecasting.
- The results of the forecasting, including error metrics like MSE, can be returned to the user for evaluation.
### 2. Web Application (app.py)

#### Key Features:
- User authentication (Email/Password and Google OAuth)
- File upload handling
- Database management
- Results visualization
- Secure session management

#### Main Routes:

1. Authentication Routes:
```python
@app.route('/login/user')
@app.route('/register')
@app.route('/logout')
```
- Handles user registration and login
- Supports both traditional and Google OAuth authentication
- Implements security measures for passwords and usernames

2. Dashboard and Data Management:
```python
@app.route('/dashboard')
@app.route('/form-elements')
@app.route('/table')
```
- File upload interface
- Results visualization
- Download functionality for forecasted data


## Database Structure

### Users Table
```sql
CREATE TABLE users (
    UserID varchar(5) NOT NULL,
    UserName varchar(50) NOT NULL,
    EMail varchar(100) NOT NULL,
    password varchar(255) NOT NULL,
    PRIMARY KEY (UserID)
)
```

### Forecast Tables
- `combined_with_past_values`: Stores historical and predicted values
- `forecasted_with_error_values`: Stores predictions with error margins

## Security Features

1. Password Validation:
- Minimum 8 characters
- Special character requirement
- Upper and lowercase letters required
- Username cannot be part of password

2. Username Validation:
- Minimum 4 characters
- No special characters allowed
- No spaces allowed
- ASCII characters only

3. Session Management:
- Secure session handling
- Automatic logout functionality
- File cleanup on logout

## Usage Flow

1. User Registration/Login:
   - Register with email/password or use Google OAuth
   - Validate credentials
   - Create session

2. Data Upload:
   - Upload Excel files (.xlsx, .xls)
   - System validates file format
   - Files stored in temporary upload folder

3. Forecasting Process:
   - System reads uploaded files
   - Applies forecasting models
   - Generates visualizations
   - Stores results in database

4. Results View:
   - Display forecasting graphs
   - Show prediction tables
   - Enable data download
   - Provide error margins

5. Data Export:
   - Download combined results
   - Access individual forecasts
   - Export visualizations

## Error Handling

The application implements comprehensive error handling:
- File upload validation
- Database connection errors
- Authentication failures
- Missing data handling
- Invalid input detection

## Technical Requirements

- Python 3.x
- Flask web framework
- MySQL database
- Required Python packages:
  - pandas
  - numpy
  - scikit-learn
  - pmdarima
  - matplotlib
  - sqlalchemy
  - google-auth
  - werkzeug

## File Structure
```
/
├── uploads/                 # Temporary file storage
├── static/
│   ├── plots/              # Generated visualizations
│   └── assets/             # Static resources
├── forecasted_data/        # Output files
├── templates/              # HTML templates
├── app.py                  # Web application
└── forecasting.py          # Forecasting logic
```

## Best Practices for Use

1. Data Preparation:
   - Use consistent date formats
   - Ensure sales data is numeric
   - Avoid empty cells in important columns
   - Maintain consistent column names

2. File Upload:
   - Use recent Excel file formats
   - Keep file sizes reasonable
   - Ensure data is properly formatted
   - Verify column headers match expected format

3. Interpreting Results:
   - Consider both model predictions
   - Review error margins
   - Compare with historical trends
   - Use forecasts as guidance, not absolute truth

4. Security:
   - Use strong passwords
   - Keep login credentials secure
   - Log out after sessions
   - Don't share account access
  

