"""
Tech & Ethics Club — main Flask application.

Sections worth knowing:
  • Gallery / projects: routes under /gallery, admin upload at /admin/gallery/add,
    data in Google Cloud Storage via cloud_storage (see cloud_storage.py).
  • GalleryItem (below): view-model dict → attributes for templates.
  • PDF: GalleryPDFGenerator for single-item and full-gallery exports.
  • Video thumbnails: VideoThumbnailExtractor when saving gallery items with video URLs.
  • Blog: separate blog_storage module; routes under /blog.
  • CIS news: cis_news_storage (GCS cis_news.json); any logged-in user may post;
    delete own posts or any if admin / CIS_NEWS_EDITOR_EMAILS.

Config: SECRET_KEY, STORAGE_BUCKET, optional GAE_ENV. Local GCS often uses
tech-ethics-club-sa-key.json (see CloudStorageManager).
"""

from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cloud_storage import cloud_storage
from cloud_user import CloudUser
from image_optimizer import ImageOptimizer
from blog_storage import blog_storage
from cis_news_storage import cis_news_storage
from video_thumbnail_extractor import VideoThumbnailExtractor
from pdf_generator import GalleryPDFGenerator


app = Flask(__name__)


print("🚀 Blog storage initialized")

CIS_NEWS_EDITOR_EMAILS = frozenset(
    {
        "vaishnavanand90@gmail.com",
        "asherburdeny@gmail.com",
       
        "chrisho2009@gmail.com",
    }
)


def user_can_manage_cis_news():
    """Moderators: admins or named editors (can delete any CIS news item)."""
    return current_user.is_authenticated and (
        current_user.is_admin or current_user.email in CIS_NEWS_EDITOR_EMAILS
    )


def user_can_delete_cis_news_item(item):
    if not current_user.is_authenticated or not item:
        return False
    if user_can_manage_cis_news():
        return True
    author = (item.get("created_by_email") or "").strip().lower()
    return author and author == (current_user.email or "").strip().lower()


ADMIN_EMAILS = [
    'chrisho2009@gmail.com',
    'amazingadityab@gmail.com',
    'vaishnavanand90@gmail.com',
    'asherburdeny@gmail.com'
]


def is_admin_email(email):
    cleaned = (email or '').strip().lower()
    if not cleaned:
        return False
    if cleaned in ADMIN_EMAILS:
        return True
    return cloud_storage.is_email_admin_eligible(cleaned)




app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15MB, matches client-side validation
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_PATH'] = None


image_optimizer = ImageOptimizer()


video_thumbnail_extractor = VideoThumbnailExtractor()


pdf_generator = GalleryPDFGenerator()


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return CloudUser.get(user_id)

@app.after_request
def add_header(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    else:
        response.headers['Cache-Control'] = 'no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    response = send_from_directory('static', filename)
    if filename.endswith('.css'):
        response.headers['Cache-Control'] = 'no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/favicon.ico')
def favicon():
    """Serve a persistent tab icon for all pages."""
    return send_from_directory('static/imgs', 'headshot_athenian_optimized.jpg')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    """List all gallery items; optional ?course=<id> filters to one course."""
    course_filter = request.args.get('course', '').strip()

    if not cloud_storage._storage_available:
        flash('Storage is currently unavailable. Gallery items cannot be loaded.', 'error')

    try:
        gallery_items_data = cloud_storage.get_all_gallery_items()
    except Exception as e:
        logging.error(f"Failed to load gallery items: {e}")
        flash('Could not load gallery items. Please try again later.', 'error')
        gallery_items_data = []

    if course_filter:
        gallery_items_data = [item for item in gallery_items_data if item.get('course_id') == course_filter]

    gallery_items = [GalleryItem(item) for item in gallery_items_data]

    try:
        courses = cloud_storage.get_all_courses()
    except Exception as e:
        logging.error(f"Failed to load courses: {e}")
        courses = []

    return render_template('gallery.html', gallery_items=gallery_items, courses=courses, selected_course=course_filter)

@app.route('/gallery/<item_id>')
def gallery_item(item_id):
    """Single project/course item page (templates/gallery_item.html)."""
    try:
        item_data = cloud_storage.get_gallery_item_by_id(item_id)
        if not item_data:
            flash('Gallery item not found.', 'error')
            return redirect(url_for('gallery'))
        
        gallery_item = GalleryItem(item_data)
        
        print(f"Gallery item {item_id} image URL: {gallery_item.image_url}")
        print(f"Gallery item {item_id} additional images: {gallery_item.additional_images}")
        print(f"Gallery item {item_id} additional images type: {type(gallery_item.additional_images)}")
        print(f"Gallery item {item_id} additional images count: {len(gallery_item.additional_images) if isinstance(gallery_item.additional_images, (list, tuple)) else 'NOT_A_LIST'}")
        if isinstance(gallery_item.additional_images, (list, tuple)) and len(gallery_item.additional_images) > 0:
            for idx, img_url in enumerate(gallery_item.additional_images):
                print(f"  Additional image {idx+1}: {img_url}")
        print(f"Gallery item {item_id} main image_link: {gallery_item.image_link}")
        print(f"Gallery item {item_id} additional_image_links: {gallery_item.additional_image_links}")
        print(f"Gallery item {item_id} additional_image_links type: {type(gallery_item.additional_image_links)}")
        print(f"Gallery item {item_id} additional_image_links count: {len(gallery_item.additional_image_links) if isinstance(gallery_item.additional_image_links, (list, tuple)) else 'NOT_A_LIST'}")
        print(f"Gallery item {item_id} additional filenames: {gallery_item.additional_filenames}")
        print(f"Gallery item {item_id} has_images: {gallery_item.has_images}")
        print(f"Gallery item {item_id} has_videos: {gallery_item.has_videos}")
        print(f"Gallery item {item_id} additional filenames count: {len(gallery_item.additional_filenames) if isinstance(gallery_item.additional_filenames, (list, tuple)) else 'NOT_A_LIST'}")
        print(f"Gallery item {item_id} raw data additional_images: {item_data.get('additional_images', 'NOT_FOUND')}")
        print(f"Gallery item {item_id} raw data additional_images type: {type(item_data.get('additional_images', []))}")
        print(f"Gallery item {item_id} raw data additional_images count: {len(item_data.get('additional_images', [])) if isinstance(item_data.get('additional_images', []), (list, tuple)) else 'NOT_A_LIST'}")
        
        return render_template('gallery_item.html', item=gallery_item)
    except Exception as e:
        flash(f'Error loading gallery item: {str(e)}', 'error')
        return redirect(url_for('gallery'))



@app.route('/admin/courses/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if not current_user.is_admin:
        flash('You do not have permission to add courses.', 'error')
        return redirect(url_for('gallery'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        instructor = request.form.get('instructor', '').strip()
        course_code = request.form.get('course_code', '').strip()
        semester = request.form.get('semester', '').strip()
        
        if not title or not description:
            flash('Title and description are required.', 'error')
            return render_template('admin/add_course.html')
        
        try:
            course = cloud_storage.create_course(
                title=title,
                description=description,
                instructor=instructor,
                course_code=course_code,
                semester=semester,
                created_by=current_user.id
            )
            
            flash('Course added successfully!', 'success')
            return redirect(url_for('gallery'))
            
        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
            return render_template('admin/add_course.html')
    
    return render_template('admin/add_course.html')

@app.route('/admin/courses/delete/<course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete courses.', 'error')
        return redirect(url_for('gallery'))
    
    try:
        success = cloud_storage.delete_course(course_id)
        if success:
            flash('Course deleted successfully!', 'success')
        else:
            flash('Error deleting course.', 'error')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    
    return redirect(url_for('gallery'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = cloud_storage.authenticate_user(email, password)
        if user_data:
            # Keep legacy/admin-eligible emails in sync with stored user flag.
            email_normalized = (email or '').strip().lower()
            if not user_data.get('is_admin', False) and is_admin_email(email_normalized):
                cloud_storage.set_user_admin_status(email_normalized, True)
                user_data['is_admin'] = True
            user = CloudUser(user_data)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        try:
            is_admin = is_admin_email(email)
            
            existing_user = cloud_storage.get_user_by_email(email)
            if existing_user:
                flash('An account with this email already exists. Please log in instead.', 'error')
                return redirect(url_for('login'))
            
            cloud_storage.create_user(email=email, password=password, is_admin=is_admin)
            
            if is_admin:
                flash('Registration successful! You have admin privileges. Please log in.', 'success')
            else:
                flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('register.html')


@app.route('/admin/manage-admins', methods=['GET', 'POST'])
@login_required
def manage_admins():
    if not current_user.is_admin:
        flash('You do not have permission to manage admins.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('manage_admins'))

        if cloud_storage.add_admin_email(email):
            # If user already exists, promote immediately.
            cloud_storage.set_user_admin_status(email, True)
            flash(f'{email} can now register/login as an admin.', 'success')
        else:
            flash('Could not save admin email. Please try again.', 'error')
        return redirect(url_for('manage_admins'))

    configured_admins = sorted(list(set(ADMIN_EMAILS + cloud_storage.get_admin_emails())))
    return render_template('admin/manage_admins.html', admin_emails=configured_admins)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/gallery/add', methods=['GET', 'POST'])
@login_required
def add_gallery_item():
    """Admin: create gallery item (images, videos, slideshow, poster, course link)."""
    if not current_user.is_admin:
        flash('You do not have permission to add gallery items.', 'error')
        return redirect(url_for('gallery'))
    
    if request.method == 'POST':
        print("Form submitted - processing POST request")
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Get multiple project links with titles
        project_link_titles = request.form.getlist('project_link_titles[]')
        project_link_urls = request.form.getlist('project_link_urls[]')
        project_links = []
        for i in range(len(project_link_titles)):
            if project_link_titles[i].strip() and project_link_urls[i].strip():
                project_links.append({
                    'title': project_link_titles[i].strip(),
                    'url': project_link_urls[i].strip()
                })
        
        # Backward compatibility: check for old single project_link field
        old_project_link = request.form.get('project_link', '').strip()
        if old_project_link and not project_links:
            project_links = [{'title': 'View Project', 'url': old_project_link}]
        
        tags = request.form.get('tags', '').strip()
        
        course_id = request.form.get('course_id', '').strip()
        if not course_id:
            course_id = None
        
        creator_names = request.form.getlist('creator_names[]')
        creator_emails = request.form.getlist('creator_emails[]')
        creator_linkedins = request.form.getlist('creator_linkedins[]')
        
        creators_list = []
        for i in range(len(creator_names)):
            if creator_names[i].strip():
                creators_list.append({
                    'name': creator_names[i].strip(),
                    'email': creator_emails[i].strip() if i < len(creator_emails) else '',
                    'linkedin': creator_linkedins[i].strip() if i < len(creator_linkedins) else ''
                })
        
        creator_name = creators_list[0]['name'] if creators_list else ''
        
        video_urls = request.form.getlist('video_urls[]')
        video_titles = request.form.getlist('video_titles[]')
        video_thumbnail_files = request.files.getlist('video_thumbnails[]')
        
        project_poster_file = request.files.get('project_poster')
        project_poster_link = request.form.get('project_poster_link', '').strip()
        thumbnail_file = request.files.get('thumbnail_image')
        thumbnail_image_link = request.form.get('thumbnail_image_link', '').strip()
        # Try with brackets first (matches form), fallback to without brackets
        additional_files = request.files.getlist('additional_images[]')
        if not additional_files or len(additional_files) == 0:
            additional_files = request.files.getlist('additional_images')
        additional_image_links = request.form.getlist('additional_image_links[]')
        
        # Get slideshow images
        slideshow_files = request.files.getlist('slideshow_images[]')
        slideshow_image_links = request.form.getlist('slideshow_image_links[]')
        slideshow_title = request.form.get('slideshow_title', '').strip()
        
        print(f"Form data received:")
        print(f"  Title: '{title}'")
        print(f"  Creator: '{creator_name}'")
        print(f"  Description: '{description}'")
        print(f"  Video URLs: {video_urls}")
        print(f"  Video titles: {video_titles}")
        print(f"  Thumbnail file: {thumbnail_file.filename if thumbnail_file else 'None'}")
        print(f"  Additional files (with []): {len(request.files.getlist('additional_images[]'))} files")
        print(f"  Additional files (without []): {len(request.files.getlist('additional_images'))} files")
        print(f"  Additional files (final): {len(additional_files)} files")
        for i, f in enumerate(additional_files):
            print(f"    File {i+1}: {f.filename if f and f.filename else 'None/EMPTY'}")
            if f and f.filename:
                print(f"      Content length: {f.content_length}")
                print(f"      Content type: {f.content_type}")
            else:
                print(f"      File object exists: {f is not None}, but no filename")
        
        has_images = bool(thumbnail_file and thumbnail_file.filename)
        has_videos = any(url.strip() for url in video_urls)
        
        print(f"Validation checks:")
        print(f"  has_images: {has_images}")
        print(f"  has_videos: {has_videos}")
        print(f"  title empty: {not title}")
        print(f"  creator_name empty: {not creator_name}")
        print(f"  description empty: {not description}")
        
        if not title or not creator_name or not description:
            print("VALIDATION FAILED: Missing required fields")
            flash('Title, creator name, and description are required.', 'error')
            return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
        
        if not has_images and not has_videos:
            print("VALIDATION FAILED: No media provided")
            flash('At least one image or video is required for the project.', 'error')
            return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
        
        max_file_size = 15 * 1024 * 1024
        
        if project_poster_file and project_poster_file.content_length and project_poster_file.content_length > max_file_size:
            flash('Project poster is too large. Maximum file size is 15MB.', 'error')
            return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
        
        if thumbnail_file and thumbnail_file.content_length and thumbnail_file.content_length > max_file_size:
            flash('Thumbnail image is too large. Maximum file size is 15MB.', 'error')
            return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
        
        for additional_file in additional_files:
            if additional_file and additional_file.filename and additional_file.content_length and additional_file.content_length > max_file_size:
                flash(f'File "{additional_file.filename}" is too large. Maximum file size is 15MB.', 'error')
                return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
        
        # Validate slideshow image file sizes
        for slideshow_file in slideshow_files:
            if slideshow_file and slideshow_file.filename and slideshow_file.content_length and slideshow_file.content_length > max_file_size:
                flash(f'Slideshow image "{slideshow_file.filename}" is too large. Maximum file size is 15MB.', 'error')
                return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
        
        try:
            print("Starting file upload process...")
            
            # Process project poster first
            project_poster_url = None
            project_poster_link_value = None
            project_poster_filename = None
            if project_poster_file and project_poster_file.filename:
                print(f"Processing project poster: {project_poster_file.filename}")
                try:
                    optimized_poster = image_optimizer.optimize_image(project_poster_file, project_poster_file.filename)
                    project_poster_filename = image_optimizer.get_optimized_filename(project_poster_file.filename)
                    
                    print(f"Uploading project poster: {project_poster_filename}")
                    project_poster_url = cloud_storage.upload_file(optimized_poster, project_poster_filename, 'uploads')
                    if project_poster_url:
                        project_poster_link_value = project_poster_link if project_poster_link else None
                        print(f"Project poster uploaded successfully: {project_poster_url}")
                        if project_poster_link_value:
                            print(f"Project poster link: {project_poster_link_value}")
                    else:
                        print("Failed to upload project poster")
                        flash('Warning: Failed to upload project poster. Continuing with other files.', 'warning')
                except Exception as poster_error:
                    print(f"Error uploading project poster: {str(poster_error)}")
                    flash(f'Warning: Error uploading project poster: {str(poster_error)}. Continuing with other files.', 'warning')
            
            thumbnail_url = None
            thumbnail_image_link_value = None
            optimized_filename = None
            if has_images:
                if not thumbnail_file or not thumbnail_file.filename:
                    print("Thumbnail file is missing or has no filename")
                    flash('Thumbnail file is missing. Please try again.', 'error')
                    return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
                
                print(f"Optimizing thumbnail: {thumbnail_file.filename}")
                optimized_thumbnail = image_optimizer.optimize_image(thumbnail_file, thumbnail_file.filename)
                optimized_filename = image_optimizer.get_optimized_filename(thumbnail_file.filename)
                
                print(f"Uploading optimized thumbnail: {optimized_filename}")
                thumbnail_url = cloud_storage.upload_file(optimized_thumbnail, optimized_filename, 'uploads')
                if not thumbnail_url:
                    print("Failed to upload thumbnail image")
                    error_msg = 'Error uploading thumbnail image. '
                    if cloud_storage.auth_error:
                        error_msg += 'This might be due to authentication issues. Please contact the administrator.'
                    else:
                        error_msg += 'Please try again.'
                    flash(error_msg, 'error')
                    return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
                print(f"Thumbnail uploaded successfully: {thumbnail_url}")
                thumbnail_image_link_value = thumbnail_image_link if thumbnail_image_link else None
                if thumbnail_image_link_value:
                    print(f"Thumbnail image link: {thumbnail_image_link_value}")
            
            videos_list = []
            if has_videos:
                print(f"Processing {len(video_urls)} videos")
                for i, video_url in enumerate(video_urls):
                    if video_url.strip():
                        video_title = video_titles[i].strip() if i < len(video_titles) and video_titles[i].strip() else f"Video {i+1}"
                        
                        video_thumbnail_url = None
                        if i < len(video_thumbnail_files) and video_thumbnail_files[i] and video_thumbnail_files[i].filename:
                            try:
                                print(f"Processing custom video thumbnail for video {i+1}")
                                optimized_video_thumbnail = image_optimizer.optimize_image(video_thumbnail_files[i], video_thumbnail_files[i].filename)
                                optimized_video_thumbnail_filename = image_optimizer.get_optimized_filename(video_thumbnail_files[i].filename)
                                
                                video_thumbnail_url = cloud_storage.upload_file(optimized_video_thumbnail, optimized_video_thumbnail_filename, 'uploads')
                                print(f"Custom video thumbnail uploaded: {video_thumbnail_url}")
                            except Exception as e:
                                print(f"Error uploading custom video thumbnail: {e}")
                        else:
                            try:
                                print(f"Auto-generating thumbnail for video {i+1}: {video_url}")
                                thumbnail_data = video_thumbnail_extractor.extract_thumbnail_from_url(video_url)
                                if thumbnail_data:
                                    optimized_thumbnail = image_optimizer.optimize_image(thumbnail_data, f"video_{i+1}_thumbnail.jpg")
                                    thumbnail_filename = f"auto_video_{i+1}_thumbnail.jpg"
                                    
                                    video_thumbnail_url = cloud_storage.upload_file(optimized_thumbnail, thumbnail_filename, 'uploads')
                                    print(f"Auto-generated video thumbnail uploaded: {video_thumbnail_url}")
                                else:
                                    print(f"Could not generate thumbnail for video {i+1}")
                            except Exception as e:
                                print(f"Error auto-generating video thumbnail: {e}")
                        
                        videos_list.append({
                            'url': video_url.strip(),
                            'title': video_title,
                            'thumbnail_url': video_thumbnail_url
                        })
                        print(f"Added video {i+1}: {video_title} - {video_url}")
            
            additional_urls = []
            additional_filenames = []
            additional_image_links_list = []
            # Filter out empty file inputs - Flask includes empty file objects for unselected files
            valid_additional_files = []
            valid_file_indices = []
            for i, additional_file in enumerate(additional_files):
                if additional_file and hasattr(additional_file, 'filename') and additional_file.filename and additional_file.filename.strip():
                    valid_additional_files.append(additional_file)
                    valid_file_indices.append(i)
                    print(f"Valid additional file {len(valid_additional_files)} (form index {i}): {additional_file.filename}")
                else:
                    print(f"Skipping empty file input at index {i}")
            
            print(f"Processing {len(valid_additional_files)} valid additional files (out of {len(additional_files)} total file inputs)")
            
            for file_idx, additional_file in enumerate(valid_additional_files[:4]):
                original_index = valid_file_indices[file_idx]
                print(f"Processing additional file {file_idx + 1} (form index {original_index}): {additional_file.filename}")
                try:
                    optimized_additional = image_optimizer.optimize_image(additional_file, additional_file.filename)
                    optimized_additional_filename = image_optimizer.get_optimized_filename(additional_file.filename)
                    
                    print(f"Uploading optimized additional file: {optimized_additional_filename}")
                    additional_url = cloud_storage.upload_file(optimized_additional, optimized_additional_filename, 'uploads')
                    if additional_url:
                        additional_urls.append(additional_url)
                        additional_filenames.append(optimized_additional_filename)
                        
                        # Get corresponding image link if provided (use original_index to match with form array)
                        image_link = None
                        if original_index < len(additional_image_links):
                            link_value = additional_image_links[original_index]
                            if link_value and link_value.strip():
                                image_link = link_value.strip()
                        additional_image_links_list.append(image_link)
                        if image_link:
                            print(f"Additional image {file_idx + 1} link: {image_link}")
                        
                        print(f"Successfully uploaded: {additional_url}")
                    else:
                        print(f"Failed to upload: {additional_file.filename}")
                        warning_msg = f'Warning: Failed to upload additional image "{additional_file.filename}". '
                        if cloud_storage.auth_error:
                            warning_msg += 'This might be due to authentication issues.'
                        else:
                            warning_msg += 'Continuing with other files.'
                        flash(warning_msg, 'warning')
                except Exception as upload_error:
                    print(f"Error uploading {additional_file.filename}: {str(upload_error)}")
                    import traceback
                    traceback.print_exc()
                    flash(f'Warning: Error uploading "{additional_file.filename}": {str(upload_error)}. Continuing with other files.', 'warning')
            
            print(f"Final additional URLs: {additional_urls}")
            print(f"Final additional URLs count: {len(additional_urls)}")
            print(f"Final additional filenames: {additional_filenames}")
            print(f"Final additional filenames count: {len(additional_filenames)}")
            print(f"Final additional image links: {additional_image_links_list}")
            print(f"Final additional image links count: {len(additional_image_links_list)}")
            
            # Verify all images were processed
            if len(additional_urls) != len(additional_files):
                print(f"WARNING: Mismatch! Processed {len(additional_urls)} URLs from {len(additional_files)} files")
                for idx, f in enumerate(additional_files):
                    print(f"  File {idx+1}: {f.filename if f and f.filename else 'EMPTY/NONE'}")
            
            # Process slideshow images
            slideshow_urls = []
            slideshow_filenames = []
            slideshow_image_links_list = []
            valid_slideshow_files = []
            valid_slideshow_file_indices = []
            for i, slideshow_file in enumerate(slideshow_files):
                if slideshow_file and hasattr(slideshow_file, 'filename') and slideshow_file.filename and slideshow_file.filename.strip():
                    valid_slideshow_files.append(slideshow_file)
                    valid_slideshow_file_indices.append(i)
                    print(f"Valid slideshow file {len(valid_slideshow_files)} (form index {i}): {slideshow_file.filename}")
            
            print(f"Processing {len(valid_slideshow_files)} valid slideshow files (out of {len(slideshow_files)} total file inputs)")
            
            for file_idx, slideshow_file in enumerate(valid_slideshow_files):
                original_index = valid_slideshow_file_indices[file_idx]
                print(f"Processing slideshow file {file_idx + 1} (form index {original_index}): {slideshow_file.filename}")
                try:
                    optimized_slideshow = image_optimizer.optimize_image(slideshow_file, slideshow_file.filename)
                    optimized_slideshow_filename = image_optimizer.get_optimized_filename(slideshow_file.filename)
                    
                    print(f"Uploading optimized slideshow file: {optimized_slideshow_filename}")
                    slideshow_url = cloud_storage.upload_file(optimized_slideshow, optimized_slideshow_filename, 'uploads')
                    if slideshow_url:
                        slideshow_urls.append(slideshow_url)
                        slideshow_filenames.append(optimized_slideshow_filename)
                        
                        # Get corresponding image link if provided
                        image_link = None
                        if original_index < len(slideshow_image_links):
                            link_value = slideshow_image_links[original_index]
                            if link_value and link_value.strip():
                                image_link = link_value.strip()
                        slideshow_image_links_list.append(image_link)
                        if image_link:
                            print(f"Slideshow image {file_idx + 1} link: {image_link}")
                        
                        print(f"Successfully uploaded slideshow image: {slideshow_url}")
                    else:
                        print(f"Failed to upload slideshow image: {slideshow_file.filename}")
                        warning_msg = f'Warning: Failed to upload slideshow image "{slideshow_file.filename}". '
                        if cloud_storage.auth_error:
                            warning_msg += 'This might be due to authentication issues.'
                        else:
                            warning_msg += 'Continuing with other files.'
                        flash(warning_msg, 'warning')
                except Exception as upload_error:
                    print(f"Error uploading slideshow image {slideshow_file.filename}: {str(upload_error)}")
                    import traceback
                    traceback.print_exc()
                    flash(f'Warning: Error uploading slideshow image "{slideshow_file.filename}": {str(upload_error)}. Continuing with other files.', 'warning')
            
            print(f"Final slideshow URLs: {slideshow_urls}")
            print(f"Final slideshow URLs count: {len(slideshow_urls)}")
            
            # Only allow tags if not assigned to a course
            tag_list = []
            if tags and not course_id:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            elif course_id and tags:
                # Clear tags if course is assigned
                tag_list = []
                print("Tags cleared because project is assigned to a course")
            
            print("Creating gallery item in cloud storage...")
            gallery_item = cloud_storage.create_gallery_item(
            title=title,
            description=description,
            image_filename=optimized_filename,
            image_url=thumbnail_url,
            image_link=thumbnail_image_link_value,  # Link for main image
            project_poster_url=project_poster_url,  # Project poster image URL
            project_poster_link=project_poster_link_value,  # Project poster link
            project_poster_filename=project_poster_filename,  # Project poster filename
            additional_images=additional_urls,
            additional_filenames=additional_filenames,
            additional_image_links=additional_image_links_list,  # Links for additional images
            slideshow_images=slideshow_urls,  # Slideshow images URLs
            slideshow_filenames=slideshow_filenames,  # Slideshow image filenames
            slideshow_image_links=slideshow_image_links_list,  # Links for slideshow images
            slideshow_title=slideshow_title if slideshow_title else None,  # Slideshow title
            creators=creators_list,
            project_link=None,  # Keep for backward compatibility but use project_links
            project_links=project_links,
            tags=tag_list,  # Empty if course_id is set
            videos=videos_list,
            course_id=course_id,
            created_by=current_user.id
        )
            
            print(f"Gallery item created successfully with ID: {gallery_item.get('id')}")
            flash('Gallery item added successfully!', 'success')
            return redirect(url_for('gallery'))
            
        except Exception as e:
            print(f"Error during gallery item creation: {str(e)}")
            import traceback
            traceback.print_exc()
            
            error_msg = f'Error adding gallery item: {str(e)}'
            
            if os.environ.get('GAE_ENV'):
                if 'authentication' in str(e).lower() or 'credentials' in str(e).lower():
                    error_msg += '\n\nProduction authentication error. The service account may need additional permissions.'
                elif 'permission' in str(e).lower() or 'forbidden' in str(e).lower():
                    error_msg += '\n\nPermission denied. The service account may not have access to the storage bucket.'
                elif 'bucket' in str(e).lower() or 'not found' in str(e).lower():
                    error_msg += '\n\nStorage bucket not accessible. Please check the bucket configuration.'
                else:
                    error_msg += '\n\nProduction error occurred. Please contact the administrator.'
            else:
                if 'authentication' in str(e).lower() or 'credentials' in str(e).lower() or cloud_storage.auth_error:
                    error_msg += '\n\nThis appears to be an authentication issue. Please contact the administrator or check the setup instructions.'
            
            flash(error_msg, 'error')
            return render_template('admin/add_gallery_item.html', courses=cloud_storage.get_all_courses())
    
    courses = cloud_storage.get_all_courses()
    return render_template('admin/add_gallery_item.html', courses=courses)

@app.route('/admin/gallery/delete/<item_id>', methods=['POST'])
@login_required
def delete_gallery_item(item_id):
    """Admin POST: remove item and associated blobs from storage."""
    if not current_user.is_admin:
        flash('You do not have permission to delete gallery items.', 'error')
        return redirect(url_for('gallery'))
    
    try:
        item = cloud_storage.get_gallery_item_by_id(item_id)
        if not item:
            flash('Gallery item not found.', 'error')
            return redirect(url_for('gallery'))
        
        success = cloud_storage.delete_gallery_item(item_id)
        
        if success:
            flash('Gallery item deleted successfully!', 'success')
        else:
            flash('Failed to delete gallery item.', 'error')
            
    except Exception as e:
        flash(f'Error deleting gallery item: {str(e)}', 'error')
    
    return redirect(url_for('gallery'))

@app.route('/admin/gallery/move-to-course', methods=['POST'])
@login_required
def move_gallery_item_to_course():
    """Bulk-assign selected gallery items to a course (or uncategorized)."""
    if not current_user.is_admin:
        flash('You do not have permission to move gallery items.', 'error')
        return redirect(url_for('gallery'))
    
    try:
        item_ids = request.form.getlist('item_ids[]')
        course_id = request.form.get('course_id', '').strip()
        
        if not course_id:
            course_id = None
        
        if not item_ids:
            flash('No gallery items selected.', 'error')
            return redirect(url_for('gallery'))
        
        if len(item_ids) == 1:
            success = cloud_storage.move_gallery_item_to_course(item_ids[0], course_id)
            if success:
                if course_id:
                    course = cloud_storage.get_course_by_id(course_id)
                    course_name = course.get('title', 'Unknown Course') if course else 'Unknown Course'
                    flash(f'Gallery item moved to {course_name} successfully!', 'success')
                else:
                    flash('Gallery item moved to Other Projects successfully!', 'success')
            else:
                flash('Failed to move gallery item.', 'error')
        else:
            results = cloud_storage.move_multiple_gallery_items_to_course(item_ids, course_id)
            successful_moves = sum(1 for success in results.values() if success)
            total_items = len(item_ids)
            
            if successful_moves == total_items:
                if course_id:
                    course = cloud_storage.get_course_by_id(course_id)
                    course_name = course.get('title', 'Unknown Course') if course else 'Unknown Course'
                    flash(f'All {total_items} gallery items moved to {course_name} successfully!', 'success')
                else:
                    flash(f'All {total_items} gallery items moved to Other Projects successfully!', 'success')
            elif successful_moves > 0:
                if course_id:
                    course = cloud_storage.get_course_by_id(course_id)
                    course_name = course.get('title', 'Unknown Course') if course else 'Unknown Course'
                    flash(f'{successful_moves} of {total_items} gallery items moved to {course_name}. Some items failed to move.', 'warning')
                else:
                    flash(f'{successful_moves} of {total_items} gallery items moved to Other Projects. Some items failed to move.', 'warning')
            else:
                flash('Failed to move any gallery items.', 'error')
                
    except Exception as e:
        flash(f'Error moving gallery items: {str(e)}', 'error')
    
    return redirect(url_for('gallery'))

@app.route('/gallery/<item_id>/pdf')
def generate_gallery_item_pdf(item_id):
    """Download one project as PDF (reportlab via pdf_generator)."""
    try:
        item_data = cloud_storage.get_gallery_item_by_id(item_id)
        if not item_data:
            flash('Gallery item not found.', 'error')
            return redirect(url_for('gallery'))
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_path = temp_file.name
        
        success = pdf_generator.generate_gallery_item_pdf(item_data, temp_path)
        
        if success:
            from flask import send_file
            return send_file(temp_path, as_attachment=True, 
                           download_name=f"{item_data['title']}_project.pdf",
                           mimetype='application/pdf')
        else:
            flash('Error generating PDF.', 'error')
            return redirect(url_for('gallery_item', item_id=item_id))
            
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('gallery_item', item_id=item_id))

@app.route('/gallery/pdf')
def generate_gallery_pdf():
    """Download combined PDF of all gallery items."""
    try:
        gallery_items_data = cloud_storage.get_all_gallery_items()
        gallery_items = [GalleryItem(item) for item in gallery_items_data]
        
        if not gallery_items:
            flash('No gallery items found.', 'error')
            return redirect(url_for('gallery'))
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_path = temp_file.name
        
        items_data = []
        for item in gallery_items:
            items_data.append({
                'title': item.title,
                'description': item.description,
                'image_url': item.image_url,
                'additional_images': item.additional_images,
                'videos': item.videos,
                'creators': item.creators,
                'tags': item.tags,
                'project_link': item.project_link,  # Backward compatibility
                'project_links': item.project_links  # New: multiple project links
            })
        
        success = pdf_generator.generate_gallery_pdf(items_data, temp_path)
        
        if success:
            from flask import send_file
            return send_file(temp_path, as_attachment=True, 
                           download_name="Tech_Ethics_Club_Gallery.pdf",
                           mimetype='application/pdf')
        else:
            flash('Error generating PDF.', 'error')
            return redirect(url_for('gallery'))
            
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('gallery'))

@app.route('/check-permissions')
@login_required
def check_permissions():
    user_data = cloud_storage.get_user_by_email(current_user.email)
    db_is_admin = user_data.get('is_admin', False) if user_data else False
    
    gallery_authorized = current_user.email in [
        'vaishnavanand90@gmail.com',
        'chrisho2009@gmail.com',
        'amazingadityab@gmail.com',
        'asherburdeny@gmail.com'
    ]
    
    permissions_info = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Permission Check</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
            .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .good {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
            .bad {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
            .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }}
            h2 {{ color: #333; }}
            .logout-btn {{ 
                background-color: #007bff; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }}
            .logout-btn:hover {{ background-color: #0056b3; }}
        </style>
    </head>
    <body>
        <h1>🔍 Permission Check for {current_user.email}</h1>
        
        <h2>Session Status:</h2>
        <div class="status {'good' if current_user.is_admin else 'bad'}">
            <strong>Current Session Admin Status:</strong> {current_user.is_admin}
        </div>
        
        <div class="status {'good' if db_is_admin else 'bad'}">
            <strong>Database Admin Status:</strong> {db_is_admin}
        </div>
        
        {'<div class="status warning"><strong>⚠️ WARNING:</strong> Your session admin status does not match the database! Please log out and log back in.</div>' if current_user.is_admin != db_is_admin else ''}
        
        <h2>Gallery Permissions:</h2>
        <div class="status {'good' if gallery_authorized else 'bad'}">
            <strong>Can Add Gallery Items:</strong> {'Yes' if gallery_authorized else 'No'}
        </div>
        
        <div class="status {'good' if current_user.is_admin else 'bad'}">
            <strong>Can Delete Gallery Items:</strong> {'Yes' if current_user.is_admin else 'No'}
        </div>
        
        <div class="status {'good' if current_user.is_admin else 'bad'}">
            <strong>Can Move Gallery Items:</strong> {'Yes' if current_user.is_admin else 'No'}
        </div>
        
        <h2>User Details:</h2>
        <p><strong>User ID:</strong> {current_user.id}</p>
        <p><strong>Email:</strong> {current_user.email}</p>
        <p><strong>Authenticated:</strong> {current_user.is_authenticated}</p>
        
        <div style="margin-top: 30px;">
            <a href="/logout" class="logout-btn">🔄 Log Out and Log Back In</a>
            <a href="/gallery" class="logout-btn" style="background-color: #28a745;">← Back to Gallery</a>
        </div>
    </body>
    </html>
    """
    
    return permissions_info

@app.route('/debug-cloud-storage')
@login_required
def debug_cloud_storage():
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('gallery'))
    
    test_result = "Not tested"
    try:
        if cloud_storage.client and cloud_storage.bucket:
            blobs = list(cloud_storage.bucket.list_blobs(max_results=3))
            test_result = f"✅ Successfully listed {len(blobs)} blobs"
        else:
            test_result = "❌ Client or bucket not available"
    except Exception as e:
        test_result = f"❌ Test failed: {str(e)}"
    
    debug_info = f"""
    <h2>Cloud Storage Debug Info</h2>
    <p><strong>Current User:</strong> {current_user.email} (Admin: {current_user.is_admin})</p>
    <p><strong>Bucket Name:</strong> {cloud_storage.bucket_name}</p>
    <p><strong>Client Available:</strong> {cloud_storage.client is not None}</p>
    <p><strong>Bucket Available:</strong> {cloud_storage.bucket is not None}</p>
    <p><strong>Auth Error:</strong> {cloud_storage.auth_error or 'None'}</p>
    <p><strong>Service Account Key Exists:</strong> {os.path.exists('tech-ethics-club-sa-key.json')}</p>
    <p><strong>Environment:</strong> {'Production (App Engine)' if os.environ.get('GAE_ENV') else 'Local Development'}</p>
    <p><strong>Project ID:</strong> {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not set')}</p>
    <p><strong>Storage Bucket Env Var:</strong> {os.environ.get('STORAGE_BUCKET', 'Not set')}</p>
    <p><strong>Service Account (from app.yaml):</strong> tech-ethics-club-sa@techandethics.iam.gserviceaccount.com</p>
    <p><strong>Test Operation:</strong> {test_result}</p>
    """
    
    if cloud_storage.client and cloud_storage.bucket:
        try:
            test_blobs = list(cloud_storage.bucket.list_blobs(max_results=1))
            debug_info += f"<p><strong>Bucket Access Test:</strong> ✅ Success (found {len(test_blobs)} blobs)</p>"
        except Exception as e:
            debug_info += f"<p><strong>Bucket Access Test:</strong> ❌ Failed - {str(e)}</p>"
    else:
        debug_info += "<p><strong>Bucket Access Test:</strong> ❌ Cannot test - client/bucket not available</p>"
    
    return debug_info

@app.route('/blog')
def blog():
    search_query = request.args.get('search', '').strip()
    author_filter = request.args.get('author_filter', '').strip()
    tag_filter = request.args.get('tag_filter', '').strip()
    search_content = request.args.get('search_content') == '1'
    exact_match = request.args.get('exact_match') == '1'
    
    all_posts = blog_storage.get_all_blog_posts()
    
    all_authors = list(set(post.get('author_name', '') for post in all_posts if post.get('author_name')))
    all_authors.sort()
    
    all_tags = set()
    for post in all_posts:
        if post.get('tags'):
            all_tags.update(post.get('tags'))
    all_tags = sorted(list(all_tags))
    
    if search_query or author_filter or tag_filter:
        filtered_posts = []
        
        for post in all_posts:
            matches = True
            
            if search_query:
                post_title = post.get('title', '').lower()
                post_content = post.get('content', '').lower()
                post_author = post.get('author_name', '').lower()
                post_tags = [tag.lower() for tag in post.get('tags', [])]
                
                search_terms = search_query.lower().split()
                
                if exact_match:
                    if not (search_query.lower() in post_title or 
                           search_query.lower() in post_content or 
                           search_query.lower() in post_author or 
                           search_query.lower() in ' '.join(post_tags)):
                        matches = False
                else:
                    if not any(word in post_title or 
                              (search_content and word in post_content) or 
                              word in post_author or 
                              any(word in tag for tag in post_tags) 
                              for word in search_terms):
                        matches = False
            
            if author_filter and matches:
                if post.get('author_name', '') != author_filter:
                    matches = False
            
            if tag_filter and matches:
                post_tags = post.get('tags', [])
                if tag_filter not in post_tags:
                    matches = False
            
            if matches:
                filtered_posts.append(post)
        
        blog_posts = filtered_posts
    else:
        blog_posts = all_posts
    
    return render_template('blog.html', blog_posts=blog_posts, 
                         all_authors=all_authors, all_tags=all_tags)

@app.route('/blog/<post_id>')
def blog_post(post_id):
    try:
        post = blog_storage.get_blog_post_by_id(post_id)
        if not post:
            flash('Blog post not found.', 'error')
            return redirect(url_for('blog'))
        
        return redirect(url_for('blog_post_by_slug', slug=post.get('slug', post_id)))
    except Exception as e:
        flash(f'Error loading blog post: {str(e)}', 'error')
        return redirect(url_for('blog'))

@app.route('/blog/post/<slug>')
def blog_post_by_slug(slug):
    try:
        post = blog_storage.get_blog_post_by_slug(slug)
        if not post:
            flash('Blog post not found.', 'error')
            return redirect(url_for('blog'))
        
        all_posts = blog_storage.get_all_blog_posts()
        all_authors = list(set(p.get('author_name', '') for p in all_posts if p.get('author_name')))
        all_authors.sort()
        
        all_tags = set()
        for p in all_posts:
            if p.get('tags'):
                all_tags.update(p.get('tags'))
        all_tags = sorted(list(all_tags))
        
        return render_template('blog_post.html', post=post, 
                             all_authors=all_authors, all_tags=all_tags)
    except Exception as e:
        flash(f'Error loading blog post: {str(e)}', 'error')
        return redirect(url_for('blog'))

@app.route('/test-blog-access')
def test_blog_access():
    if current_user.is_authenticated:
        authorized_emails = ['vaishnavanand90@gmail.com', 'asherburdeny@gmail.com', 'amazingadityab@gmail.com', 'chrisho2009@gmail.com']
        can_add_blog = current_user.email in authorized_emails
        return f"User is authenticated: {current_user.email}<br>Is admin: {current_user.is_admin}<br>Can add blog posts: {can_add_blog}"
    else:
        return "User is not authenticated"

@app.route('/debug-blog-storage')
def debug_blog_storage():
    try:
        posts = blog_storage.get_all_blog_posts()
        
        debug_info = f"""
        <h2>Blog Storage Debug Info</h2>
        <p><strong>Total posts found:</strong> {len(posts)}</p>
        <p><strong>Storage bucket:</strong> {blog_storage.bucket_name}</p>
        <p><strong>Blog file:</strong> {blog_storage.blog_blob_name}</p>
        <p><strong>Environment:</strong> {'Production' if os.environ.get('GAE_ENV') else 'Local Development'}</p>
        <p><strong>Project ID:</strong> {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not set')}</p>
        <p><strong>Storage bucket env var:</strong> {os.environ.get('STORAGE_BUCKET', 'Not set')}</p>
        """
        
        if posts:
            debug_info += "<h3>Posts:</h3><ul>"
            for post in posts:
                debug_info += f"<li>{post.get('title', 'No title')} by {post.get('author_name', 'Unknown')}</li>"
            debug_info += "</ul>"
        else:
            debug_info += "<p><em>No posts found</em></p>"
            
        return debug_info
        
    except Exception as e:
        return f"<h2>Blog Storage Error</h2><p>Error: {str(e)}</p><p>Type: {type(e).__name__}</p>"

@app.route('/add-blog-post', methods=['GET', 'POST'])
@login_required
def add_blog_post():
    print(f"DEBUG: add_blog_post route accessed by user: {current_user.email if current_user.is_authenticated else 'Not authenticated'}")
    
    authorized_emails = [
        'vaishnavanand90@gmail.com',
        'asherburdeny@gmail.com',
        'amazingadityab@gmail.com',
        'chrisho2009@gmail.com'
    ]
    if current_user.email not in authorized_emails:
        print(f"DEBUG: Access denied for user: {current_user.email}")
        flash('Access denied. Only authorized users can add blog posts.', 'error')
        return redirect(url_for('blog'))
    
    print("DEBUG: User authorized, showing form")
    
    if request.method == 'POST':
        title = request.form.get('title')
        author_name = request.form.get('author_name')
        author_city = request.form.get('author_city', '').strip()
        author_state = request.form.get('author_state', '').strip()
        author_country = request.form.get('author_country', '').strip()
        author_school = request.form.get('author_school', '').strip()
        tags = request.form.get('tags')
        
        paragraph_headers = request.form.getlist('paragraph_headers[]')
        paragraph_contents = request.form.getlist('paragraph_contents[]')
        paragraph_images = request.files.getlist('paragraph_images[]')
        
        works_cited_titles = request.form.getlist('works_cited_titles[]')
        works_cited_urls = request.form.getlist('works_cited_urls[]')
        works_cited_authors = request.form.getlist('works_cited_authors[]')
        
        if not title or not author_name or not paragraph_contents or not any(paragraph_contents):
            flash('Title, author name, and at least one paragraph are required.', 'error')
            return redirect(url_for('add_blog_post'))
        
        image_urls = []
        for i, image_file in enumerate(paragraph_images):
            if image_file and image_file.filename:
                try:
                    import uuid
                    import os
                    file_extension = os.path.splitext(image_file.filename)[1]
                    filename = f"{uuid.uuid4()}{file_extension}"
                    
                    image_url = cloud_storage.upload_file(image_file, filename, 'blog_images')
                    if image_url:
                        image_urls.append(image_url)
                    else:
                        image_urls.append('')
                except Exception as e:
                    print(f"Error uploading image: {e}")
                    image_urls.append('')
            else:
                image_urls.append('')
        
        content_parts = []
        for i, content in enumerate(paragraph_contents):
            if content.strip():
                header = paragraph_headers[i].strip() if i < len(paragraph_headers) and paragraph_headers[i].strip() else None
                
                image_marker = f"[IMAGE:{image_urls[i]}]" if i < len(image_urls) and image_urls[i] else ""
                
                if header:
                    content_parts.append(f"## {header}\n\n{content.strip()}\n{image_marker}")
                else:
                    content_parts.append(f"{content.strip()}\n{image_marker}")
        
        content = '\n\n'.join(content_parts)
        
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        new_post = blog_storage.add_blog_post(title, content, current_user.email, author_name, author_city, author_state, author_country, author_school, tag_list)
        
        if new_post:
            flash('Blog post published successfully!', 'success')
            return redirect(url_for('blog_post_by_slug', slug=new_post['slug']))
        else:
            flash('Error publishing blog post. Please try again.', 'error')
            return redirect(url_for('add_blog_post'))
    
    return render_template('add_blog_post.html')

@app.route('/edit-blog-post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog_post(post_id):
    authorized_emails = [
        'vaishnavanand90@gmail.com',
        'asherburdeny@gmail.com',
        'amazingadityab@gmail.com',
        'chrisho2009@gmail.com'
    ]
    if current_user.email not in authorized_emails:
        flash('Access denied. Only authorized users can edit blog posts.', 'error')
        return redirect(url_for('blog'))
    
    post = blog_storage.get_blog_post_by_id(post_id)
    if not post:
        flash('Blog post not found.', 'error')
        return redirect(url_for('blog'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        author_name = request.form.get('author_name')
        author_city = request.form.get('author_city', '').strip()
        author_state = request.form.get('author_state', '').strip()
        author_country = request.form.get('author_country', '').strip()
        author_school = request.form.get('author_school', '').strip()
        tags = request.form.get('tags')
        
        paragraph_headers = request.form.getlist('paragraph_headers[]')
        paragraph_contents = request.form.getlist('paragraph_contents[]')
        paragraph_images = request.files.getlist('paragraph_images[]')
        
        works_cited_titles = request.form.getlist('works_cited_titles[]')
        works_cited_urls = request.form.getlist('works_cited_urls[]')
        works_cited_authors = request.form.getlist('works_cited_authors[]')
        
        if not title or not author_name or not paragraph_contents or not any(paragraph_contents):
            flash('Title, author name, and at least one paragraph are required.', 'error')
            return redirect(url_for('edit_blog_post', post_id=post_id))
        
        image_urls = []
        existing_image_urls = request.form.getlist('existing_image_urls[]')
        
        for i, image_file in enumerate(paragraph_images):
            if image_file and image_file.filename:
                try:
                    import uuid
                    import os
                    file_extension = os.path.splitext(image_file.filename)[1]
                    filename = f"{uuid.uuid4()}{file_extension}"
                    
                    image_url = cloud_storage.upload_file(image_file, filename, 'blog_images')
                    if image_url:
                        image_urls.append(image_url)
                    else:
                        image_urls.append('')
                except Exception as e:
                    print(f"Error uploading image: {e}")
                    image_urls.append('')
            else:
                existing_url = existing_image_urls[i] if i < len(existing_image_urls) else ''
                image_urls.append(existing_url)
        
        content_parts = []
        for i, content in enumerate(paragraph_contents):
            if content.strip():
                header = paragraph_headers[i].strip() if i < len(paragraph_headers) and paragraph_headers[i].strip() else None
                
                image_marker = f"[IMAGE:{image_urls[i]}]" if i < len(image_urls) and image_urls[i] else ""
                
                if header:
                    content_parts.append(f"## {header}\n\n{content.strip()}\n{image_marker}")
                else:
                    content_parts.append(f"{content.strip()}\n{image_marker}")
        
        content = '\n\n'.join(content_parts)
        
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        updated_post = blog_storage.update_blog_post(post_id, title, content, author_name, author_city, author_state, author_country, author_school, tag_list)
        
        if updated_post:
            flash('Blog post updated successfully!', 'success')
            return redirect(url_for('blog_post_by_slug', slug=updated_post['slug']))
        else:
            flash('Error updating blog post. Please try again.', 'error')
            return redirect(url_for('edit_blog_post', post_id=post_id))
    
    return render_template('edit_blog_post.html', post=post)

@app.route('/delete-blog-post/<post_id>', methods=['POST'])
@login_required
def delete_blog_post(post_id):
    authorized_emails = [
        'vaishnavanand90@gmail.com',
        'asherburdeny@gmail.com',
        'amazingadityab@gmail.com',
        'chrisho2009@gmail.com'
    ]
    if current_user.email not in authorized_emails:
        flash('Access denied. Only authorized users can delete blog posts.', 'error')
        return redirect(url_for('blog'))
    
    try:
        if blog_storage.delete_blog_post(post_id):
            flash('Blog post deleted successfully.', 'success')
        else:
            flash('Error deleting blog post.', 'error')
    except Exception as e:
        flash(f'Error deleting blog post: {str(e)}', 'error')
    
    return redirect(url_for('blog'))


@app.route("/cis-news", methods=["GET", "POST"])
def cis_news():
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Please log in to post CIS news.", "error")
            return redirect(url_for("login"))

        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        image_file = request.files.get("image")

        if not title or not body:
            flash("Headline and content are required.", "error")
            return redirect(url_for("cis_news"))

        image_url = None
        if image_file and image_file.filename:
            allowed = (".jpg", ".jpeg", ".png", ".gif", ".webp")
            ext = os.path.splitext(image_file.filename)[1].lower()
            if ext not in allowed:
                flash("Please upload a JPG, PNG, GIF, or WebP image.", "error")
                return redirect(url_for("cis_news"))
            try:
                optimized = image_optimizer.optimize_image(
                    image_file, image_file.filename
                )
                fname = image_optimizer.get_optimized_filename(image_file.filename)
                image_url = cloud_storage.upload_file(
                    optimized, fname, "cis_news_images"
                )
                if not image_url:
                    flash(
                        "Image upload failed. Try again or post without an image.",
                        "error",
                    )
                    return redirect(url_for("cis_news"))
            except Exception as e:
                flash(f"Could not process image: {str(e)}", "error")
                return redirect(url_for("cis_news"))

        created = cis_news_storage.add_item(
            title, body, image_url, current_user.email
        )
        if created:
            flash("News posted.", "success")
        else:
            flash("Could not save news. Please try again.", "error")
        return redirect(url_for("cis_news"))

    all_items = cis_news_storage.get_all_items()
    # Initial search box value (e.g. shared link); filtering runs in the browser as the user types.
    search_query = (request.args.get("search") or "").strip()

    return render_template(
        "cis_news.html",
        cis_news_items=all_items,
        cis_search_query=search_query,
        cis_news_total=len(all_items),
        can_manage_cis_news=user_can_manage_cis_news(),
    )


@app.route("/cis-news/delete/<item_id>", methods=["POST"])
@login_required
def delete_cis_news(item_id):
    item = cis_news_storage.get_item_by_id(item_id)
    if not item:
        flash("That news item was not found.", "error")
        return redirect(url_for("cis_news"))
    if not user_can_delete_cis_news_item(item):
        flash("You can only delete your own posts unless you are a moderator.", "error")
        return redirect(url_for("cis_news"))
    if cis_news_storage.delete_item(item_id):
        flash("News item removed.", "success")
    else:
        flash("Item not found or could not be deleted.", "error")
    return redirect(url_for("cis_news"))


@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if not name or not email or not subject or not message:
        flash('All fields are required.', 'error')
        return redirect(url_for('contact'))
    
    try:
        email_body = f"""
New Contact Form Submission from Tech & Ethics Club Website

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This message was sent from the Tech & Ethics Club contact form.
        """
        
        sender_email = "techandethicsclub@gmail.com"
        recipient_email = "techandethicsclub@gmail.com"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Contact Form: {subject} - {name}"
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        email_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not email_password:
            print("=" * 50)
            print("CONTACT FORM SUBMISSION")
            print("=" * 50)
            print(f"From: {name} ({email})")
            print(f"Subject: {subject}")
            print(f"Message: {message}")
            print("=" * 50)
            print("Email would be sent to:", recipient_email)
            print("=" * 50)
            print("⚠️  GMAIL_APP_PASSWORD not set - email not sent")
            print("=" * 50)
            
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, email_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Contact form email sent successfully to {recipient_email}")
            
        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP Authentication failed - check Gmail App Password")
            flash('There was an error sending your message. Please try again or contact us directly.', 'error')
            return redirect(url_for('contact'))
        except Exception as e:
            print(f"❌ SMTP Error: {str(e)}")
            flash('There was an error sending your message. Please try again or contact us directly.', 'error')
            return redirect(url_for('contact'))
        
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
        
    except Exception as e:
        print(f"Error sending contact form email: {str(e)}")
        flash('There was an error sending your message. Please try again or contact us directly.', 'error')
        return redirect(url_for('contact'))

class GalleryItem:
    """Normalizes a gallery item dict from cloud_storage for templates (URLs, lists, flags)."""

    def __init__(self, item_data):
        self.id = item_data.get('id')
        self.title = item_data.get('title')
        self.description = item_data.get('description')
        self.image_filename = item_data.get('image_filename')
        self.image_url = item_data.get('image_url')
        self.image_link = item_data.get('image_link')  # Link for main image
        self.project_poster_url = item_data.get('project_poster_url')  # Project poster image URL
        self.project_poster_link = item_data.get('project_poster_link')  # Project poster link
        self.project_poster_filename = item_data.get('project_poster_filename')  # Project poster filename
        
        # Ensure additional_images is always a list
        additional_images_raw = item_data.get('additional_images', [])
        if isinstance(additional_images_raw, str):
            # Handle case where it might be stored as a string
            import json
            try:
                self.additional_images = json.loads(additional_images_raw) if additional_images_raw else []
            except:
                self.additional_images = [additional_images_raw] if additional_images_raw else []
        elif additional_images_raw is None:
            self.additional_images = []
        else:
            self.additional_images = list(additional_images_raw) if additional_images_raw else []
        
        self.additional_filenames = item_data.get('additional_filenames', [])
        
        # Ensure additional_image_links is always a list
        additional_image_links_raw = item_data.get('additional_image_links', [])
        if isinstance(additional_image_links_raw, str):
            import json
            try:
                self.additional_image_links = json.loads(additional_image_links_raw) if additional_image_links_raw else []
            except:
                self.additional_image_links = [additional_image_links_raw] if additional_image_links_raw else []
        elif additional_image_links_raw is None:
            self.additional_image_links = []
        else:
            self.additional_image_links = list(additional_image_links_raw) if additional_image_links_raw else []
        self.project_link = item_data.get('project_link')  # Backward compatibility
        self.project_links = item_data.get('project_links', [])  # New: list of project links
        
        # Backward compatibility: if project_links is empty but project_link exists, convert it
        if not self.project_links and self.project_link:
            self.project_links = [{'title': 'View Project', 'url': self.project_link}]
        
        self.tags = item_data.get('tags', [])
        self.videos = item_data.get('videos', [])
        
        # Handle slideshow images
        slideshow_images_raw = item_data.get('slideshow_images', [])
        if isinstance(slideshow_images_raw, str):
            import json
            try:
                self.slideshow_images = json.loads(slideshow_images_raw) if slideshow_images_raw else []
            except:
                self.slideshow_images = [slideshow_images_raw] if slideshow_images_raw else []
        elif slideshow_images_raw is None:
            self.slideshow_images = []
        else:
            self.slideshow_images = list(slideshow_images_raw) if slideshow_images_raw else []
        
        self.slideshow_filenames = item_data.get('slideshow_filenames', [])
        
        # Handle slideshow image links
        slideshow_image_links_raw = item_data.get('slideshow_image_links', [])
        if isinstance(slideshow_image_links_raw, str):
            import json
            try:
                self.slideshow_image_links = json.loads(slideshow_image_links_raw) if slideshow_image_links_raw else []
            except:
                self.slideshow_image_links = [slideshow_image_links_raw] if slideshow_image_links_raw else []
        elif slideshow_image_links_raw is None:
            self.slideshow_image_links = []
        else:
            self.slideshow_image_links = list(slideshow_image_links_raw) if slideshow_image_links_raw else []
        
        self.has_slideshow = len(self.slideshow_images) > 0
        self.slideshow_title = item_data.get('slideshow_title')
        
        self.course_id = item_data.get('course_id')
        self.created_by = item_data.get('created_by')
        self.created_at = item_data.get('created_at')
        
        self.creators = item_data.get('creators', [])
        
        if self.creators and len(self.creators) > 0:
            first_creator = self.creators[0]
            self.creator_name = first_creator.get('name', '')
            self.creator_email = first_creator.get('email', '')
            self.creator_linkedin = first_creator.get('linkedin', '')
            self.creator_city = first_creator.get('city', '')
            self.creator_state = first_creator.get('state', '')
            self.creator_country = first_creator.get('country', '')
            self.creator_school = first_creator.get('school', '')
        else:
            self.creator_name = item_data.get('creator_name', '')
            self.creator_email = item_data.get('creator_email', '')
            self.creator_linkedin = item_data.get('creator_linkedin', '')
            self.creator_city = item_data.get('creator_city', '')
            self.creator_state = item_data.get('creator_state', '')
            self.creator_country = item_data.get('creator_country', '')
            self.creator_school = item_data.get('creator_school', '')
            if self.creator_name:
                self.creators = [{
                    'name': self.creator_name,
                    'email': self.creator_email,
                    'linkedin': self.creator_linkedin,
                    'city': self.creator_city,
                    'state': self.creator_state,
                    'country': self.creator_country,
                    'school': self.creator_school
                }]
        
        self.has_videos = len(self.videos) > 0
        # Ensure additional_images is a list before checking length
        additional_images_list = self.additional_images if isinstance(self.additional_images, (list, tuple)) else []
        self.has_images = bool(self.image_url) or len(additional_images_list) > 0
        print(f"GalleryItem init - additional_images: {self.additional_images}, type: {type(self.additional_images)}, length: {len(additional_images_list) if isinstance(self.additional_images, (list, tuple)) else 'NOT_LIST'}, has_images: {self.has_images}")
        self.is_mixed_media = self.has_videos and self.has_images
        self.has_multiple_creators = len(self.creators) > 1

if __name__ == '__main__':
    app.run(debug=False, port=5000) 