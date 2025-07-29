#!/usr/bin/env python3
"""
Main Flask application for Tech Ethics Club Website
Cloud Storage Version - Uses Google Cloud Storage for data persistence
"""

from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime
from cloud_storage import cloud_storage
from cloud_user import CloudUser

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return CloudUser.get(user_id)

@app.after_request
def add_header(response):
    """Add headers to prevent caching issues."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = '0'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    """Gallery page."""
    gallery_items_data = cloud_storage.get_all_gallery_items()
    gallery_items = [GalleryItem(item) for item in gallery_items_data]
    return render_template('gallery.html', gallery_items=gallery_items)

@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')

@app.route('/team')
def team():
    """Team page."""
    return render_template('team.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = cloud_storage.authenticate_user(email, password)
        if user_data:
            user = CloudUser(user_data)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Check if this email should be an admin
            is_admin = is_admin_email(email)
            cloud_storage.create_user(email=email, password=password, is_admin=is_admin)
            
            if is_admin:
                flash('Registration successful! You have admin privileges. Please log in.', 'success')
            else:
                flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/gallery/add', methods=['GET', 'POST'])
@login_required
def add_gallery_item():
    """Add gallery item."""
    # Check if user is admin
    if not current_user.is_admin:
        flash('You do not have permission to add gallery items.', 'error')
        return redirect(url_for('gallery'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        creator_name = request.form.get('creator_name')
        description = request.form.get('description')
        project_link = request.form.get('project_link')
        image_file = request.files.get('image')
        
        if not title or not creator_name or not description or not image_file:
            flash('Title, creator name, description, and image are required.', 'error')
            return render_template('admin/add_gallery_item.html')
        
        try:
            # Upload image to cloud storage
            image_url = cloud_storage.upload_file(image_file, image_file.filename, 'uploads')
            if not image_url:
                flash('Error uploading image. Please try again.', 'error')
                return render_template('admin/add_gallery_item.html')
            
            # Create gallery item
            cloud_storage.create_gallery_item(
                title=title,
                description=description,
                image_filename=image_file.filename,
                image_url=image_url,
                creator_name=creator_name,
                project_link=project_link,
                created_by=current_user.id
            )
            
            flash('Gallery item added successfully!', 'success')
            return redirect(url_for('gallery'))
            
        except Exception as e:
            flash(f'Error adding gallery item: {str(e)}', 'error')
            return render_template('admin/add_gallery_item.html')
    
    return render_template('admin/add_gallery_item.html')

@app.route('/admin/gallery/delete/<item_id>', methods=['POST'])
@login_required
def delete_gallery_item(item_id):
    """Delete gallery item."""
    # Check if user is admin
    if not current_user.is_admin:
        flash('You do not have permission to delete gallery items.', 'error')
        return redirect(url_for('gallery'))
    
    try:
        # Get the item to delete the image file
        item = cloud_storage.get_gallery_item_by_id(item_id)
        if not item:
            flash('Gallery item not found.', 'error')
            return redirect(url_for('gallery'))
        
        # Delete the gallery item (this will also delete the JSON file)
        success = cloud_storage.delete_gallery_item(item_id)
        
        if success:
            flash('Gallery item deleted successfully!', 'success')
        else:
            flash('Failed to delete gallery item.', 'error')
            
    except Exception as e:
        flash(f'Error deleting gallery item: {str(e)}', 'error')
    
    return redirect(url_for('gallery'))

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission."""
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    if not name or not email or not message:
        flash('All fields are required.', 'error')
        return redirect(url_for('contact'))
    
    # Here you could save the contact message to cloud storage
    # For now, just flash a success message
    flash('Thank you for your message! We will get back to you soon.', 'success')
    return redirect(url_for('contact'))

# GalleryItem class for template compatibility
class GalleryItem:
    def __init__(self, item_data):
        self.id = item_data.get('id')
        self.title = item_data.get('title')
        self.description = item_data.get('description')
        self.image_filename = item_data.get('image_filename')
        self.image_url = item_data.get('image_url')
        self.creator_name = item_data.get('creator_name')
        self.project_link = item_data.get('project_link')
        self.created_by = item_data.get('created_by')
        self.created_at = item_data.get('created_at')

# Admin email list
ADMIN_EMAILS = [
    'chrisho2009@gmail.com',
    'amazingadityab@gmail.com',
    'vaishnavanand90@gmail.com'
]

def is_admin_email(email):
    """Check if an email is in the admin list."""
    return email in ADMIN_EMAILS

if __name__ == '__main__':
    app.run(debug=True, port=5000) 