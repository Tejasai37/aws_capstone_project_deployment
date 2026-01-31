from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configuration for File Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory database (dictionary)
users = {}
admin_users = {}
projects = []  
enrollments = {} 

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
        
        if username in users:
            return "User already exists!"
        
        users[username] = password
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        user_enrollments_ids = enrollments.get(username, [])
        
        my_projects = [p for p in projects if p['id'] in user_enrollments_ids]
        
        return render_template('home.html', username=username, my_projects=my_projects)
    return redirect(url_for('login'))

@app.route('/projects')
def projects_list():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    user_enrollments_ids = enrollments.get(username, [])
    
    return render_template('projects_list.html', projects=projects, user_enrollments=user_enrollments_ids)

@app.route('/enroll/<int:project_id>')
def enroll(project_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    
    if username not in enrollments:
        enrollments[username] = []
        
    if project_id not in enrollments[username]:
        enrollments[username].append(project_id)
        
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
        
        if username in admin_users:
            return "Admin already exists!"
        
        admin_users[username] = password
        return redirect(url_for('admin_login'))
    return render_template('admin_signup.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in admin_users and admin_users[username] == password:
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        return "Invalid admin credentials!"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', username=session['admin'], projects=projects, users=users, enrollments=enrollments)

@app.route('/admin/create-project', methods=['GET', 'POST'])
def admin_create_project():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
        
    if request.method == 'POST':
        title = request.form['title']
        problem_statement = request.form['problem_statement']
        solution_overview = request.form['solution_overview']
        
        # Handle File Uploads
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
            
        # Create Project ID (simple auto-increment)
        project_id = len(projects) + 1
        
        new_project = {
            'id': project_id,
            'title': title,
            'problem_statement': problem_statement,
            'solution_overview': solution_overview,
            'image': image_filename,
            'document': doc_filename
        }
        
        projects.append(new_project)
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin_create_project.html', username=session['admin'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
