from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import boto3
import uuid

from werkzeug.utils import secure_filename
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# AWS Configuration 
REGION = 'us-east-1' 

dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

# DynamoDB Tables (Create these tables in DynamoDB manually)
users_table = dynamodb.Table('Users')
admin_users_table = dynamodb.Table('AdminUsers')
projects_table = dynamodb.Table('Projects')
enrollments_table = dynamodb.Table('Enrollments')

# SNS Topic ARN (Replace with your actual SNS Topic ARN)
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:604665149129:aws_capstone_topic' 

# Configuration for File Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def send_notification(subject, message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print(f"Error sending notification: {e}")

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists
        response = users_table.get_item(Key={'username': username})
        if 'Item' in response:
            return "User already exists!"
        
        # Add user
        users_table.put_item(Item={'username': username, 'password': password})
        
        # Notify
        send_notification("New User Signup", f"User {username} has signed up.")
        
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        response = users_table.get_item(Key={'username': username})
        
        if 'Item' in response and response['Item']['password'] == password:
            session['username'] = username
            send_notification("User Login", f"User {username} has logged in.")
            return redirect(url_for('home'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        
        # Get user enrollments
        response = enrollments_table.get_item(Key={'username': username})
        user_enrollments_ids = response.get('Item', {}).get('project_ids', [])
        
        # Get all projects needed
        my_projects = []
        if user_enrollments_ids:
            for pid in user_enrollments_ids:
                 p_res = projects_table.get_item(Key={'id': pid})
                 if 'Item' in p_res:
                     my_projects.append(p_res['Item'])

        return render_template('home.html', username=username, my_projects=my_projects)
    return redirect(url_for('login'))

@app.route('/projects')
def projects_list():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    
    # Get enrollments to show status
    res_enroll = enrollments_table.get_item(Key={'username': username})
    user_enrollments_ids = res_enroll.get('Item', {}).get('project_ids', [])
    
    # Scan all projects
    res_projects = projects_table.scan()
    projects = res_projects.get('Items', [])
    
    return render_template('projects_list.html', projects=projects, user_enrollments=user_enrollments_ids)

@app.route('/enroll/<project_id>')
def enroll(project_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    
    # Get current enrollments
    response = enrollments_table.get_item(Key={'username': username})
    current_enrollments = response.get('Item', {}).get('project_ids', [])
    
    if project_id not in current_enrollments:
        current_enrollments.append(project_id)
        enrollments_table.put_item(Item={'username': username, 'project_ids': current_enrollments})
        send_notification("Project Enrollment", f"User {username} enrolled in project ID {project_id}")
        
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        response = admin_users_table.get_item(Key={'username': username})
        if 'Item' in response:
            return "Admin already exists!"
        
        admin_users_table.put_item(Item={'username': username, 'password': password})
        send_notification("Admin Signup", f"Admin {username} registered.")
        return redirect(url_for('admin_login'))
    return render_template('admin_signup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        response = admin_users_table.get_item(Key={'username': username})
        
        if 'Item' in response and response['Item']['password'] == password:
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        return "Invalid admin credentials!"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Scan everything for dashboard summary
    users = users_table.scan().get('Items', [])
    projects = projects_table.scan().get('Items', [])
    enrollments = enrollments_table.scan().get('Items', []) # This returns list of dicts {'username':..., 'project_ids':...}
    
    enrollments_dict = {item['username']: item['project_ids'] for item in enrollments}
    
    # Convert users list to dict
    users_dict = {u['username']: u['password'] for u in users}

    return render_template('admin_dashboard.html', username=session['admin'], projects=projects, users=users_dict, enrollments=enrollments_dict)

@app.route('/admin/create-project', methods=['GET', 'POST'])
def admin_create_project():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
        
    if request.method == 'POST':
        title = request.form['title']
        problem_statement = request.form['problem_statement']
        solution_overview = request.form['solution_overview']
        
        # Handle File Uploads (Still Local)
        image = request.files['image']
        document = request.files['document']
        
        image_filename = None
        doc_filename = None

        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            
        if document:
            doc_filename = secure_filename(document.filename)
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], doc_filename))
            
        # Create Project ID (UUID)
        project_id = str(uuid.uuid4())
        
        new_project = {
            'id': project_id,
            'title': title,
            'problem_statement': problem_statement,
            'solution_overview': solution_overview,
            'image': image_filename,
            'document': doc_filename
        }
        
        projects_table.put_item(Item=new_project)
        send_notification("New Project", f"Project '{title}' has been created.")
        
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin_create_project.html', username=session['admin'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
