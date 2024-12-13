import os
import json

# This python is used to merge all JSON files under /home/user/Desktop/Files/University/G3T1/Big Data/bigHomework/spider_original_data,
# and output a single JSON
# Please note the missing value under the key "raw_info" in the JSON file
input_directory = '/home/user/Desktop/Files/University/G3T1/Big Data/bigHomework/spider_original_data'
output_file = '/home/user/Desktop/Files/University/G3T1/Big Data/bigHomework/spider/merged_data.json'

merged_data = []

for filename in os.listdir(input_directory):
    if filename.endswith('.json'):
        file_path = os.path.join(input_directory, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
            
            for item in data:
                parsed_data = {}
                parsed_data['song_link'] = item['song_link']
                parsed_data['img_link'] = item['img_link']
                parsed_data['title'] = item['title']
                parsed_data['tag'] = filename.split('_')[0]
                
                raw_parse = item['raw_info'].split(' / ')
                
                if len(raw_parse) > 0:
                    parsed_data['singer'] = raw_parse[0]
                else:
                    parsed_data['singer'] = 'NULL'
                
                if len(raw_parse) > 1:
                    date = raw_parse[1]
                    date_parts = date.split('-')
                    year = date_parts[0]
                    month = date_parts[1] if len(date_parts) > 1 else '01'
                    day = date_parts[2] if len(date_parts) > 2 else '01'
                    
                    if len(month) == 1:
                        month = '0' + month
                    if len(day) == 1:
                        day = '0' + day
                    
                    parsed_data['date'] = f"{year}-{month}-{day}"
                else:
                    parsed_data['date'] = 'NULL'
                
                if len(raw_parse) >2: #专辑or单曲
                    parsed_data['music_type'] = raw_parse[2]
                else:
                    parsed_data['music_type'] = 'NULL'
                    
                if len(raw_parse) > 3:# CD or 电子版
                    parsed_data['medium'] = raw_parse[3]
                else:
                    parsed_data['medium'] = 'NULL'
                    
                if len(raw_parse) > 4: # 轻音乐 or 原声 or xxx 此处和tag可能一样，可能不一样
                    parsed_data['music_type2'] = raw_parse[4]
                else:
                    parsed_data['music_type2'] = 'NULL'
                
                merged_data.append(parsed_data)

with open(output_file, 'w') as output:
    json.dump(merged_data, output, ensure_ascii=False, indent=4)
    
    