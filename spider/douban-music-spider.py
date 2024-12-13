from lxml import etree
import requests
import html
from urllib.parse import quote
import json

BASE_OUTPUT_PATH = '/home/user/Desktop/Files/University/G3T1/Big Data/bigHomework/spider_original_data/'

tag_list = ['流行','电影原声','古典','纯音乐','经典']

def getFullURL(tag, number):# must input Chinese in tag, and the code below will use percent encode
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }
    tag = quote(tag)
    full_URL = r"https://music.douban.com/tag/" + tag + r"?start=" + str(number) + r"&type=T"
    response = requests.get(full_URL,headers=headers)
    return response.content


def parseHTML(html_content):
    # 解析HTML
    tree = etree.HTML(html_content)

    # 获取每首歌曲信息
    songs = tree.xpath('//a[@class="nbg"]')
    
    result_list = []
    
    for song in songs:
        # 获取歌曲页面链接
        song_link = song.xpath('./@href')[0]
        
        # 获取图片链接
        img_link = song.xpath('.//img/@src')[0]
        
        # 获取歌曲标题
        title = song.xpath('.//ancestor::td/following-sibling::td//a/text()')[0].strip()
        
        # 获取其他信息
        raw_info = song.xpath('.//ancestor::td/following-sibling::td//p[@class="pl"]/text()')
        raw_info = html.unescape(raw_info[0].strip()) if raw_info else "无信息"
        
        
        result_list.append({
            "song_link":song_link,
            "img_link":img_link,
            "title":title,
            "raw_info":raw_info
            })
        # print(f"歌曲链接: {song_link}")
        # print(f"图片链接: {img_link}")
        # print(f"标题: {title}")
        # print(f"其他信息: {raw_info}")
    return result_list

def getPages(tag, pageNumberStart, pageCount):
    # one page contains 20 items. This argument means number of pages
    page_idx = pageNumberStart
    for i in range(0, pageCount):
        item_idx = page_idx * 20
        html_content = getFullURL(tag, item_idx)
        result_list = parseHTML(html_content)
        
        # write data into JSON file
        with open(BASE_OUTPUT_PATH + tag + '_' + '{:06d}'.format(page_idx) + '.json', 'w') as f:
            json.dump(result_list, f, ensure_ascii=False, indent=4)
        
        page_idx += 1

def isTagListDuplicate():
    tag_set = set(tag_list)
    if len(tag_set) != len(tag_list):
        print("Duplicate tags in tag_list")
        return True
    return False
# main part starts here

if isTagListDuplicate():
    print("Please check tag_list")
    exit(1)
        
getPages(tag_list[-1], 0, 50)
    
    