# use async IO to call shell command
import asyncio

import uuid
import time
from flask import Flask, request, jsonify

# app = Flask(__name__)

# Dict to store result
results = {}

async def run_command(command):
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()

def execute_spark_submit():
    command = ["/hadoop/spark-2.4.5-bin-hadoop2.7/bin/spark-submit", "--class", "MovieLensALS",
               "/hadoop/Spark_Recommend-1.0-SNAPSHOT.jar", "/hadoop/movie_recommend/",
               "/hadoop/movie_recommend/personalRatings.dat", "10", "5", "10"]

    task_id = str(uuid.uuid4())
    results[task_id] = {"status": "running"}

    async def background_task():
        start_time = time.time()
        output, error = await run_command(command)
        elapsed_time = time.time() - start_time

        results[task_id] = {
            "status": "completed",
            "output": output,
            "error": error,
            "elapsed_time": elapsed_time
        }

    asyncio.create_task(background_task())
    return task_id

# @app.route('/start-task', methods=['POST'])
# def start_task():
#     task_id = execute_spark_submit()
#     return jsonify({"task_id": task_id})

# @app.route('/get-result/<task_id>', methods=['GET'])
# def get_result(task_id):
#     result = results.get(task_id, {"status": "not found"})
#     return jsonify(result)

# if __name__ == "__main__":
#     app.run(debug=True)

async def main():
    task_id = execute_spark_submit()
    print(f"Task ID: {task_id}")
    await asyncio.sleep(60)  # Simulate waiting for the task to complete
    result = results.get(task_id, {"status": "not found"})
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())