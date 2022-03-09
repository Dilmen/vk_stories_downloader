import os
import sys
import json
from datetime import datetime
import wget
import time
import random
import re

token = open("token").read().replace("\n","")

url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'

if len(sys.argv) == 1:
    file = wget.download(url, out=f'{datetime.now().strftime("%d-%m-%Y_%H:%M")}.json')
else:
    file = sys.argv[1]

def chage_datechage(path_file, modTime):
    os.utime(path_file, (modTime, modTime))
    
    t = ""
    for i in path_file.split("/")[0:-1]:
        t += i + "/"
        os.utime(t, (modTime, modTime))

def print_info_image(block, user):
    ouput = f'stories/{user} ({block.get("owner_id")})/{block.get("id")}/'
    create_dir(ouput)
    for i in block.get("photo").get("sizes"):
        print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
        
        file_stories = wget.download(i.get("url"), out=ouput)

        chage_datechage(file_stories, block.get("photo").get("date"))
        
        
        print()
    
    print()
        
def print_info_video(block, user):
    ouput = f'stories/{user} ({block.get("owner_id")})/{block.get("id")}/'
    create_dir(ouput)
    get_video_image(block.get("image"), "Prewiew", ouput, block.get("date"))
    get_video_image(block.get("first_frame"), "First frame", ouput, block.get("date"))
    
    for i in block.get("files"):
        print(f'{i} - {block.get("files").get(i)}')
        
        file_stories = wget.download(block.get("files").get(i), out=ouput)
        chage_datechage(file_stories, block.get("date"))
        
        print()
    
    print()

def get_video_image(block, name, path, date):
    path = f'{path}/{name}'
    create_dir(path)
    for i in block:
        
        print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
        
        file_stories = wget.download(i.get("url"), out=f'{path}/{i.get("width")}x{i.get("height")}.jpg')
        
        chage_datechage(file_stories, date)
        
        print()
    print()

def print_info_stories(block):
    print(f'id - {block.get("id")} | type - {block.get("type")} | date - {datetime.fromtimestamp(block.get("date")).strftime("%m/%d/%Y, %H:%M:%S")}')

def stories_from_group(block):
    for i in block:
        print(i.get("name"))
        stories_mod(i)

def stories_mod(datas):
    user = del_specific_chapters(datas.get("name"))
    for stories in datas.get("stories"):
        time.sleep(random.randint(1,10))
        print_info_stories(stories)
        if stories.get("type") == "photo":
            print_info_image(stories, user)
        else:
            print_info_video(stories.get("video"), user)

def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def del_specific_chapters(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)

with open(file, "r") as read_file:
    data = json.load(read_file)

user = ""
for datas in data.get("response").get("items"):
    if datas.get("type") == "stories":
        print(f'name - {datas.get("name")}')
        user = del_specific_chapters(datas.get("name"))
        for stories in datas.get("stories"):
            time.sleep(random.randint(1,10))
            print_info_stories(stories)
            if stories.get("type") == "photo":
                print_info_image(stories, user)
            else:
                print_info_video(stories.get("video"), user)
    else:
        stories_from_group(datas.get("grouped"))
