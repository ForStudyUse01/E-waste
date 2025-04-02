from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from functools import lru_cache, wraps
from templates.AI import EwasteAnalyzer
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Initialize AI analyzer
analyzer = EwasteAnalyzer()

# Ensure upload folder exists
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# User data storage (in a real app, use a database)
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@lru_cache(maxsize=1)
def get_material_chart(materials):
    try:
        fig = plt.figure(figsize=(6, 6))
        plt.pie(materials.values(), labels=materials.keys(), autopct='%1.1f%%')
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()
    except Exception as e:
        logger.error(f"Error generating material chart: {str(e)}")
        return None

@app.route('/')
def home():
    return render_template('index.html', current_page='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        users = load_users()
        user = users.get(email)
        
        if user and check_password_hash(user['password'], password):
            session['user'] = {
                'email': email,
                'name': user['name']
            }
            if 'points' not in session:
                session['points'] = user.get('points', 0)
            return redirect(url_for('home'))
        
        return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        
        users = load_users()
        if email in users:
            return render_template('signup.html', error='Email already registered')
        
        # Remove the points assignment
        users[email] = {
            'name': name,
            'password': generate_password_hash(password, method='pbkdf2:sha256:260000'),
            # Remove points and reward history
        }
        save_users(users)
        
        session['user'] = {
            'email': email,
            'name': name
        }
        # Remove the points session assignment
        flash('Signup successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('signup.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/scan')
@login_required
def scan():
    # Get the reward chart from the analyzer
    reward_chart = analyzer.reward_chart
    return render_template('scan.html', current_page='Scan E-Waste', reward_chart=reward_chart)

@app.route('/centers')
@login_required
def centers():
    return render_template('centers.html', current_page='Recycling Centers')

@app.route('/rewards')
@login_required
def rewards():
    if 'points' not in session:
        session['points'] = 0
    if 'redeemed_rewards' not in session:
        session['redeemed_rewards'] = []
    return render_template('rewards.html', 
                         current_page='Rewards',
                         points=session['points'],
                         redeemed_rewards=session['redeemed_rewards'])

@app.route('/about')
def about():
    return render_template('about.html', current_page='About Us')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Please upload JPG or PNG files only.'}), 400

        # Create uploads directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(filepath)
        logger.info(f"File saved successfully: {filepath}")
        
        try:
            # Analyze image using AI
            analysis_result = analyzer.analyze_device(filepath)
            
            if not analysis_result:
                logger.error("Failed to analyze image")
                return jsonify({'error': 'Failed to analyze image. Please try again.'}), 500
            
            if analysis_result['status'] == 'error':
                return jsonify({
                    'success': False,
                    'error': analysis_result['message'],
                    'reward_chart': analysis_result['reward_chart']
                }), 400
            
            # Format device info for frontend
            device_info = {
                "Device_Type": analysis_result.get('device_type', 'Unknown').capitalize(),
                "Condition": analysis_result.get('condition', 'Unknown').capitalize(),
                "Potential_Points": analysis_result.get('reward', 0),
                "Status": "Pending Approval"
            }
            
            logger.info(f"Successfully processed image: {filename}")
            logger.info(f"Analysis result: {device_info}")
            
            return jsonify({
                'success': True,
                'device_info': device_info,
                'reward_chart': analysis_result['reward_chart'],
                'message': 'Analysis completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return jsonify({'error': f'Failed to analyze image: {str(e)}'}), 500
        finally:
            # Clean up the uploaded file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Cleaned up uploaded file: {filepath}")
            except Exception as e:
                logger.error(f"Error cleaning up file: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/redeem_reward', methods=['POST'])
@login_required
def redeem_reward():
    try:
        data = request.json
        reward_name = data.get('name')
        points_cost = data.get('points')
        
        if 'points' not in session:
            session['points'] = 0
        if 'redeemed_rewards' not in session:
            session['redeemed_rewards'] = []
        
        if session['points'] >= points_cost:
            session['points'] -= points_cost
            session['redeemed_rewards'].append(reward_name)
            
            # Update user's points in the users file
            users = load_users()
            if session['user']['email'] in users:
                users[session['user']['email']]['points'] = session['points']
                save_users(users)
            
            return jsonify({
                'success': True,
                'message': f'Successfully redeemed {reward_name}!',
                'points': session['points']
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Not enough points! Need {points_cost} points.',
                'points': session['points']
            }), 400
    except Exception as e:
        logger.error(f"Error in redeem_reward: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/add_points', methods=['POST'])
@login_required
def add_points():
    try:
        if 'points' not in session:
            session['points'] = 0
        points_to_add = request.json.get('points', 150)
        session['points'] += points_to_add
        
        # Update user's points in the users file
        users = load_users()
        if session['user']['email'] in users:
            users[session['user']['email']]['points'] = session['points']
            save_users(users)
        
        return jsonify({
            'success': True,
            'message': f'Added {points_to_add} points!',
            'points': session['points']
        })
    except Exception as e:
        logger.error(f"Error in add_points: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/approve_device', methods=['POST'])
@login_required
def approve_device():
    try:
        data = request.json
        device_id = data.get('device_id')
        status = data.get('status')  # 'approved' or 'rejected'
        notes = data.get('notes', '')
        
        # In a real application, you would update this in a database
        # For now, we'll just return a success response
        return jsonify({
            'success': True,
            'message': f'Device {status} successfully',
            'notes': notes
        })
    except Exception as e:
        logger.error(f"Error in approve_device: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/confirm_collection', methods=['POST'])
@login_required
def confirm_collection():
    try:
        data = request.json
        device_id = data.get('device_id')
        points = data.get('points', 0)
        
        # Update user's points
        if 'points' not in session:
            session['points'] = 0
        session['points'] += points
        
        # Update user's points in the users file
        users = load_users()
        if session['user']['email'] in users:
            users[session['user']['email']]['points'] = session['points']
            save_users(users)
        
        return jsonify({
            'success': True,
            'message': f'Device collected successfully. {points} points added to your account!',
            'points': session['points']
        })
    except Exception as e:
        logger.error(f"Error in confirm_collection: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 