import requests
import time
import json

# Convert personalRatings.dat-1 to JSON format
personal_ratings_data = [
    {"user_id": 1, "movie_id": 3, "rating": 3, "timestamp": 978301968},
    {"user_id": 1, "movie_id": 4, "rating": 4, "timestamp": 978300275},
    {"user_id": 1, "movie_id": 5, "rating": 5, "timestamp": 978824291},
    {"user_id": 1, "movie_id": 6, "rating": 3, "timestamp": 978302268},
    {"user_id": 1, "movie_id": 7, "rating": 5, "timestamp": 978302039},
    {"user_id": 1, "movie_id": 8, "rating": 5, "timestamp": 978300719},
    {"user_id": 2, "movie_id": 7, "rating": 7, "timestamp": 978302037},
    {"user_id": 2, "movie_id": 8, "rating": 8, "timestamp": 978300718},
    {"user_id": 3, "movie_id": 1, "rating": 5, "timestamp": 978300760},
    {"user_id": 3, "movie_id": 2, "rating": 3, "timestamp": 978302109},
    {"user_id": 4, "movie_id": 7, "rating": 5, "timestamp": 178302039},
    {"user_id": 4, "movie_id": 8, "rating": 5, "timestamp": 178300719}
]

# Submit the request to start the task
response = requests.post(
    'http://127.0.0.1:5000/start-task',
    json={"personal_ratings": personal_ratings_data},
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    task_id = response.json().get("task_id")
    print(f"Task submitted successfully. Task ID: {task_id}")

    # Poll the status every second
    while True:
        status_response = requests.get(f'http://127.0.0.1:5000/get-result/{task_id}')
        status_data = status_response.json()

        if status_data.get("status") == "completed":
            print("Task completed.")
            print("Output:", status_data.get("stdout"))
            print("Error:", status_data.get("stderr"))
            print("Elapsed Time:", status_data.get("elapsed_time"))
            break
        elif status_data.get("status") == "running":
            print("Task is still running...")
        else:
            print("Error:", status_data.get("error"))
            break

        time.sleep(1)
else:
    print("Failed to submit the task:", response.json().get("error"))