from flask import Flask, redirect, send_from_directory, session, url_for, request, render_template, flash, send_file
from google.auth.transport.requests import Request
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import google.oauth2.id_token
import os
import time
from werkzeug.security import check_password_hash   # For security of the code.
from werkzeug.utils import secure_filename  
import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import List
from werkzeug.security import generate_password_hash
from flask import current_app
from threading import Thread
import mysql.connector

def check_and_create_database():
    try:
        # Connect to MySQL server without specifying a database
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Avatar751"
        )
        cursor = connection.cursor()

        # Check if the database exists
        cursor.execute("SHOW DATABASES LIKE 'mydatabase'")
        result = cursor.fetchone()

        if result:
            print("Database 'mydatabase' already exists. No need to create it.")
        else:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE mydatabase")
            print("Database 'mydatabase' created successfully.")

        # Switch to the desired database
        cursor.execute("USE mydatabase")
        
        # Check if the table exists
        cursor.execute("SHOW TABLES LIKE 'users'")
        result = cursor.fetchone()

        if result:
            print("Table 'users' already exists. No need to create it.")
        else:
            # Create users table with the correct structure
            cursor.execute("""
            CREATE TABLE users (
                UserID varchar(5) NOT NULL,
                UserName varchar(50) NOT NULL,
                EMail varchar(100) NOT NULL,
                password varchar(255) NOT NULL,
                PRIMARY KEY (UserID)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            print("Table 'users' created successfully.")
        
        # Verify table structure
        cursor.execute("DESCRIBE users")
        table_structure = cursor.fetchall()
        print("\nTable structure:")
        for column in table_structure:
            print(column)

        connection.commit()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


def troubleshoot_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Avatar751",
            database="mydatabase"
        )
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'users'")
        table_exists = cursor.fetchone()
        print(f"Table exists: {bool(table_exists)}")
        
        if table_exists:
            # Get table structure
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            print("\nCurrent table structure:")
            for column in columns:
                print(f"Column: {column[0]}, Type: {column[1]}")
                
    except mysql.connector.Error as e:
        print(f"Troubleshooting error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


def init_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Avatar751",
            database="mydatabase"
        )
        
        cursor = connection.cursor()
        
        # Create users table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            UserID varchar(5) NOT NULL,
            UserName varchar(50) NOT NULL,
            EMail varchar(100) NOT NULL,
            password varchar(255) NOT NULL,
            PRIMARY KEY (UserID)
        );
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        print("Database initialized successfully")
        
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


UPLOAD_FOLDER = 'uploads'
PLOT_FOLDER = 'static/plots'

# Initialize Flask
init_database()
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key for session

# Admin email for access control
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)
ADMIN_EMAILS = ["emirkzlcm0@gmail.com"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        

class DatabaseConfig:
    def __init__(self, username: str, password: str, host: str, database: str):
        self.username = "root"
        self.password = "Avatar751"
        self.host = "localhost"
        self.database = "mydatabase"

    def get_connection_string(self) -> str:
        return f"mysql+mysqlconnector://{self.username}:{self.password}@{self.host}/{self.database}"


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Avatar751",
            database="mydatabase"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
    
# Google OAuth setup
base_path = os.getcwd()
CLIENT_SECRETS_FILE = os.path.join(base_path,"client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"]
REDIRECT_URI = "http://localhost:5000/callback"

# Initialize OAuth flow
flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

# Default profile picture
DEFAULT_PROFILE_PICTURE = "/static/assets/default_profile.png"


@app.route('/')
def base():
    return render_template("base.html")


@app.route('/home')
def home():
    # Login screen where the user chooses their login type
    return render_template("login.html")


@dataclass
class User:
    id: int
    username: str
    email: str

def load_users_from_database(db_config: DatabaseConfig) -> List[User]:
    """
    Veritabanından kullanıcıları yükler
    
    Args:
        db_config: DatabaseConfig nesnesi
        
    Returns:
        List[User]: Kullanıcı listesi
    """
    try:
        # Bağlantı dizesini al ve engine oluştur
        connection_string = db_config.get_connection_string()
        engine = create_engine(connection_string)
        
        # Session oluştur ve sorguyu çalıştır
        with Session(engine) as session:
            query = text("""
                    SELECT UserID, UserName, EMail, password FROM users 
                """)
            result = session.execute(query)
            users = [User(id=row[0], username=row[1], email=row[2]) for row in result]
            return users
            
    except Exception as e:
        print(f"Veritabanı hatası: {str(e)}")
        return []



# For password feature testing. 
import string
def validate_password(username, password, confirm_password):

    special_chars =  "!#$%&'()*+,-./:;<=>?@['\']^_`{|}~"
    lower_characters = string.ascii_lowercase
    upper_characters = string.ascii_uppercase


    # Checking if the password is written correctly.
    if password != confirm_password:
        return False, "The passwords do not match."
    
    # Checking the length.
    if len(password) < 8:
        return False, "The password should be at least 8 characters long."

    # Checking if at least 1 special character in the password.
    unsuccess = 0
    for char in password:
        if char in special_chars:    
            break
        else:
            unsuccess += 1
    
    # If the unsuccess is equal to the length of password. There is no special character.
    if unsuccess == len(password):
        return False, "The password should contain at least 1 special character"
    

    # Check for a lower character.
    unsuccess = 0
    for char in password:
        if char in lower_characters:
            break
        else:
            unsuccess += 1
    
    if unsuccess == len(password):
        return False, "The password should contain at least 1 lower character"
    
    # Check for an upper character.
    unsuccess = 0
    for char in password:
        if char in upper_characters:
            break
        else:
            unsuccess += 1
    
    if unsuccess == len(password):
        return False, "The password should contain at least 1 upper character."
    
    # Check if password contains the username.
    username = username.lower()
    password = password.lower()
    if username in password:
        return False, "The password should not contain the username."

    return True, "The password is set correctly."


def validate_username(username):

    letters_in_ascii = string.ascii_letters
    special_chars =  "!#$%&'()*+,-./:;<=>?@['\']^`{|}~" # Except "_".

    # Check the length.
    if len(username) < 4:
        return False, "The username should be at least 4 characters long."

    # Check if the username contains special characters.
    for char in username:
        if char in special_chars:
            return False, "The username can not contain special characters."
    
    # Check if the username contains blank spaces.
    blank_spaces_username = "".join(username.split())
    if len(blank_spaces_username) != len(username):
        return False, "The username can not contain blank spaces." 
    
    # Check if the character contains non-ascii characters.
    for char in username:
        if char not in letters_in_ascii:
            return False, "The username should contain only ASCII letters."
        
    return True, "The username is valid and correct."

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        is_password_valid, message = validate_password(username=name, password=password, confirm_password=confirm_password)
        # Check Password
        if not is_password_valid:
            flash(message)
            return redirect(url_for('register'))

        is_username_valid, message = validate_username(username=name)
        if not is_username_valid:
            flash(message)
            return redirect(url_for('register'))

        # Konfigürasyon nesnesini bir kere oluştur
        db_config = DatabaseConfig(
            username="root",
            password="Avatar751",
            host="localhost",
            database="mydatabase"
        )            

        existing_users = load_users_from_database(db_config)
        
        # UserID oluşturma mantığı
        if not existing_users:
            user_id = "00001"
        else:
            last_user = max(existing_users, key=lambda x: x.id)
            next_id = int(last_user.id) + 1
            user_id = f"{next_id:05d}"  # 5 haneli formatta

        # Mevcut kullanıcıları kontrol et
        for user in existing_users:
            if user.email == email:
                flash('Bu email adresi zaten kayıtlı!')
                return redirect(url_for('register'))
                    
        try:
            # Veritabanı bağlantısı
            engine = create_engine(db_config.get_connection_string())

            # Yeni kullanıcıyı kaydet
            with Session(engine) as session:
                hashed_password = generate_password_hash(password)
                query = text("""
                    INSERT INTO users (UserID, UserName, EMail, password) 
                    VALUES (:user_id, :name, :email, :password)
                """)
                session.execute(query, {
                    'user_id': user_id,
                    'name': name,
                    'email': email,
                    'password': password
                })
                session.commit()
                
            flash('Registration successful! Please log in.')
            return redirect(url_for('home'))
            
        except Exception as e:
            flash(f'Kayıt sırasında bir hata oluştu: {str(e)}')
            return redirect(url_for('register'))
            
    return render_template('register.html')



@app.route('/login/user')
def login():
    # Check if the user is already logged in via email/password
    if "user_info" in session:
        return redirect(url_for('base'))  # Redirect to base if already logged in

    # Start the Google OAuth flow
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/login/user', methods=['POST'])
def login_user():
    try:
        connection = get_db_connection()
        if not connection:
            flash("Database connection failed.")
            return redirect(url_for("home"))
        
        cursor = connection.cursor(dictionary=True)
        email = request.form['email']
        password = request.form['password']
        
        # Query user from database
        cursor.execute("SELECT UserID, UserName, EMail, password FROM users WHERE EMail = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            flash("Email not registered.")
            return redirect(url_for("home"))
        
        if user['password'] != password:  # In production, use proper password hashing
            flash("Incorrect password.")
            return redirect(url_for("home"))
        
        # Store user info in session
        session['user_info'] = {
            'id': user['UserID'],
            'name': user['UserName'],
            'email': user['EMail']
        }

        flash("Login successful!")
        return redirect(url_for('profile'))
        
    except Error as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for("home"))
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route("/login/user")
def google_login():
    # Default user_info to None
    user_info = None

    # Check if the user is logged in via normal email/password or Google OAuth
    if "user_info" not in session and "credentials" not in session:
        return redirect(url_for("login"))  # Redirect to login if not logged in

    # If logged in via email/password
    if "user_info" in session:
        user_info = session["user_info"]

    # If logged in via Google OAuth
    elif "credentials" in session:
        credentials = Credentials(**session["credentials"])
        if "id_token" not in session["credentials"]:
            return "Error: No id_token in session", 400
        
        try:
            # Verify the Google OAuth2 token
            id_info = google.oauth2.id_token.verify_oauth2_token(session["credentials"]["id_token"], Request())

            # Extract user information
            user_info = {
                'name': id_info.get('name'),
                'email': id_info.get('email'),
                'picture': id_info.get('picture', DEFAULT_PROFILE_PICTURE),
                'role': 'Admin' if id_info.get('email') in ADMIN_EMAILS else 'User'  # Determine if the user is an admin
            }

            # Store user_info in the session
            session["user_info"] = user_info
        except ValueError:
            return "Error: Invalid ID Token", 400

    # Pass user_info to the template
    return render_template("dashboard.html", user_info=user_info)



@app.route("/callback")
def callback():
    if "state" not in session or session["state"] != request.args.get("state"):
        return "Error: State mismatch", 400

    # Fetch credentials using the authorization response
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "id_token": credentials.id_token
    }

    # Add delay to simulate processing time (if needed)
    time.sleep(4)

    try:
        # Verify the Google ID Token
        id_info = google.oauth2.id_token.verify_oauth2_token(session["credentials"]["id_token"], Request())
        
        # Store user information in session
        session["user_info"] = {
            "name": id_info.get("name"),
            "email": id_info.get("email"),
            "picture": id_info.get("picture", DEFAULT_PROFILE_PICTURE)
        }

        # Set role based on email
        session["user_info"]["role"] = 'Admin' if session["user_info"]["email"] in ADMIN_EMAILS else 'User'
    except ValueError:
        return "Error: Invalid ID Token", 400

    # Redirect to the appropriate profile page based on the role
    if session["user_info"]["role"] == "Admin":
        return redirect(url_for("profile"))
    else:
        return redirect(url_for("profile"))




@app.route('/unauthorized')
def unauthorized():
    session.clear()
    return render_template("unauthorized.html")


import os
import shutil

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()

    # Define the paths to the directories
    upload_folder = app.config['UPLOAD_FOLDER']
    forecasted_data_folder = os.path.join(app.root_path, 'forecasted_data')
    plots_folder = app.config['PLOT_FOLDER']

    # Function to delete all files in a folder
    def delete_files_in_folder(folder_path):
        if os.path.exists(folder_path):
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)  # Remove individual file
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove directory and its contents
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

    # Delete files in all relevant folders
    delete_files_in_folder(upload_folder)
    delete_files_in_folder(forecasted_data_folder)
    delete_files_in_folder(plots_folder)

    # Redirect to the home or base page
    return redirect(url_for('base'))

@app.route('/dashboard')
def Dashboard():
    return render_template("dashboard.html", user_info=session.get("user_info"))


# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}  # Add .xls support
def allowed_file(filename):
    return '.' in filename and filename.rstrip().rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


import os
import shutil

@app.route('/form-elements', methods=['GET', 'POST'])
def FormElements():
    if request.method == 'POST':
        # Ensure file part exists
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)

        files = request.files.getlist('file')  # Allow multiple files

        if not files:
            flash("No files selected")
            return redirect(request.url)

        # Clear existing files in the forecast_data/ and static/plots/ directories if uploading new data
        # You can modify this logic if needed (based on user selection)
        forecast_data_dir = os.path.join(app.config['UPLOAD_FOLDER'])
        plots_dir = os.path.join(app.config['PLOT_FOLDER'])
       

        # Delete all files in forecast_data/
        if os.path.exists("forecasted_data"):
            for filename in os.listdir("forecasted_data"):
                file_path = os.path.join("forecasted_data", filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

        # Delete all files in static/plots/
        if os.path.exists(plots_dir):
            for filename in os.listdir(plots_dir):
                file_path = os.path.join(plots_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

        # Save uploaded files
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                print(f"File saved to: {file_path}")  # Debugging: Ensure file is saved
            else:
                flash(f"Invalid file: {file.filename}")

        # Konfigürasyon nesnesini bir kere oluştur
        db_config = DatabaseConfig(
            username="root",
            password="Avatar751",
            host="localhost",
            database="mydatabase"
        )

        # Algoritmanın calistigi yer
        fc.future_forcasting(len(files), db_config=db_config)

        flash("Forecast process is completed!")
        flash("Files uploaded successfully!")
        return redirect(url_for('Table'))  # Redirect to table route

    return render_template("form_element.html", user_info=session.get("user_info"))


@app.route('/profile')
def profile():
    user_info = session.get("user_info")
    if not user_info:
        return redirect(url_for("login"))
    return render_template("profile.html", user_info=user_info)


@app.route('/about')
def About():
    return render_template("about.html", user_info=session.get("user_info"))

import forecasting as fc

def delete_files_in_directory(directory_path):
   try:
     files = os.listdir(directory_path)
     for file in files:
       file_path = os.path.join(directory_path, file)
       if os.path.isfile(file_path):
         os.remove(file_path)
     print("All files deleted successfully.")
   except OSError:
     print("Error occurred while deleting files.")


import zipfile
@app.route('/download_all_forecasted_files')
def download_all_forecasted_files():
    forecasted_data_folder = os.path.join(app.root_path, 'forecasted_data')
    forecasted_files = [f for f in os.listdir(forecasted_data_folder) if f.endswith('.xlsx')]

    # Create a ZIP file containing all the forecasted files
    zip_filename = 'forecasted_files.zip'
    zip_filepath = os.path.join(app.root_path, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for file in forecasted_files:
            file_path = os.path.join(forecasted_data_folder, file)
            zipf.write(file_path, os.path.basename(file_path))

    # Send the ZIP file to the user
    return send_file(zip_filepath, as_attachment=True)



import pandas as pd

@app.route('/table')
def Table():
    # Validate user session
    user_info = session.get("user_info")
    if not user_info:
        flash("Session expired or not set.")
        return redirect(url_for('FormElements'))

    # Check uploaded files
    forecasted_data_folder = os.path.join(app.root_path, 'forecasted_data')
    forecasted_files = [f for f in os.listdir(forecasted_data_folder) if f.endswith('.xlsx')]

    uploaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.xlsx', '.xls'))]
    if len(uploaded_files) < 1:
        flash("Please upload at least 1 Excel file.")
        return redirect(url_for('FormElements'))

    try:
        # Path to the forecast plot
        plot_path = os.path.join(app.config['PLOT_FOLDER'], 'forecast_plot.png')

        # Check if the plot already exists
        if not os.path.exists(plot_path):
            # Generate and save the forecast plot
            # fc.window_sliding_technique(len(uploaded_files) + 3)
            
            # Check if the plot was successfully generated
            if not os.path.exists(plot_path):
                flash("Error: Plot was not generated.")
                return redirect(url_for('FormElements'))

        # Read time series data from the generated Excel file
        time_series_data = []
        time_series_file = os.path.join(forecasted_data_folder, 'combined_time_series.xlsx')  # Adjust filename as needed
        if os.path.exists(time_series_file):
            # Read the Excel file into a DataFrame
            df = pd.read_excel(time_series_file)
            time_series_data = df.to_dict(orient='records')  # Convert DataFrame to list of dictionaries

        # Pass forecasted files, plot image, and time series data to template
        return render_template(
            "table.html",
            #plot_image = os.path.join(app.config['PLOT_FOLDER'], 'forecast_plot.png'),
            plot_image='plots/forecast_plot.png',
            forecasted_files=forecasted_files,
            time_series_data=time_series_data,
            user_info=user_info
        )

    except Exception as e:
        flash(f"Error generating graph: {str(e)}")
        return redirect(url_for('FormElements'))

@app.route('/settings')
def Settings():
    return render_template("settings.html", user_info=session.get("user_info"))

@app.route('/contact')
def Contact():
    return render_template("contact.html", user_info=session.get("user_info"))

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'arasaka_icon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == "__main__":
    troubleshoot_database()
    check_and_create_database()
    app.run("localhost", 5000, debug=True)

             
