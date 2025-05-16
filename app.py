from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from models import db, User

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Define upload folder and allowed file types
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Set up database
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
db_path = os.path.join(instance_path, 'dating.db')

if not os.access(instance_path, os.W_OK):
    raise PermissionError(f"Cannot write to instance directory: {instance_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    return "Welcome to the Dating API"

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not email or not password or not username:
        return jsonify({"error": "Missing fields"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, username=username)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return jsonify({
            "user_id": user.id,
            "username": user.username,
            "token": "mock_token_123"
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/update-profile/<int:user_id>', methods=['POST'])
def update_profile(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json

    user.age = data.get('age', user.age)
    user.gender = data.get('gender', user.gender)
    user.bio = data.get('bio', user.bio)
    user.location = data.get('location', user.location)

    db.session.commit()
    return jsonify({"message": "Profile updated successfully!"})

@app.route('/upload-profile-pic/<int:user_id>', methods=['POST'])
def upload_profile_pic(user_id):
    user = User.query.get_or_404(user_id)

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save the relative path in the DB (e.g., static/uploads/filename.jpg)
        user.profile_pic = filepath
        db.session.commit()

        return jsonify({
            "message": "Profile picture uploaded successfully!",
            "profile_pic_url": f"/{filepath}"
        }), 200

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)
