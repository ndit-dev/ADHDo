## --TODO LIST-------------------------------------------------------------
## TODO: remove reset checkmar message, and make sure extra update is not needed
##
## TODO: reset tasks checkmarks during the night
## TODO: recurring tasks / ever present tasks
## TODO: Stylyze the pages with CSS
## TODO: Make sure the UX/IX works good on phones and tablets
## ------------------------------------------------------------------------


## ---- ##
## INIT ##
## ---- ##

# Import necessary libraries
from flask import Flask, request, jsonify, render_template, redirect, flash, send_file, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.expression import func
from collections import defaultdict
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from datetime import datetime, time
import os
import secrets
import sqlite3
import time as time_module

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

## -------- ##
## DATABASE ##
## -------- ##

# Configure SQLAlchemy with SQLite database
# Default database path
db_path = 'sqlite:////adhdo_app/data/adhdo.db'

app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Category model for storing task categories
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    name = db.Column(db.String(50), nullable=False) # Category name
    tasks = db.relationship('Task', backref='category', lazy=True) # Relationship to tasks
    is_visible = db.Column(db.Boolean, default=True) # Visibility toggle
    sort_order = db.Column(db.Integer, nullable=False, default=0) # Sort order

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_visible': self.is_visible # assuming is_visible is a field in your model
        }

# Task model for storing tasks
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    title = db.Column(db.String(50), nullable=False) # Task title
    completed = db.Column(db.Boolean, default=False) # Completion status
    sort_order = db.Column(db.Integer, nullable=False, default=0) # Sort order
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True) # Foreign key to category

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'sort_order': self.sort_order,
            'category_id': self.category.id,
        }
    
# Settings model for storing application settings
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key, even though we will only have one row
    lastReset = db.Column(db.DateTime, default=datetime.now) # Timestamp of the last time the app was opened
    resetTime = db.Column(db.Time, default=time(3, 0), nullable=True)  # Time of the day for daily reset, default to 03:00

    def to_dict(self):
        return {
            'id': self.id,
            'lastReset': self.lastReset,
            'resetTime': self.resetTime
        }


# create the database
with app.app_context():
    db.create_all()    

    # Check if there's no row in Settings
    if not Settings.query.first():
        default_settings = Settings()  # This will use the default values defined in the model
        db.session.add(default_settings)
        db.session.commit()

## ------ ##
## ROUTES ##
## ------ ##

# default route
@app.route('/', methods=['GET'])
def home():
    # Query tasks and manually group by category
    category_alias = aliased(Category)
    tasks = (
        Task.query
        .join(category_alias, Task.category)
        .order_by(category_alias.sort_order, category_alias.name, Task.sort_order, Task.id)
        .options(joinedload(Task.category))
        .all()
    )

    grouped_tasks = defaultdict(list)
    for task in tasks:
        # Add the category object to the list
        grouped_tasks[task.category].append(task)

    return render_template('index.html', grouped_tasks=grouped_tasks)




## TASKS ##

# Route to add a new task, accessible via POST request
@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form.get('task-title')
    category_name = request.form.get('category')

    # make sure the new task has the highest sort order
    highest_task_sort_order = db.session.query(db.func.max(Task.sort_order)).scalar()
    task_sort_order = (highest_task_sort_order or 0) + 1

    # Check if category name is provided
    if not category_name:
        flash('Category must be provided', 'error')
        return redirect('/')

    # Step 1: Look for an existing category
    category = Category.query.filter_by(name=category_name).first()

    # Step 2: If not found, create, commit, and query again
    if not category:

        # make sure the new category has the highest sort order
        highest_category_sort_order = db.session.query(db.func.max(Category.sort_order)).scalar()
        category_sort_order = (highest_category_sort_order or 0) + 1

        new_category = Category(name=category_name, sort_order=category_sort_order)
        db.session.add(new_category)
        db.session.commit()
        category = Category.query.filter_by(name=category_name).first()

    # Step 3: Create the task with the retrieved category
    new_task = Task(title=title, completed=False, category=category, sort_order=task_sort_order)
    db.session.add(new_task)
    db.session.commit()

    task_dict = new_task.to_dict() # assuming to_dict method is defined in Task model
    category_dict = category.to_dict()

    return jsonify(status='success', task=task_dict, category=category_dict, category_id=category.id)

# View tasks from a specific category
@app.route('/get_tasks/<category_name>', methods=['GET'])
def get_tasks_by_category(category_name):
    # Find the specified category
    category = Category.query.filter_by(name=category_name).first()
    if category is None:
        return jsonify({"error": "Category not found"}), 404

    # Query all tasks for that category
    tasks = Task.query.filter_by(category_id=category.id).all()

    # Convert the tasks to a dictionary format
    tasks_dict = [{"title": task.title, "completed": task.completed} for task in tasks]

    # Convert the dictionary to a JSON response
    return jsonify(tasks_dict)

@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    completed = request.form['completed'] == 'true'
    task = Task.query.get(task_id)
    task.completed = completed
    db.session.commit()
    return jsonify(success=True)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = db.session.query(Task).filter_by(id=task_id).first()
    category_deleted = False
    
    if task:
        category_id = task.category_id
        db.session.delete(task)
        db.session.commit()

        # Check if the category is now empty
        task_count = Task.query.filter_by(category_id=category_id).count()
        if task_count == 0:
            category = db.session.get(Category, category_id)
            if category:
                db.session.delete(category)
                db.session.commit()
                category_deleted = True
    else:
        flash('Task not found', 'error')

    # Send JSON response to the client
    return jsonify(status='success' if task else 'error', category_deleted=category_deleted)

@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.title = request.form.get('title')
    db.session.commit()
    return jsonify(status='success', task={'id': task_id, 'title': task.title})

@app.route('/update_task_order', methods=['POST'])
def update_task_order():
    # Get the new ordering from the request
    new_order = request.json['order']

    # Update the sort_order fields for the tasks
    for task_id, sort_order in new_order.items():
        task = db.session.get(Task, task_id) # Using Session.get() instead of Query.get()
        task.sort_order = sort_order
        db.session.commit()

    return jsonify(status='success')

@app.route('/reset-checkmarks', methods=['POST'])
def reset_checkmarks():
    try:
        tasks = Task.query.all()
        for task in tasks:
            task.completed = False
        db.session.commit()
        return jsonify(success=True, message="All checkmarks have been reset.")
    except Exception as e:
        return jsonify(success=False, message=str(e))
    


## CATEGORIES ##

@app.route('/categories')
def get_categories():
    categories = Category.query.with_entities(Category.name).all()
    return jsonify([category.name for category in categories])

@app.route('/toggle_category/<int:category_id>', methods=['POST'])
def toggle_category(category_id):
    category = Category.query.get(category_id)
    category.is_visible = not category.is_visible
    db.session.commit()
    return jsonify(success=True)

@app.route('/edit_category/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.name = request.form.get('name')
    db.session.commit()
    return redirect('/manage_categories')

@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    # Check if there are any tasks associated with this category
    task_count = Task.query.filter_by(category_id=category.id).count()
    if task_count > 0:
        flash('Cannot delete category with active tasks!', 'error')
        return redirect('/manage_categories')

    db.session.delete(category)
    db.session.commit()

    flash('Category deleted successfully', 'success')
    return redirect('/manage_categories')

@app.route('/update_category_order', methods=['POST'])
def update_category_order():
    # Get the new ordering from the request
    new_order = request.json['order']

    # Update the sort_order fields for the categories
    for category_id, sort_order in new_order.items():
        category = db.session.get(Category, category_id)
        category.sort_order = sort_order
        db.session.commit()

    return jsonify(status='success')

@app.route('/env')
def show_env():
    return dict(os.environ)




## SETTINGS AND MISC ##

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/settings')
def settings():
    # get all tasks in the database
    tasks = db.session.query(Task).all()

    # get the server timezone
    server_timezone = time_module.tzname[0]

    # get all categories in the database
    categories = Category.query \
                .outerjoin(Task) \
                .with_entities(Category, func.count(Task.id).label('tasks_count'), Category.sort_order) \
                .group_by(Category.id) \
                .order_by(Category.sort_order) \
                .all()
    return render_template('settings.html', categories=categories, tasks=tasks, server_timezone=server_timezone)

@app.route('/backup', methods=['GET'])
def backup():
    # find the path to sqlite database
    BASE_DIR = '/adhdo_app/data/'  # Define this at the top of your script or as a configuration option.
    actual_db_path = os.path.join(BASE_DIR, 'adhdo.db')

    # Get the current date and time, and format it
    current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Define a backup file name with the current date and time appended
    backup_file = f"backup_{current_datetime}.db"

    # Create a backup
    source = sqlite3.connect(actual_db_path)
    backup = sqlite3.connect(backup_file)
    with backup:
        source.backup(backup)

    g.backup_file_to_remove = backup_file
    print(f"sent: {backup_file}")
    return send_file(backup_file, as_attachment=True, download_name=backup_file)

@app.after_request  # delete backup file after download
def cleanup(response):
    backup_file = getattr(g, 'backup_file_to_remove', None)
    if backup_file:
        try:
            print(f"deleted backup file from {backup_file}")
            os.remove(backup_file)
        except Exception as e:
            print(f"Error deleting backup file: {e}")
    return response

@app.route('/restore', methods=['POST'])
def restore():
    # find the path to sqlite database
    BASE_DIR = '/adhdo_app/data/'  # Define this at the top of your script or as a configuration option.
    actual_db_path = os.path.join(BASE_DIR, 'adhdo.db')

    # Check if a file was posted
    if 'dbfile' not in request.files:
        raise BadRequest("No file part")

    file = request.files['dbfile']

    # If the user does not select a file, the browser can submit an empty file without a filename.
    if file.filename == '':
        raise BadRequest("No selected file")

    # Check for proper file extension
    if not file.filename.endswith('.db'):
        raise BadRequest("Invalid file type. Please upload a .db file.")

    # Save the uploaded file/update-last-reset
    filename = secure_filename(file.filename)
    backup_path = os.path.join("/tmp", filename)  # save to temporary location
    file.save(backup_path)

    try:
        # Restore the backup
        current_db = sqlite3.connect(actual_db_path)
        backup_db = sqlite3.connect(backup_path)
        with current_db:
            backup_db.backup(current_db)
    
        flash('Database restored from ' + filename, 'success')
    except Exception as e:
        # Handle any error that arises during file operations
        flash(f"An error occurred while restoring the database: {e}", 'danger')

    return redirect('/settings')

@app.route('/get-settings', methods=['GET'])
def get_settings():
    settings = Settings.query.first()
    
    if not settings:
        return jsonify({'error': 'No settings found'}), 404

    return jsonify({
        'lastReset': settings.lastReset.strftime('%Y-%m-%dT%H:%M:%S'),  # Convert to string format
        'resetTime': {
            'hour': settings.resetTime.hour,
            'minute': settings.resetTime.minute
            
        }
    })

@app.route('/update-last-reset', methods=['POST'])
def update_last_opened():
    settings = Settings.query.first()
    
    if not settings:
        # Create a new entry if not found
        settings = Settings()
        db.session.add(settings)
    
    # Update the lastReset field with current time
    settings.lastReset = datetime.now()
    
    # Save changes
    db.session.commit()

    return jsonify({'message': 'lastReset updated successfully'}), 200


@app.route('/update-reset-time', methods=['POST'])
def update_reset_time():
    data = request.get_json()
    resetTime = data.get("resetTime")

    hours, minutes = map(int, resetTime.split(":"))
    resetTimeObj = time(hour=hours, minute=minutes)

    # Store the resetTimeObj in the database
    settings = Settings.query.first()
    settings.resetTime = resetTimeObj
    db.session.commit()

    return jsonify(status='success')