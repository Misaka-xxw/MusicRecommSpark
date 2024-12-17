# 此处，由merged JSON生成target的三个dat文件，使用MovieLens数据集的格式
# 生成的三个dat文件分别为：ratings.dat, movies.dat, personalRatings.dat

import json
import os
import random
import datetime

INPUT_JSON_PATH = '/home/ubuntu/Desktop/BigData/MusicRecommSpark/spider/merged_data.json'

OUTPUT_DIRECTORY = '/home/ubuntu/Desktop/BigData/MusicRecommSpark/dataset'

INPUT_POINTER = open(INPUT_JSON_PATH, 'r')
OUTPUT_RATINGS_POINTER = open(os.path.join(OUTPUT_DIRECTORY, 'ratings.dat'), 'w')
OUTPUT_MOVIES_POINTER = open(os.path.join(OUTPUT_DIRECTORY, 'movies.dat'), 'w')
OUTPUT_MUSIC_DATA_POINTER = open(os.path.join(OUTPUT_DIRECTORY, 'musicData.json'), 'w')

random.seed(20241215)
# 读取merged JSON文件
merged_data = json.load(INPUT_POINTER)

# 生成movies.dat文件 and musicData.json
movie_id_idx = 1
music_data = {}
for movie in merged_data:
    OUTPUT_MOVIES_POINTER.write(str(movie_id_idx) + '::' + movie['title'] + ' (' + movie['date'][0:4] + ')'+'::' + movie['tag'] + '\n')
    music_data[str(movie_id_idx)] = {"name": movie['title'], "year": movie['date'][0:4], "tag": movie['tag'],
                                     "img_url": movie['img_link'], "click_url": movie['song_link'], "singer": movie['singer']}  
    movie_id_idx += 1

music_data['max_id'] = movie_id_idx - 1
json.dump(music_data, OUTPUT_MUSIC_DATA_POINTER, indent=4, ensure_ascii=False)
OUTPUT_MOVIES_POINTER.close()

# 生成ratings.dat文件
used_movie_id = set()

user_id_idx = 1
for repeat in range(1000):
    for moviesPerUser in range(50):
        movie_id = random.randint(1, movie_id_idx - 1) # randint use range [a, b]
        used_movie_id.add(movie_id)
        rating = random.randint(1, 5)
        start_timestamp = int(datetime.datetime(2023, 1, 1).timestamp())
        end_timestamp = int(datetime.datetime(2024, 12, 11).timestamp())
        timestamp = random.randint(start_timestamp, end_timestamp)
        OUTPUT_RATINGS_POINTER.write(f"{user_id_idx}::{movie_id}::{rating}::{timestamp}\n")
    user_id_idx += 1

OUTPUT_RATINGS_POINTER.close()

unused_movie_ids = set(range(1, movie_id_idx)) - used_movie_id

print("If the below line is not empty set, which means some movies are not included in the ratings.dat.")
print("Missing movies will cause the ALS model to fail.")
print(unused_movie_ids)



