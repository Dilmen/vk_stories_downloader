import os
import sys
import json
from datetime import datetime
import wget
import time
import random

token = open("token").read().replace("\n","")

url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'

toke.close()

if len(sys.argv) == 1:
    file = wget.download(url, out=f'{datetime.now().strftime("%d-%m-%Y_%H:%M")}.json')
else:
    file = sys.argv[1]

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def print_info_image(block):
    ouput = f'stories/{block.get("owner_id")}/{block.get("id")}/'
    create_dir(ouput)
    for i in block.get("photo").get("sizes"):
        print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
        
        wget.download(i.get("url"), out=ouput)
    
    print()
        

def print_info_video(block):
    ouput = f'stories/{block.get("owner_id")}/{block.get("id")}/'
    create_dir(ouput)
    get_video_image(block.get("image"), "Prewiew", ouput)
    get_video_image(block.get("first_frame"), "First frame", ouput)
    
    for i in block.get("files"):
        print(f'{i} - {block.get("files").get(i)}')
        
        wget.download(block.get("files").get(i), out=ouput)
        print()
    
    print()

def get_video_image(block, name, path):
    path = f'{path}/{name}'
    create_dir(path)
    for i in block:
        
        print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
        
        wget.download(i.get("url"), out=path)
        print()
    print()

def print_info_stories(block):
    print(f'id - {block.get("id")} | type - {block.get("type")} | date - {datetime.fromtimestamp(block.get("date")).strftime("%m/%d/%Y, %H:%M:%S")}')

def stories_from_group(block):
    for i in block:
        print(i.get("name"))
        stories_mod(i)

def stories_mod(datas):
    for stories in datas.get("stories"):
        time.sleep(random.randint(1,10))
        print_info_stories(stories)
        if stories.get("type") == "photo":
            print_info_image(stories)
        else:
            print_info_video(stories.get("video"))

def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    
with open(file, "r") as read_file:
    data = json.load(read_file)

for datas in data.get("response").get("items"):
    if datas.get("type") == "stories":
        print(f'name - {datas.get("name")}')
        for stories in datas.get("stories"):
            time.sleep(random.randint(1,10))
            print_info_stories(stories)
            if stories.get("type") == "photo":
                print_info_image(stories)
            else:
                print_info_video(stories.get("video"))
    else:
        stories_from_group(datas.get("grouped"))
