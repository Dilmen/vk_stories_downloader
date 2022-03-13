import wget
import os
import urllib.request
import progressbar as pb
import re
import json
from datetime import datetime
import sys

def download_file(url, path, title=None):
    if title == None:
        title = os.path.splitext(url)
        title = title[0].split("/")[-1] + title[1].split("?")[0]
    
    file_stories = path + title
    
    try:
        r = urllib.request.urlopen(url)
        file_size = r.getheader('Content-Length')
        
        if os.path.exists(file_stories):
            if os.stat(file_stories).st_size == int(file_size):
                return
        
        urllib.request.urlretrieve(url, file_stories, reporthook=download_progress)
        download_progress.progress_bar.finish()
        
        return file_stories
        
    except urllib.error.HTTPError as e:
        print(f'Ops! Error : {e}')
    except urllib.error.ContentTooShortError:
        print("- file")
    
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
    
    os.utime(path_file, (modTime, modTime))
    
    t = ""
    
    for i in path_file.split("/")[0:-1]:
        t += i + "/"
        os.utime(t, (modTime, modTime))
        
def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def del_specific_chapters(name):
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(".","_")

def print_count(count):
    print(f'\n            Осталось {count} историй; Завершенно на {((count_t - count) / count_t) * 100}%', end="\n\n")

def count_stories(datas):
    count = 0
    
    if ads and datas.get("ads") != None:
        for i in datas.get("ads").get("items"):
            count += len(i.get("stories"))
    
    for i in datas.get("items"):
        if i.get("stories") != None:
            count += len(i.get("stories"))
            
    if datas.get("items")[datas.get("count") - 1].get("grouped") != None:
        for i in datas.get("items")[datas.get("count") - 1].get("grouped"):
            count += len(i.get("stories"))
    
    return count

def print_info_stories(block):
    print(f'id - {block.get("id")} | type - {block.get("type")} | date - {datetime.fromtimestamp(block.get("date")).strftime("%d/%m/%Y, %H:%M:%S")}')

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
            print(f'size - {block_t["width"]}x{block_t["height"]} | url - {block_t["url"]}')
            ar.append(download_file(block_t["url"], output))            
        else:
            for i in block_t:
                print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
                ar.append(download_file(i.get("url"), output))  
        
        for i in ar:
            change_modification_date(i, date)
                
    elif typu == "video":
        if download_type in ["video", "all"]:
            v = list(block.get("video").get("files").items())
            
            if len(v) > 1:
                print("Send me this json!")
            else:
                print(f'size - {v[0][0]} | url - {v[0][1]}')
                ar = download_file(v[0], output)
                
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
                print("Send me this json!")
                continue
            
            print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')
            ar.append(download_file(i.get("url"), output, f'{name} {i.get("width")}x{i.get("height")}.jpg'))
    
    for i in ar:
        change_modification_date(i, date)

token = open("token").read().replace("\n","").strip()
url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'
ads = False
preview = False
quality = "max"
         
if "-h" in sys.argv:
    print("-f download from file\n-v download only video\n-i download only image\n-p download prewiew and first_frame\n-q ( all | max | low ) quality\n--ads\n\nThe default: download and image (quality is max) and video but no prewiew and first frame")
    exit()

if "-v" in sys.argv:
    download_type = "video"
elif "-i" in sys.argv:
    download_type = "image"
else:
    download_type = "all"

if "-p" in sys.argv:
    preview = True

if "-q" in sys.argv:
    quality = sys.argv[sys.argv.index("-q") + 1]
    if quality not in ["all","low","max"]: quality = "max"

if "-f" in sys.argv:
    json_file = sys.argv[sys.argv.index("-f") + 1]
else:
    json_file = f'{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.json'
    download_file(url, json_file)

if "--ads" in sys.argv:
    ads = True

try:
    with open(json_file, "r", encoding='utf-8') as read_file:
        data = json.load(read_file)
except FileNotFoundError as e:
    print(f'Error - {e}')
    exit()

count = count_stories(data.get("response"))
count_t = count

for datas in data.get("response").get("items"):
    if datas.get("type") == "stories":
        print(f'            name - {datas.get("name")}', end="\n\n")
        user = del_specific_chapters(datas.get("name"))
        count = stories_mod(datas, user, count)
    else:
        for grouped in datas.get("grouped"):
            print(f'            name - {grouped.get("name")}', end="\n\n")
            user = del_specific_chapters(grouped.get("name"))
            count = stories_mod(grouped, user, count)

if ads and data.get("response").get("ads") != None:
    for datas in data.get("response").get("ads").get("items"):
        count = stories_mod(datas, "ADS", count)

print("            FIN!")
