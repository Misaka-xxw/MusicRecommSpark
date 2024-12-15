# use async IO to call shell command
import asyncio
import uuid
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

PERSONAL_RATINGS_CACHE_PATH = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/personal_ratings_cache"
MUSIC_DATA_CONFIG_JSON_PATH = "/home/ubuntu/Desktop/BigData/MusicRecommSpark/dataset/musicData.json"

with open (MUSIC_DATA_CONFIG_JSON_PATH, "r") as file:
    CONFIG_JSON = json.load(file)

app = Flask(__name__)
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
def get_result(task_id):
    if results[task_id]['status'] == 'running':
        return jsonify({"status": "running",
                        "start_timestamp": results[task_id]['start_timestamp']})
    elif results[task_id]['status'] == 'completed':
        return jsonify({"status": "completed",
                        "stdout": results[task_id]['stdout'],
                        "stderr": results[task_id]['stderr'],
                        "elapsed_time": results[task_id]['elapsed_time']})   
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/apis/v1/delete-result/<task_id>', methods=['DELETE'])
@cross_origin(origin='*')
def delete_result(task_id):
    if results[task_id]['status'] == 'completed':
        del results[task_id]
        return jsonify({"status": "deleted"})
    elif results[task_id]['status'] == 'running':
        return jsonify({"error": "Task is still running"}), 400
    else:
        return jsonify({"error": "Task not found"}), 404
    
@app.route('/apis/v1/get-musics-imgurls', methods=['POST'])
@cross_origin(origin='*')
def get_musics_urls():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content type must be application/json"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # music_ids = data['music_ids']
    # music_urls = {}
    # for music_id in music_ids:
    #     music_urls[music_id] = f"https://music.163.com/song/media/outer/url?id={music_id}.mp3"
    # return jsonify(music_urls)
    
@app.route('/apis/v1/get-musics-count', methods=['GET'])
@cross_origin(origin='*')
def get_musics_count():
    return jsonify({"max_id":CONFIG_JSON['max_id']})

@app.route('/apis/v1/get-musics-info', methods=['GET'])
@cross_origin(origin='*')
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

if __name__ == "__main__":
    app.run(debug=True)
