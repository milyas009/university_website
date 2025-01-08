from flask import render_template, request, json, Response, flash, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from application import app, db
from application.models import User, Course, Enrollment
from application.forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.queryset.visitor import Q
import os

courseData = [
    {"courseID": "1111", "title": "PHP 101", "description": "Intro to PHP", "credits": 3, "term": "Fall, Spring"},
    {"courseID": "2222", "title": "Java 1", "description": "Intro to Java Programming", "credits": 4, "term": "Spring"},
    {"courseID": "3333", "title": "Adv PHP 201", "description": "Advanced PHP Programming", "credits": 3, "term": "Fall"},
    {"courseID": "4444", "title": "Angular 1", "description": "Intro to Angular", "credits": 3, "term": "Fall, Spring"},
    {"courseID": "5555", "title": "Java 2", "description": "Advanced Java Programming", "credits": 4, "term": "Fall"}
]

@app.route('/', methods=['GET'])
@app.route("/index", methods=['GET'])
@app.route("/home", methods=['GET'])
def index():
    return render_template("index.html", index=True)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template("login.html", title="Login", form=form, login=True)

@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user_exists = User.objects(email=form.email.data).first()
            if user_exists:
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            # Generate a new user_id
            last_user = User.objects.order_by('-user_id').first()
            next_id = 1 if not last_user else last_user.user_id + 1
            
            user = User(
                user_id=next_id,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            user.set_password(form.password.data)
            user.save()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration', 'danger')
            
    return render_template("register.html", title="Register", form=form, register=True)

@app.route("/courses/")
@app.route("/courses/<term>")
def courses(term = None):
    if term is None:
        term = "Spring 2019"
    
    courseData = [
        {"courseID":"1111","title":"PHP 101","description":"Intro to PHP","credits":3,"term":"Fall, Spring"},
        {"courseID":"2222","title":"Java 1","description":"Intro to Java Programming","credits":4,"term":"Spring"},
        {"courseID":"3333","title":"Adv PHP 201","description":"Advanced PHP Programming","credits":3,"term":"Fall"},
        {"courseID":"4444","title":"Angular 1","description":"Intro to Angular","credits":3,"term":"Fall, Spring"},
        {"courseID":"5555","title":"Java 2","description":"Advanced Java Programming","credits":4,"term":"Fall"}
    ]

    # First, ensure all courses exist in the database
    for course in courseData:
        try:
            # Check if course exists
            existing_course = Course.objects(course_id=course['courseID']).first()
            if not existing_course:
                # Create new course
                new_course = Course(
                    course_id=course['courseID'],
                    title=course['title'],
                    description=course['description'],
                    credits=course['credits'],
                    term=course['term']
                )
                new_course.save()
        except Exception as e:
            app.logger.error(f"Error processing course {course['courseID']}: {str(e)}")

    return render_template("courses.html", courseData=courseData, courses=True, term=term)

@app.route("/enrollment", methods=["GET", "POST"])
@login_required
def enrollment():
    if request.method == 'POST':
        try:
            course_id = request.form.get('courseID')
            
            if not course_id:
                flash('Missing course information', 'danger')
                return redirect(url_for('courses'))

            # Get the course from database
            course = Course.objects(course_id=course_id).first()
            if not course:
                flash('Course not found', 'danger')
                return redirect(url_for('courses'))

            # Check if already enrolled
            enrollment_exists = Enrollment.objects(user=current_user.id, course=course.id).first()
            if enrollment_exists:
                flash(f'You are already enrolled in {course.title}', 'info')
                return redirect(url_for('courses'))

            # Create new enrollment
            enrollment = Enrollment(
                user=current_user.id,
                course=course.id
            ).save()
            
            flash(f'Successfully enrolled in {course.title}', 'success')
            return render_template(
                "enrollment.html",
                enrollment=True,
                data={"id": course.course_id, "title": course.title, "term": course.term}
            )
            
        except Exception as e:
            app.logger.error(f'Error during enrollment: {str(e)}')
            flash(f'Error during enrollment: {str(e)}', 'danger')
            return redirect(url_for('courses'))
            
    return redirect(url_for('courses'))

@app.route("/api/", methods=['GET'])
@app.route("/api/<idx>", methods=['GET'])
def api(idx=None):
    if idx is None:
        jdata = courseData
    else:
        try:
            jdata = courseData[int(idx)]
        except IndexError:
            return Response(json.dumps({"error": "Invalid index"}), status=404, mimetype="application/json")
        except ValueError:
            return Response(json.dumps({"error": "Invalid index format"}), status=400, mimetype="application/json")
    return Response(json.dumps(jdata), mimetype="application/json")

@app.route("/user", methods=['GET'])
def user():
    users = User.objects.all()
    return render_template("user.html", users=users)

@app.route("/my-courses")
@login_required
def my_courses():
    try:
        # Get all enrollments for current user with course details
        enrollments = Enrollment.objects(user=current_user.id)
        enrolled_courses = []
        
        for enrollment in enrollments:
            course = Course.objects(id=enrollment.course.id).first()
            if course:
                enrolled_courses.append({
                    'course_id': course.course_id,
                    'title': course.title,
                    'term': course.term,
                    'description': course.description,
                    'credits': course.credits,
                    'completed': enrollment.completed,
                    'progress': enrollment.progress
                })
        
        return render_template(
            "my_courses.html", 
            courses=enrolled_courses,
            enrolled=bool(enrolled_courses)
        )
    except Exception as e:
        flash(f"Error loading courses: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route("/schedule")
@login_required
def schedule():
    # Sample schedule data - in production, this would come from a database
    schedule_data = {
        "Monday": [
            {"time": "9:00 AM", "course": "PHP 101"},
            {"time": "11:00 AM", "course": "Angular 1"}
        ],
        "Tuesday": [
            {"time": "9:00 AM", "course": "Java 1"},
            {"time": "2:00 PM", "course": "Python Basics"}
        ]
    }
    return render_template("schedule.html", schedule=schedule_data)

@app.route("/library")
def library():
    # Sample library resources - in production, this would come from a database
    resources = {
        "ebooks": [
            {"title": "Python Programming", "author": "John Doe", "url": "#"},
            {"title": "Web Development Basics", "author": "Jane Smith", "url": "#"}
        ],
        "videos": [
            {"title": "JavaScript Tutorial", "duration": "1:30:00", "url": "#"},
            {"title": "Database Design", "duration": "45:00", "url": "#"}
        ]
    }
    return render_template("library.html", resources=resources)

@app.route("/study-materials")
def study_materials():
    # Sample study materials - in production, this would come from a database
    materials = {
        "PHP": [
            {"title": "PHP Basics Handbook", "type": "pdf", "url": "#"},
            {"title": "Practice Exercises", "type": "doc", "url": "#"}
        ],
        "Java": [
            {"title": "Java Fundamentals Guide", "type": "pdf", "url": "#"},
            {"title": "OOP Concepts", "type": "pdf", "url": "#"}
        ]
    }
    return render_template("study_materials.html", materials=materials)

@app.route("/help-center")
def help_center():
    # Sample FAQ data
    faqs = [
        {
            "question": "How do I reset my password?",
            "answer": "Click on the 'Forgot Password' link on the login page and follow the instructions sent to your email."
        },
        {
            "question": "How do I enroll in a course?",
            "answer": "Browse the courses page, select your desired course, and click the 'Enroll' button. You must be logged in to enroll."
        }
    ]
    return render_template("help_center.html", faqs=faqs)

@app.route("/about")
def about():
    # Sample statistics
    stats = {
        "courses": 50,
        "instructors": 30,
        "students": 1000,
        "years": 3
    }
    return render_template("about.html", stats=stats)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if all([name, email, message]):
            # In production, you would send this to your email system
            flash("Thank you for your message. We'll get back to you soon!", "success")
            return redirect(url_for('contact'))
        else:
            flash("Please fill in all fields", "danger")
    
    return render_template("contact.html")

@app.route("/profile")
@login_required
def profile():
    # Get enrollment statistics
    enrollments = Enrollment.objects(user=current_user.id)
    stats = {
        "total": len(enrollments),
        "completed": sum(1 for e in enrollments if getattr(e, 'completed', False)),
        "in_progress": sum(1 for e in enrollments if not getattr(e, 'completed', False))
    }
    return render_template("profile.html", stats=stats)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/update-profile", methods=['POST'])
@login_required
def update_profile():
    try:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        if first_name and last_name:
            user = User.objects(id=current_user.id).first()
            user.update(
                first_name=first_name,
                last_name=last_name
            )
            flash("Profile updated successfully!", "success")
        else:
            flash("Please provide both first and last name", "danger")
            
    except Exception as e:
        flash(f"Error updating profile: {str(e)}", "danger")
        
    return redirect(url_for('profile'))

@app.route("/change-password", methods=['POST'])
@login_required
def change_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash("Please fill in all password fields", "danger")
            return redirect(url_for('settings'))
            
        if new_password != confirm_password:
            flash("New passwords don't match", "danger")
            return redirect(url_for('settings'))
            
        user = User.objects(id=current_user.id).first()
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            flash("Password updated successfully!", "success")
        else:
            flash("Current password is incorrect", "danger")
            
    except Exception as e:
        flash(f"Error changing password: {str(e)}", "danger")
        
    return redirect(url_for('settings'))

@app.route("/submit-support-ticket", methods=['POST'])
@login_required
def submit_support_ticket():
    try:
        subject = request.form.get('subject')
        description = request.form.get('description')
        
        if not all([subject, description]):
            flash("Please fill in all fields", "danger")
            return redirect(url_for('help_center'))
            
        # In production, you would save this to a database and notify support staff
        flash("Support ticket submitted successfully! We'll respond within 24 hours.", "success")
        
    except Exception as e:
        flash(f"Error submitting ticket: {str(e)}", "danger")
        
    return redirect(url_for('help_center'))

@app.route("/update-notification-settings", methods=['POST'])
@login_required
def update_notification_settings():
    try:
        email_notif = request.form.get('emailNotif') == 'on'
        course_updates = request.form.get('courseUpdates') == 'on'
        news_updates = request.form.get('newsUpdates') == 'on'
        
        # In production, you would save these preferences to the user's profile
        flash("Notification preferences updated successfully!", "success")
        
    except Exception as e:
        flash(f"Error updating preferences: {str(e)}", "danger")
        
    return redirect(url_for('settings'))

@app.route("/update-privacy-settings", methods=['POST'])
@login_required
def update_privacy_settings():
    try:
        profile_visible = request.form.get('profileVisibility') == 'on'
        show_progress = request.form.get('showProgress') == 'on'
        
        # In production, you would save these settings to the user's profile
        flash("Privacy settings updated successfully!", "success")
        
    except Exception as e:
        flash(f"Error updating privacy settings: {str(e)}", "danger")
        
    return redirect(url_for('settings'))

@app.route("/download-material/<material_id>")
@login_required
def download_material(material_id):
    try:
        # In production, you would fetch the material from your storage system
        # For now, we'll just show a message
        flash("Material download started!", "success")
        
    except Exception as e:
        flash(f"Error downloading material: {str(e)}", "danger")
        
    return redirect(url_for('study_materials'))

@app.route("/dashboard")
@login_required
def dashboard():
    # Get user's courses and stats
    enrollments = Enrollment.objects(user=current_user.id)
    
    # Calculate statistics
    stats = {
        "total_courses": len(enrollments),
        "completed_courses": sum(1 for e in enrollments if e.completed),
        "hours_spent": sum(e.hours_spent for e in enrollments if hasattr(e, 'hours_spent')),
        "certificates": sum(1 for e in enrollments if e.completed)
    }
    
    # Get current courses
    current_courses = []
    for enrollment in enrollments:
        if not enrollment.completed:
            course = Course.objects(id=enrollment.course.id).first()
            if course:
                current_courses.append({
                    "title": course.title,
                    "description": course.description,
                    "progress": enrollment.progress,
                    "last_accessed": enrollment.last_accessed.strftime("%B %d, %Y") if enrollment.last_accessed else "Never"
                })
    
    # Sample deadlines (replace with actual data from your database)
    deadlines = [
        {"date": "Mar 15", "title": "Final Project", "course": "PHP 101"},
        {"date": "Mar 18", "title": "Quiz 2", "course": "Java 1"},
        {"date": "Mar 20", "title": "Assignment 3", "course": "Angular 1"}
    ]
    
    # Sample achievements (replace with actual data)
    achievements = [
        {"icon": "fas fa-trophy", "title": "Completed PHP Basics", "date": "2 days ago"},
        {"icon": "fas fa-star", "title": "Perfect Quiz Score", "date": "1 week ago"},
        {"icon": "fas fa-award", "title": "First Assignment", "date": "2 weeks ago"}
    ]
    
    return render_template(
        "dashboard.html",
        stats=stats,
        current_courses=current_courses,
        deadlines=deadlines,
        achievements=achievements
    )

# Helper functions
def get_user_progress(user_id):
    """Calculate user's course progress"""
    try:
        enrollments = Enrollment.objects(user=user_id)
        total_courses = len(enrollments)
        completed_courses = sum(1 for e in enrollments if getattr(e, 'completed', False))
        
        if total_courses > 0:
            progress = (completed_courses / total_courses) * 100
        else:
            progress = 0
            
        return {
            'total': total_courses,
            'completed': completed_courses,
            'in_progress': total_courses - completed_courses,
            'percentage': round(progress, 1)
        }
    except Exception as e:
        app.logger.error(f"Error calculating progress: {str(e)}")
        return None

def get_recent_activities(user_id, limit=5):
    """Get user's recent activities"""
    try:
        # In production, you would fetch this from an activity log
        activities = [
            {"type": "course_enrolled", "course": "Python Basics", "date": "2024-01-15"},
            {"type": "assignment_submitted", "course": "Java 1", "date": "2024-01-14"},
            {"type": "course_completed", "course": "Web Development", "date": "2024-01-10"}
        ]
        return activities[:limit]
    except Exception as e:
        app.logger.error(f"Error fetching activities: {str(e)}")
        return []

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Create error templates (404.html)

@app.route("/course/<course_id>")
def course_detail(course_id):
    course = Course.objects(course_id=course_id).first_or_404()
    
    # Check if user is enrolled
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = Enrollment.objects(user=current_user.id, course=course.id).first()
        is_enrolled = enrollment is not None
    
    # Sample data - replace with actual data from your database
    course.full_description = "Detailed course description..."
    course.learning_outcomes = [
        "Build professional PHP applications",
        "Understand OOP concepts",
        "Work with databases",
        "Create secure applications"
    ]
    course.requirements = [
        "Basic understanding of HTML and CSS",
        "Basic programming knowledge",
        "A computer with internet access"
    ]
    course.modules = [
        {
            "title": "Introduction to PHP",
            "lessons": [
                {"title": "Setting up PHP", "duration": "10:00", "type_icon": "fa-video"},
                {"title": "Basic Syntax", "duration": "15:00", "type_icon": "fa-video"},
                {"title": "Variables", "duration": "12:00", "type_icon": "fa-video"}
            ]
        }
    ]
    course.instructor = {
        "name": "John Doe",
        "title": "Senior PHP Developer",
        "image": "path/to/image",
        "bio": "Experienced developer with 10+ years...",
        "students": 5000,
        "courses": 10
    }
    course.ratings = {
        5: 75,
        4: 20,
        3: 3,
        2: 1,
        1: 1
    }
    course.reviews = [
        {
            "user_name": "Jane Smith",
            "user_image": "path/to/image",
            "rating": 5,
            "date": "2 weeks ago",
            "comment": "Excellent course!"
        }
    ]
    
    return render_template("course_detail.html", course=course, is_enrolled=is_enrolled)

@app.route("/search")
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    # Basic search implementation
    if query:
        courses = Course.objects(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
        
        if category:
            courses = courses.filter(category=category)
            
        results = [{
            'id': str(course.id),
            'course_id': course.course_id,
            'title': course.title,
            'description': course.description,
            'category': course.category,
            'instructor': course.instructor.name if course.instructor else None,
            'rating': course.average_rating if hasattr(course, 'average_rating') else None
        } for course in courses]
    else:
        results = []
        
    return render_template(
        'search_results.html',
        query=query,
        results=results,
        category=category
    )

@app.route("/api/search")
def api_search():
    """API endpoint for live search"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
        
    courses = Course.objects(title__icontains=query).limit(5)
    results = [{
        'id': str(course.id),
        'title': course.title,
        'url': url_for('course_detail', course_id=course.course_id)
    } for course in courses]
    
    return jsonify(results)