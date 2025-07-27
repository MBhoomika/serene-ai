from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from serene_ai import SereneAI, DailyChallenge
from dotenv import load_dotenv
import os
from pathlib import Path
import time
import openai
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from models import db, User, CommunityPost, Comment, ChatHistory, Journal, MoodTracker, MeditationSession

# Load environment variables
load_dotenv()

# Verify API key is loaded
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("OpenAI API key not found in environment variables")

# Create instance directory if it doesn't exist
instance_path = Path(__file__).parent / 'instance'
instance_path.mkdir(exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///serene_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize SereneAI
try:
    serene_ai = SereneAI()
    print("✅ SereneAI initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize SereneAI: {str(e)}")
    serene_ai = None

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = "basic"

migrate = Migrate(app, db)

# Initialize the database
def init_db():
    with app.app_context():
        # Create tables only if they don't exist
        db.create_all()
        print("Database tables initialized successfully")

# Initialize the database
init_db()

# Clear any existing session when starting the app
@app.before_request
def clear_session():
    if not current_user.is_authenticated:
        session.clear()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.before_request
def before_request():
    """Handle authentication and redirects before each request."""
    # List of routes that don't require authentication
    public_routes = ['login', 'register', 'static']
    
    # Always redirect to login if not authenticated
    if not current_user.is_authenticated and request.endpoint not in public_routes:
        return redirect(url_for('login'))

@app.route('/')
def index():
    """Root route - always redirect to login first"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # If already logged in, redirect to menu
    if current_user.is_authenticated:
        return redirect(url_for('menu'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if fields are filled
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        # Query for user
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('menu'))
        else:
            flash('Invalid username or password.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    # If already logged in, redirect to menu
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate all fields are filled
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
            
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
            
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
            
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/chat_page')
@login_required
def chat_page():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/meditation')
@login_required
def meditation():
    """Handle meditation page."""
    try:
        return render_template('meditation.html')
    except Exception as e:
        print(f"Error in meditation route: {str(e)}")
        flash('An error occurred while loading the meditation page', 'error')
        return redirect(url_for('menu'))

@app.route('/journal')
@login_required
def journal():
    # Get user's journal entries, ordered by most recent first
    entries = Journal.query.filter_by(user_id=current_user.id)\
        .order_by(Journal.timestamp.desc()).all()
    return render_template('journal.html', entries=entries)

@app.route('/mood_tracker')
@login_required
def mood_tracker():
    return render_template('mood_tracker.html')

@app.route('/save_mood', methods=['POST'])
@login_required
def save_mood():
    try:
        data = request.get_json()
        mood = data.get('mood')
        note = data.get('note')
        
        if not mood:
            return jsonify({'error': 'Please select a mood'}), 400
            
        entry = MoodTracker(
            user_id=current_user.id,
            mood=mood,
            note=note
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Mood saved successfully'})
    except Exception as e:
        print(f"Error saving mood: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_post', methods=['POST'])
@login_required
def save_post():
    try:
        content = request.form.get('content')
        if not content:
            flash('Post content cannot be empty', 'error')
            return redirect(url_for('community'))
        
        new_post = CommunityPost(
            content=content,
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        flash('Your post has been shared with the community!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while saving your post', 'error')
        app.logger.error(f"Error saving post: {str(e)}")
    return redirect(url_for('community'))

@app.route('/community')
@login_required
def community():
    try:
        if not current_user.is_authenticated:
            flash('Please log in to access the community page', 'error')
            return redirect(url_for('login'))
            
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Query posts with user relationship loaded
        posts = CommunityPost.query.options(
            db.joinedload(CommunityPost.user),
            db.joinedload(CommunityPost.comments).joinedload(Comment.user)
        ).order_by(CommunityPost.timestamp.desc()).paginate(page=page, per_page=per_page)
        
        # Calculate statistics
        total_posts = CommunityPost.query.count()
        total_comments = Comment.query.count()
        total_likes = db.session.query(db.func.sum(CommunityPost.likes)).scalar() or 0
        
        return render_template('community.html', 
                             posts=posts,
                             total_posts=total_posts,
                             total_comments=total_comments,
                             total_likes=total_likes)
    except Exception as e:
        app.logger.error(f"Error in community route: {str(e)}")
        flash('An error occurred while loading the community page', 'error')
        return redirect(url_for('menu'))

@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    try:
        post = CommunityPost.query.get_or_404(post_id)
        post.likes += 1
        db.session.commit()
        return jsonify({'success': True, 'likes': post.likes})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error liking post: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    try:
        content = request.form.get('content')
        if not content:
            flash('Comment cannot be empty', 'error')
            return redirect(url_for('community'))
        
        post = CommunityPost.query.get_or_404(post_id)
        comment = Comment(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding your comment', 'error')
        app.logger.error(f"Error adding comment: {str(e)}")
    return redirect(url_for('community'))

@app.route('/resources')
@login_required
def resources():
    return render_template('resources.html')

@app.route('/log_meditation', methods=['POST'])
@login_required
def log_meditation():
    try:
        data = request.get_json()
        duration = data.get('duration')
        meditation_type = data.get('type')
        
        session = MeditationSession(
            user_id=current_user.id,
            duration=duration,
            type=meditation_type
        )
        db.session.add(session)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error logging meditation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/menu')
@login_required
def menu():
    """Menu route - only accessible when logged in"""
    try:
        # Get daily challenge
        daily_challenge = DailyChallenge().get_daily_challenge()
        
        # Get user's recent journal entries
        recent_journals = Journal.query.filter_by(user_id=current_user.id)\
            .order_by(Journal.timestamp.desc())\
            .limit(3)\
            .all()
        
        # Get user's recent chat history
        recent_chats = ChatHistory.query.filter_by(user_id=current_user.id)\
            .order_by(ChatHistory.timestamp.desc())\
            .limit(3)\
            .all()
        
        return render_template('menu.html',
                             daily_challenge=daily_challenge,
                             recent_journals=recent_journals,
                             recent_chats=recent_chats)
    except Exception as e:
        print(f"Error in menu route: {str(e)}")
        return redirect(url_for('login'))

@app.route('/start_activity', methods=['POST'])
@login_required
def start_activity():
    try:
        data = request.get_json()
        activity_type = data.get('activity_type')
        response = serene_ai.start_activity(activity_type)
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in start_activity: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if not serene_ai:
        return jsonify({
            'error': 'Chat service is currently unavailable. Please check the server logs for more information. 🙏'
        }), 503
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return jsonify({'error': 'Message cannot be empty'}), 400
            
            # Get response from SereneAI
            response = serene_ai.get_response(user_message)
            
            # Save chat history
            chat_entry = ChatHistory(
                user_id=current_user.id,
                message=user_message,
                response=response,
                emotion=serene_ai._analyze_emotion(user_message),
                intent=serene_ai._analyze_intent(user_message)
            )
            
            db.session.add(chat_entry)
            db.session.commit()
            
            return jsonify({'response': response})
            
        except Exception as e:
            print(f"❌ Error in chat route: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred. Please try again in a moment. 💫'}), 500
    
    return render_template('chat.html')

@app.route('/save_chat', methods=['POST'])
@login_required
def save_chat():
    data = request.get_json()
    message = data.get('message')
    response = data.get('response')
    emotion = data.get('emotion')
    intent = data.get('intent')
    
    if not message or not response:
        return jsonify({'error': 'Message and response are required'}), 400
    
    chat_entry = ChatHistory(
        user_id=current_user.id,
        message=message,
        response=response,
        emotion=emotion,
        intent=intent
    )
    
    db.session.add(chat_entry)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/chat_history')
@login_required
def chat_history():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    history = ChatHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ChatHistory.timestamp.desc())\
        .paginate(page=page, per_page=per_page)
    return render_template('chat_history.html', history=history)

@app.route('/search_chat', methods=['POST'])
@login_required
def search_chat():
    query = request.form.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if query:
        history = ChatHistory.query.filter(
            ChatHistory.user_id == current_user.id,
            (ChatHistory.message.ilike(f'%{query}%') | 
             ChatHistory.response.ilike(f'%{query}%'))
        ).order_by(ChatHistory.timestamp.desc())\
         .paginate(page=page, per_page=per_page)
    else:
        history = ChatHistory.query.filter_by(user_id=current_user.id)\
            .order_by(ChatHistory.timestamp.desc())\
            .paginate(page=page, per_page=per_page)
    
    return render_template('chat_history.html', history=history, query=query)

@app.route('/save_journal', methods=['POST'])
@login_required
def save_journal():
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        mood = data.get('mood')
        
        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400
            
        entry = Journal(
            user_id=current_user.id,
            title=title,
            content=content,
            mood=mood
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Journal entry saved successfully'})
    except Exception as e:
        print(f"Error saving journal entry: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"Error starting server: {str(e)}")