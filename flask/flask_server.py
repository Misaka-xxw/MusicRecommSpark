# use async IO to call shell command
import asyncio
import uuid
import time
import json
import urllib.parse
from io import BytesIO
import requests
import traceback
import imghdr
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, request, jsonify, send_file, redirect, send_from_directory, session
from flask_cors import CORS, cross_origin

from functools import wraps

PERSONAL_RATINGS_CACHE_PATH = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/personal_ratings_cache"
MUSIC_DATA_CONFIG_JSON_PATH = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/dataset/musicData.json"
DATABASE = '/home/ubuntu/Desktop/BigData/MusicRecommSpark/flask/users.db'

# Init database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login.html?msg=login_required')   
        return f(*args, **kwargs)
    return decorated_function
# Load music dataset
with open (MUSIC_DATA_CONFIG_JSON_PATH, "r") as file:
    CONFIG_JSON = json.load(file)


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
CORS(app)

# Dict to store results
results = {}


async def run_command(command):
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()


def execute_spark_submit(task_uuid: str,
                         personal_ratings_path: str = "/hadoop/movie_recommend/personalRatings.dat",
                         training_data_path: str = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/dataset/",
                         bestRank: int = 10, bestLambda: int = 5, bestNumIter: int = 10):
    
    # set training_data_path to "/home/ubuntu/Desktop/BigData/MusicRecommSpark/dataset_movie_demo/" to run movie demo data
    # This recommendation will always output 20 recommended movies/msuics, and this is unchangeable.
    command = ["/hadoop/spark-2.4.5-bin-hadoop2.7/bin/spark-submit", "--class", "MovieLensALS",
               "/hadoop/Spark_Recommend-1.0-SNAPSHOT.jar", training_data_path,
               personal_ratings_path, str(bestRank), str(bestLambda), str(bestNumIter)]

    
    results[task_uuid] = {"status": "running",
                        "start_timestamp": time.time()}
    print(results)

    def background_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_time = time.time()
        output, error = loop.run_until_complete(run_command(command))
        elapsed_time = time.time() - start_time
        results[task_uuid] = {
            "status": "completed",
            "stdout": output,
            "stderr": error,
            "elapsed_time": elapsed_time
        }
        loop.close()

    # Run the task in a separate thread
    import threading

    thread = threading.Thread(target=background_task)
    thread.start()

    return "SUBMITTED"


@app.route('/apis/v1/start-task', methods=['POST'])
@cross_origin(origin='*')
@login_required
# only allow application/json content type
def start_task():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content type must be application/json"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    personal_ratings_data = data['personal_ratings']
    dat_file = ''
    for item in personal_ratings_data:
        dat_line = f"{item['user_id']}::{item['movie_id']}::{item['rating']}::{item['timestamp']}\n"
        dat_file += dat_line

    # generate UUID here
    task_id = str(uuid.uuid4()) # The original return type is uuid.UUID, but it is not JSON serializable.
    # Save personal ratings file, used in spark.
    with open(f"{PERSONAL_RATINGS_CACHE_PATH}/{task_id}.dat", "w") as file:
        file.write(dat_file)
    excute_result = execute_spark_submit(task_uuid = task_id, personal_ratings_path=f"{PERSONAL_RATINGS_CACHE_PATH}/{task_id}.dat")
    if excute_result != "SUBMITTED":
        return jsonify({"error": "Failed to submit the task"}), 500
    

    return jsonify({"task_id": task_id})


@app.route('/apis/v1/get-result/<task_id>', methods=['GET'])
@cross_origin(origin='*')
@login_required
def get_result(task_id):
    if results[task_id]['status'] == 'running':
        return jsonify({"status": "running",
                        "start_timestamp": results[task_id]['start_timestamp']})
    elif results[task_id]['status'] == 'completed':
        data = split_stdout(results[task_id]['stdout'])
        return jsonify({"status": "completed",
                        "stdout": results[task_id]['stdout'],
                        "stderr": results[task_id]['stderr'],
                        "data": data,
                        "elapsed_time": results[task_id]['elapsed_time']})   
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/apis/v1/delete-result/<task_id>', methods=['DELETE'])
@cross_origin(origin='*')
@login_required
def delete_result(task_id):
    if results[task_id]['status'] == 'completed':
        del results[task_id]
        return jsonify({"status": "deleted"})
    elif results[task_id]['status'] == 'running':
        return jsonify({"error": "Task is still running"}), 400
    else:
        return jsonify({"error": "Task not found"}), 404
    
# @app.route('/apis/v1/get-musics-', methods=['POST'])
# @cross_origin(origin='*')
# def get_musics_urls():
#     if request.content_type != 'application/json':
#         return jsonify({"error": "Content type must be application/json"}), 400

#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "Invalid JSON"}), 400

    # music_ids = data['music_ids']
    # music_urls = {}
    # for music_id in music_ids:
    #     music_urls[music_id] = f"https://music.163.com/song/media/outer/url?id={music_id}.mp3"
    # return jsonify(music_urls)
    
@app.route('/apis/v1/get-musics-count', methods=['GET'])
@cross_origin(origin='*')
@login_required
def get_musics_count():
    return jsonify({"max_id":CONFIG_JSON['max_id']})

@app.route('/apis/v1/get-musics-info', methods=['POST'])
@cross_origin(origin='*')
@login_required
def get_musics_info():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content type must be application/json"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    music_ids = data
    if not all(isinstance(music_id, int) for music_id in music_ids):
        return jsonify({"error": "All music IDs must be integers"}), 400

    music_info = {}
    for music_id in music_ids:
        music_detail = CONFIG_JSON[str(music_id)]
        if music_detail:
            music_info[str(music_id)] = music_detail
        else:
            music_info[str(music_id)] = "Music ID not found"

    return jsonify(music_info)

# css and js static resources
@app.route('/css/element-ui.css', methods=['GET'])
@cross_origin(origin='*')
def get_element_ui_css():
    CSS_PATH_ELEMENT_UI = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/css/element-ui.css"
    return send_file(CSS_PATH_ELEMENT_UI, mimetype='text/css')

@app.route('/css/vue.js', methods=['GET'])
@cross_origin(origin='*')
def get_vue_js():
    JS_PATH_VUE = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/css/vue.js"
    return send_file(JS_PATH_VUE, mimetype='text/javascript')

@app.route('/css/index.js', methods=['GET'])
@cross_origin(origin='*')
def get_index_js():
    JS_PATH_INDEX = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/css/index.js"
    return send_file(JS_PATH_INDEX, mimetype='text/javascript')

@app.route('/css/my_func.js', methods=['GET'])
@cross_origin(origin='*')
def get_my_func_js():
    JS_PATH_INDEX = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/css/my_func.js"
    return send_file(JS_PATH_INDEX, mimetype='text/javascript')

@app.route('/css/fonts/element-icons.woff', methods=['GET'])
@cross_origin(origin='*')
def get_element_icons_woff():
    WOFF_PATH_ELEMENT_ICONS = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/css/element-icons.woff"
    return send_file(WOFF_PATH_ELEMENT_ICONS)

@app.route('/css/fonts/element-icons.ttf', methods=['GET'])
@cross_origin(origin='*')
def get_element_icons_ttf():
    TTF_PATH_ELEMENT_ICONS = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/css/element-icons.ttf"
    return send_file(TTF_PATH_ELEMENT_ICONS)

@app.route('/static/<filename>', methods=['GET'])
@cross_origin(origin='*')
def get_static_files(filename):
    print(filename)
    STATIC_PATH = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/static"
    return send_from_directory(STATIC_PATH, filename)

# HTML pages in website
@app.route('/recommend.html', methods=['GET'])
@cross_origin(origin='*')
@login_required
def get_recommend_page():
    HTML_PATH_RECOMMEND = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/recommend.html"
    return send_file(HTML_PATH_RECOMMEND)

@app.route('/', methods=['GET'])
@cross_origin(origin='*')
def index():
    return redirect('/index.html')

@app.route('/index.html', methods=['GET'])
@cross_origin(origin='*')
def get_index_page():
    HTML_PATH_INDEX = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/index.html"
    return send_file(HTML_PATH_INDEX)

@app.route('/login.html', methods=['GET'])
@cross_origin(origin='*')
def get_login_page():
    HTML_PATH_LOGIN = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/view/login.html"
    return send_file(HTML_PATH_LOGIN)

def getDoubanImage(douban_url):
    print(douban_url)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'}
    MAX_RETRIES = 3
    retries = 0
    while retries < MAX_RETRIES:
        response = requests.get(douban_url, headers=headers)
        if response.status_code == 200:
            content = response.content
            image_file_suffix = douban_url.split('.')[-1]
            mimetype = f"image/jpeg" if image_file_suffix == "jpg" else f"image/{image_file_suffix}"
            return 200, content, mimetype
        else:
            retries = retries+1
    return 500, False, False
# proxy for douban image (to bypass cross-origin issue)
@app.route('/apis/v1/get-image/<path:encoded_url>', methods=['GET'])
@cross_origin(origin='*')
@login_required
def get_image(encoded_url):
        decoded_url = urllib.parse.unquote(encoded_url)
        status, content, mimetype = getDoubanImage(decoded_url)
        if status == 200:
            return send_file(BytesIO(content),mimetype=mimetype)
        else:
            return jsonify({"error":"image fetch error."}), 400


def split_stdout(s: str) -> list[dict]:
    """Parsing stdout as an array of dictionaries"""
    lines = s.split("\n")
    res = []
    for i in range(2, len(lines)):
        word = lines[i].split(":")
        if len(word) > 2:
            res.append({'user_id': word[0], 'movie_id': word[1], 'rating': word[2], 'name': word[3]})
    # Sort the result by rating in descending order
    res.sort(key=lambda x: float(x['rating']), reverse=True)
    return res

# Account register and login
@app.route('/apis/v1/register', methods=['POST'])
@cross_origin(origin='*')
def register():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content type must be application/json",
                        "status": "error"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON", "status": "error"}), 400

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"message": "Username, password and email are required",
                        "status": "error"}), 400

    hashed_password = generate_password_hash(password)

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"message": "User already exists",
                        "status": "error"}), 400

    return jsonify({"message": "User registered successfully",
                    "status": "success"}), 201

@app.route('/apis/v1/login', methods=['POST'])
@cross_origin(origin='*')
def login():
    if request.content_type != 'application/json':
        return jsonify({"message": "Content type must be application/json",
                        "status":"error"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON",
                        "status":"error"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required",
                        "status":"error"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

    if row is None or not check_password_hash(row[0], password):
        return jsonify({"message": "Invalid username or password",
                        "status":"error"}), 400

    session['username'] = username
    return jsonify({"message": "Logged in successfully",
                    "status":"success"}), 200

@app.route('/apis/v1/logout', methods=['POST'])
@cross_origin(origin='*')
@login_required
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully",
                    "status":"success"}), 200
# test APIs
@app.route('/apis/v1/test-login-required', methods=['GET'])
@cross_origin(origin='*')
@login_required
def test_login_required():
    return jsonify({"message": "You are logged in",
                    "status":"success"}), 200
if __name__ == "__main__":
    app.run(debug=True)
