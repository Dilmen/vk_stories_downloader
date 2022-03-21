#!/usr/bin/env python3
import os
import urllib.request
import progressbar as pb
import re
import json
from datetime import datetime
import sys
import time
import socket
import logging
import http
import argparse

version = "0.2.6"

def download_file(url, path, title=None, attempt=0):
    if attempt >= 10:
        return
    
    if title == None:
        title = os.path.splitext(url)
        title = title[0].split("/")[-1] + title[1].split("?")[0]
    
    file_stories = path + title
    
    try:
        
        if os.path.exists(file_stories):
            if check_in_completed(path, title):
               return
            else:
                r = urllib.request.urlopen(url)
                file_size = r.getheader('Content-Length')
                
                if os.stat(file_stories).st_size == int(file_size):
                    completed(path, title)
                    return
        
        timeout = 10
        
        socket.setdefaulttimeout(timeout)
        urllib.request.urlretrieve(url, file_stories, reporthook=download_progress)
        download_progress.progress_bar.finish()
        completed(path, title)
        
        if arguments.dump:
           return 
        
        for i in range(sleep):
            sys.stdout.write(f'\rZzzz {sleep - i}   ')
            time.sleep(1)
            if i + 1 == sleep: sys.stdout.write(f'\r                   ')            
            sys.stdout.flush()
        
        return file_stories
        
    except urllib.error.HTTPError as e:
        print_log(f'\nOps! Error : {e}')
    except urllib.error.URLError as e:
        print_log(f'\nOps! Error : {e}')
    except socket.timeout as e:
        print_log(f'\nOps! Error : {e}')
        download_file(url, path, title, attempt + 1)
    except http.client.HTTPException as e:
        print_log(f'\nOps! Error : {e}')
        download_file(url, path, title, attempt + 1)
    except OSError as e:
        print_log(f'\nOps! Error : {e}')
        download_file(url, path, title, attempt + 1)
    
    return

def download_progress(blocks_read, block_size, total_size):
    # print(locals())
    if blocks_read == 0:
        widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.ETA(), ' ',
                   pb.FileTransferSpeed()]
        download_progress.progress_bar = pb.ProgressBar(
            widgets=widgets, maxval=total_size + block_size).start()

    download_progress.progress_bar.update(blocks_read * block_size)

def change_modification_date(path, modTime):
    if not os.path.exists(path):
        return
    
    os.utime(path, (modTime, modTime))
    
    t = ""
    
    for i in path.split("/")[0:-1]:
        t += i + "/"
        os.utime(t, (modTime, modTime))
        
def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def del_specific_chapters(name):
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(".","_")

def bar_gen(f):
    t = "["
    
    for i in range(1,11):
        t += "#" if i*10 <= f else "_"
    
    return f'{t}]'

def print_count(count):
    t = (((count_t - count) / count_t) * 100)
    print_log(f'\n  Remain stories - {count} | Completed on {t}% {bar_gen(t)} {str(t).split(".")[0]}%', end="\n\n")

def count_stories(datas):
    count = 0
    
    adsC = 0
    friends = 0
    public = 0
    
    if ads and datas.get("ads") != None:
        for i in datas.get("ads").get("items"):
            count += len(i.get("stories"))
            adsC += len(i.get("stories"))
    
    for i in datas.get("items"):
        if i.get("stories") != None:
            count += len(i.get("stories"))
            friends += len(i.get("stories"))
        if i.get("type") == "community_grouped_stories":
            for j in i.get("grouped"):
                count += len(j.get("stories"))
                public += len(j.get("stories"))
    
    #for i in datas.get("items"):
    
    #if datas.get("items")[datas.get("count") - 1].get("grouped") != None:
        #for i in datas.get("items")[datas.get("count") - 1].get("grouped"):
            #count += len(i.get("stories"))
    
    return count, adsC, friends, public

def print_info_stories(block):
    print_log(f'id - {block.get("id")} | type - {block.get("type")} | date - {datetime.fromtimestamp(block.get("date")).strftime("%d/%m/%Y, %H:%M:%S")}')

def stories_mod(datas, user, count):  
    for stories in datas.get("stories"):
        print_info_stories(stories)
        
        if stories.get("type") == "photo" and download_type in ["image", "all"]:
            download_stories(stories, "photo", user)
        elif stories.get("type") == "video":
            download_stories(stories, "video", user)
        
        count -= 1
        print_count(count)
        
    return count

def download_stories(block, typu, user):
    output = f'stories/{user} ({block.get("owner_id")})/{block.get("id")}/'
    create_dir(output)
    date = block.get("date")
    
    if typu == "photo":
        block_t = block.get("photo").get("sizes")
        
        if quality == "max":
            block_t = block_t.pop()
        elif quality == "low":
            block_t = block_t[0]
        
        ar = []
        
        if block_t != block.get("photo").get("sizes"):
            print_log(f'size - {block_t["width"]}x{block_t["height"]} | url - {block_t["url"]}')
            ar.append(download_file(block_t["url"], output))            
        else:
            for i in block_t:
                print_log(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
                ar.append(download_file(i.get("url"), output))  
        
        for i in ar:
            if i != None:
                change_modification_date(i, date)
                
    elif typu == "video":
        if download_type in ["video", "all"]:
            v = list(block.get("video").get("files").items())
            
            if len(v) > 1:
                print_log("(⌐■_■) ∠( ᐛ 」∠)_")
            else:
                print_log(f'size - {v[0][0]} | url - {v[0][1]}')
                ar = download_file(v[0][1], output)
                
                if ar != None:
                    change_modification_date(ar, date)
                    
        if preview:
            download_preview(block.get("video"), "image", output, date)
            download_preview(block.get("video"), "first_frame", output, date)

def download_preview(block, name, output, date):
    ar = []
    
    if block.get(name) != None:
        for i in block.get(name):
            if "mycdn.me" in i.get("url"):
                print_log("∠( ᐛ 」∠)_")
                continue
            
            print_log(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
            ar.append(download_file(i.get("url"), output, f'{name} {i.get("width")}x{i.get("height")}.jpg'))
    
    for i in ar:
        if i != None:
            change_modification_date(i, date)

def print_log(string, end="\n"):
    if logs:
        logging.info(string.replace("\n","").strip())
    print(string, end=end)

def completed(path, name):
    f = open(f'{path}.completed', "a+")
    f.write(f'{name}\n')
    f.close()

def check_in_completed(path, name):
    if os.path.exists(f'{path}.completed'):
        f = open(f'{path}.completed', "r")
        lines = f.readlines()
        f.close()
        
        for i in lines:
            if i.replace("\n","") == name:
                return True
    
    return False

parser = argparse.ArgumentParser(description='Script to download stories fron VK')
parser.add_argument('-f', type=str, dest='file', help='get stoies from file')
parser.add_argument('-v', action='store_true', dest='video', help='download only video')
parser.add_argument('-i', action='store_true', dest='image', help='download only image')
parser.add_argument('--preview', action='store_true', dest='preview', help='download video preview')
parser.add_argument('-q', type=str, default="max", dest='quality', choices=('all', 'low', 'max'), help='select quality (default: max)')
parser.add_argument('--ads', action='store_true', dest='ads', help='download ads stories')
parser.add_argument('--sleep',default=3, dest='sleep', help='Provide sleep timer', type=int)
parser.add_argument('--log', action='store_true', dest='log', help='Write to log file')
parser.add_argument('--dump', action='store_true', dest='dump', help='download only dump and exit')
parser.add_argument('--version', action='version', version="%(prog)s " + version)

try:
    token = open("token").read().replace("\n","").strip()
except FileNotFoundError as e:
    print(f'Error - {e}')
    sys.exit()
    
arguments = parser.parse_args()
url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'
ads = arguments.ads
preview = arguments.preview
quality = arguments.quality
sleep = arguments.sleep
logs = arguments.log

if arguments.video:
    download_type = "video"
elif arguments.image:
    download_type = "image"
else:
    download_type = "all"

if arguments.file == None:
    json_file = f'{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.json'
    download_file(url, "", json_file)
    
    if arguments.dump:
        sys.exit()
    
else:
    json_file = arguments.file
    
if logs:
    create_dir("logs")
    logging.basicConfig(filename=f'logs/{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.log', encoding='utf-8', format='%(asctime)s ➤➤➤ %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
    logging.info(" ".join(sys.argv))

try:
    with open(json_file, "r", encoding='utf-8') as read_file:
        data = json.load(read_file)
except FileNotFoundError as e:
    print_log(f'Error - {e}')
    sys.exit()

count, adsC, friends, public = count_stories(data.get("response"))
count_t = count

print_log(f'    Count stories: friends - {friends} | public - {public} | ads - {adsC} | all - {count_t}')
time.sleep(5)

for datas in data.get("response").get("items"):
    if datas.get("type") == "stories":
        print_log(f'            name - {datas.get("name")}', end="\n\n")
        user = del_specific_chapters(datas.get("name"))
        count = stories_mod(datas, user, count)
    else:
        for grouped in datas.get("grouped"):
            print_log(f'            name - {grouped.get("name")}', end="\n\n")
            user = del_specific_chapters(grouped.get("name"))
            count = stories_mod(grouped, user, count)

if ads and data.get("response").get("ads") != None:
    for datas in data.get("response").get("ads").get("items"):
        count = stories_mod(datas, "ADS", count)

print_log("            FIN!")
