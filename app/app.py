import io
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for, Response
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import boto3
import os
import json
import docker  
import subprocess # Import the Docker library

app = Flask(__name__)

# ... Other configurations ...

# Create a Docker client
docker_client = docker.from_env()

# ... Other routes ...


# @app.route('/start-windows', methods=['GET'])
# def start_windows_docker_container():
#     try:
#         # Define the Docker Compose YAML content
#         docker_compose_yaml = """
#         version: "2"
#         services:
#           guacamole:
#             image: oznu/guacamole
#             container_name: guacamole
#             volumes:
#               - postgres:/config
#             ports:
#               - 8080:8080
#         volumes:
#           postgres:
#             driver: local
#         """
        
#         # Create a temporary Docker Compose file
#         with open('docker-compose.yml', 'w') as f:
#             f.write(docker_compose_yaml)
        
#         # Use subprocess to run the Docker Compose command
#         subprocess.run(['docker-compose', '-f', 'docker-compose.yml', 'up', '-d'], cwd=os.getcwd())
        
#         # Remove the temporary Docker Compose file
#         os.remove('docker-compose.yml')
        
#         return "Docker container started successfully."
#     except Exception as e:
#         return f"Error starting Docker container: {str(e)}"


@app.route('/start-windows', methods=['GET'])
def start_windows():
    try:
        # Use subprocess to run the external Docker Compose file
        subprocess.run(['docker-compose', '-f', 'docker-compose.yml', 'up', '-d'], cwd=os.getcwd())
        
        return "Docker container started successfully."
    except Exception as e:
        return f"Error starting Docker container: {str(e)}"

@app.route('/start-linux', methods=['GET'])
def start_linux():
    try:
        # Use subprocess to run the external Docker Compose file
        subprocess.run(['docker-compose', '-f', 'docker-compose.yml', 'up', '-d'], cwd=os.getcwd())
        
        return "Docker container started successfully."
    except Exception as e:
        return f"Error starting Docker container: {str(e)}"

# Configure MongoDB
app.config['MONGO_URI'] = 'mongodb://localhost:27017/cloudstorage'
mongo = PyMongo(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load AWS S3 credentials from config.json
with open('../s3_credentials/config.json', 'r') as config_file:
    config = json.load(config_file)

s3 = boto3.client(
    's3',
    aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY']
)
bucket_name = config['AWS_BUCKET_NAME']

# Define a User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


# Other routes for your application
# ...

# Create a user_loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Check if the uploaded file has an allowed file extension
              s3.upload_fileobj(file, bucket_name, file.filename)
    # List files in the S3 bucket
    objects = s3.list_objects(Bucket=bucket_name)
    files = [obj['Key'] for obj in objects.get('Contents', [])]
    return render_template('index.html', files=files)


@app.route('/download/<string:file_name>', methods=['GET'])
def download(file_name):
    # Download a file from S3
    file_data = s3.get_object(Bucket=bucket_name, Key=file_name)
    
    # Determine the Content-Type based on the file extension
    content_type = get_content_type(file_name)
    
    # Set the Content-Disposition header to specify the file name
    response = Response(file_data['Body'].read(), content_type=content_type)
    response.headers['Content-Disposition'] = f'attachment; filename={file_name}'
    
    return response


# Routes for user registration and login
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get registration data from the form
        username = request.form['username']
        password = request.form['password']

        # Check if the username is already in use (you may need to query MongoDB)
        # If not, create a new user and store their data in the database

        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get login data from the form
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password match (query MongoDB for user data)
        # If the user is found, log them in using login_user(user)

        flash('Login successful.')
        return redirect(url_for('index'))
    return render_template('login.html')



def get_content_type(file_name):
    # Set the Content-Type to "application/octet-stream" for all files
    return 'application/octet-stream'
    
    # Get the file extension from the file name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Use the mapping to determine the Content-Type
    return extension_to_content_type.get(file_extension, 'application/octet-stream')

@app.route('/remove', methods=['POST'])
def remove_file():
    if request.method == 'POST':
        data = json.loads(request.data)
        file_name = data.get('file')

        if file_name:
            try:
                # Delete the file from S3
                s3.delete_object(Bucket=bucket_name, Key=file_name)
                return jsonify({'message': f'{file_name} removed successfully'})
            except Exception as e:
                return jsonify({'error': str(e)})
        else:
            return jsonify({'error': 'Invalid request'})
    else:
        return jsonify({'error': 'Invalid request'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
