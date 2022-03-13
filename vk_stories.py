import os
import sys
import json
from datetime import datetime
import urllib.request
import time
import random
import re
import urllib
from sys import exit
import progressbar as pb

def download_progress(blocks_read, block_size, total_size):
    
    if blocks_read == 0:
        widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.ETA(), ' ',
                   pb.FileTransferSpeed()]
        download_progress.progress_bar = pb.ProgressBar(
            widgets=widgets, maxval=total_size + block_size).start()

    download_progress.progress_bar.update(blocks_read * block_size)

def download_file(url, out, file_stories=False):
    try:
        if file_stories == False:
            file_stories = get_name(url)
        
        if os.path.exists(f'{out}{file_stories}'):
            return
        
        urllib.request.urlretrieve(url, f'{out}{file_stories}', reporthook=download_progress)
        download_progress.progress_bar.finish()
        
        returnf '{out}{file_stories}'
        
    except urllib.error.HTTPError as e:
        print(f'Ops! Error : {e}')
        
        return False
    
        time.sleep(5)

def chage_datechage(path_file, modTime):
    os.utime(path_file, (modTime, modTime))
    
    t = ""
    for i in path_file.split("/")[0:-1]:
        t += i + "/"
        os.utime(t, (modTime, modTime))

def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def get_name(url):
    return (url.rstrip("/").split("/")[-1]).split("?")[0]

def del_specific_chapters(name):
    return re.sub(r'[^\w\-_\. ]', '_', name)

def print_info_image(block, user, download=False):
    if download not in ["all","image"]:
        return False
    
    vlock = block.get("photo").get("sizes")
    
    if quality == "max":
        vlock = vlock.pop()
    elif quality == "low":
        vlock = vlock[0]
    
    ouput = f'stories/{user} ({block.get("owner_id")})/{block.get("id")}/'
    
    if vlock != block.get("photo").get("sizes"):
        print(f'size - {vlock["width"]}x{vlock["height"]} | url - {vlock["url"]}')
        
        if download:
            path = download_file(vlock["url"], ouput)
            
            if path != False:
                chage_datechage(path, block.get("photo").get("date"))
    else:
        for i in vlock:
            print(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')

token = open("token").read().replace("\n","").strip()

url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'
download = "all"
opt_download = ""
quality = "max"
ads = False

if "-h" in sys.argv:
    print("-f download from file\n-v download only video\n-i download only image\n-p download prewiew and first_frame\n-q ( all | max | low ) quality\n--ads\n\nThe default: download and image (quality is max) and video but no prewiew and first frame")
    exit()
    
if "-v" in sys.argv:
    download = "video"
elif "-i" in sys.argv:
    download = "image"
    
if "-p" in sys.argv:
    opt_download = "prewiew"

if "-q" in sys.argv:
    quality = sys.argv[sys.argv.index("-q") + 1]
    if quality not in ["all","low","max"]: quality = "max"

    
if "-f" in sys.argv:
    json_file = sys.argv[sys.argv.index("-f") + 1]
else:
    json_file = f'{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.json'
    download_file(url, "", json_file)

if "--ads" in sys.argv:
    ads = True
