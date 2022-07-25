#!/usr/bin/env python3
import os
import urllib.request
import json
from datetime import datetime
import sys
import time
import socket
import logging
import http
import argparse
from pathlib import Path
import progressbar as pb
import vk_api

version = "0.4"

def download_file(url: str, path: Path, title: str = None, attempt: int = 0):
    if attempt >= 10:
        return

    title = title or Path(url).stem + Path(url).suffix.split("?")[0]

    file_stories = path.joinpath(title)

    if not create_dir(path):
        download_file(url, path, title, attempt + 1)

    try:
        if file_stories.is_file():
            if check_in_completed(path, title):
                return
            else:
                r = urllib.request.urlopen(url)
                file_size = r.getheader('Content-Length')

                if file_stories.stat().st_size == int(file_size):
                    completed(path, title)
                    return

        timeout = 10

        socket.setdefaulttimeout(timeout)
        urllib.request.urlretrieve(url, file_stories, reporthook=download_progress)
        download_progress.progress_bar.finish()
        completed(path, title)

        if arguments.dump:
            return file_stories

        for i in range(sleep):
            sys.stdout.write(f'\r{"":>10}Zzzz{(sleep - i):3}')
            time.sleep(1)
            if i + 1 == sleep: sys.stdout.write(f'\r{"":20}')
            sys.stdout.flush()

        print()

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
    except Exception as e:
        print_log(f'\nOps! SEND ME THIS ERROR!!! : {e}')

    print()

    check_on_emptyfolder_and_remove(path)

    return

def check_on_emptyfolder_and_remove(path: Path):
    try:
        if not len(list(path.iterdir())):
            path.rmdir()

        if not len(list(path.parent.iterdir())):
            path.parent.rmdir()

    except OSError as e:
        print_log(f'\nOps! Error : {e}')

def download_progress(blocks_read, block_size, total_size):
    if blocks_read == 0:
        widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.ETA(), ' ',
                   pb.FileTransferSpeed()]
        download_progress.progress_bar = pb.ProgressBar(
            widgets=widgets, maxval=total_size + block_size).start()

    download_progress.progress_bar.update(blocks_read * block_size)

def change_modification_date(path: Path, modTime: int):
    if not path.exists():
        return

    try:
        os.utime(path, (modTime, modTime))

        for i in path.parents:
            os.utime(i, (modTime, modTime))

    except OSError as e:
        print_log(f'\nOps! Error : {e}')

def create_dir(path: Path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True

    except OSError as e:
        print_log(f'\nOps! Error : {e}')
        return False

def replace_specific_chapters(name: str):
    for i in "\/:*?\"<>|":
        name = name.replace(i, "_")

    return name

def bar_gen(f: int):
    return f'[{"".join(["#" if x * 10 <= f else "_" for x in range(1,11)])}]'

def print_count(count: int):
    t = ((count_t - count) / count_t) * 100

    print_log(f'\n  Remain stories - {count} | Completed on {t}% {bar_gen(t)} {str(t).split(".")[0]}%', end="\n\n")

def count_stories(datas: dict):
    adsC = 0
    friends = 0
    public = 0

    if ads and datas.get("ads", 0):
        for i in datas.get("ads").get("items"):
            adsC += len(i.get("stories"))

    for i in datas.get("items"):
        if "stories" in i:
            friends += len(i.get("stories"))
        if i.get("type") == "community_grouped_stories":
            for j in i.get("grouped"):
                public += len(j.get("stories"))

    return (adsC + friends + public), adsC, friends, public

def print_info_stories(block: dict):
    print_log(f'id - {block.get("id")} | type - {block.get("type")} | date - {datetime.fromtimestamp(block.get("date")).strftime("%d/%m/%Y, %H:%M:%S")}')

def stories_mod(datas: dict, user: str, count: int):
    for stories in datas.get("stories"):
        print_info_stories(stories)

        if stories.get("type") == "photo" and download_type in ("image", "all"):
            download_stories(stories, "photo", user)
        elif stories.get("type") == "video":
            download_stories(stories, "video", user)

        count -= 1

        print_count(count)

    return count

def download_stories(block: dict, typu: str, user: str):
    output = Path(path_stories, f'stories/{user} ({block.get("owner_id")})/{block.get("id")}')
    date = block.get("date")

    if typu == "photo":

        block_t = block.get("photo").get("sizes")

        if quality == "max":
            block_t = block_t.pop()
        elif quality == "low":
            block_t = block_t[0]

        if block_t != block.get("photo").get("sizes"):
            print_log(f'size - {block_t["width"]}x{block_t["height"]} | url - {block_t["url"]}')

            ar = download_file(block_t["url"], output)

            if ar is not None:
                change_modification_date(ar, date)

        else:
            for i in block_t:
                print_log(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')

                ar = download_file(i.get("url"), output)

                if ar is not None:
                    change_modification_date(ar, date)

    elif typu == "video":

        if download_type in ("video", "all"):
            v = list(block.get("video").get("files").items())

            if len(v) > 1:
                #print_log("(⌐■_■) ∠( ᐛ 」∠)_")
                block_t = block.get("video").get("files")
                tt = list(filter(lambda x : "mp4" in x , list(block_t)))

                if video_quality is not None:
                    t = tt[0]
                    qs = f'mp4_{video_quality}'
                    tt = block_t.get(qs, block_t.get(tt[0]))
                    qs = qs if block_t.get(qs, 0) else t
                else:
                    if quality == "max":
                        qs = tt[-1]
                        tt = block_t.get(tt[-1])
                    elif quality == "low":
                        qs = tt[0]
                        tt = block_t.get(tt[0])

                if quality != "all":

                    print_log(f'size - {qs} | url - {tt}')

                    ar = download_file(tt, output, f'{qs}.{tt.split("=")[-1]}.mp4')

                    if ar is not None:
                        change_modification_date(ar, date)

                elif video_quality is None:
                    for i in tt:
                        print_log(f'size - {i} | url - {block_t.get(i)}')

                        ar = download_file(block_t.get(i), output, f'{i}.{block_t.get(i).split("=")[-1]}.mp4')

                        if ar is not None:
                            change_modification_date(ar, date)

            else:
                print_log(f'size - {v[0][0]} | url - {v[0][1]}')
                ar = download_file(v[0][1], output)

                if ar is not None:
                    change_modification_date(ar, date)

        if preview:
            download_preview(block.get("video"), "image", output.joinpath("image"), date)
            download_preview(block.get("video"), "first_frame", output.joinpath("first_frame"), date)

def download_preview(block: dict, name: str, output: str, date: int):
    if name in block:
        for i in block.get(name):
            #    mycdn "∠( ᐛ 」∠)_"

            print_log(f'size - {i.get("width")}x{i.get("height")} | url - {i.get("url")}')

            ou = download_file(i.get("url"), output, f'{name} {i.get("width")}x{i.get("height")}.jpg')

            if ou is not None:
                change_modification_date(ou, date)

def print_log(*string: str, end: str = "\n", out = sys.stdout, sep: str = " "):
    string = " ".join(string)
    
    if logs:
        logging.info(string.replace("\n", "").strip())

    print(string, end=end, file=out, sep=sep)

def completed(path: Path, name: str):
    with open(Path(path, ".completed"), "a+") as f:
        f.write(f'{name}\n')

def check_in_completed(path: Path, name):
    if (path := Path(path, ".completed")).is_file():
        with open(path) as f:
            for line in f:
                if line.rstrip("\n") == name:
                    return True

    return False

def get_token():

    config_filename = ".vk_config.v2.json"
    login = input("Number input: ")
    password = input("Password input: ")
    vk_session = vk_api.VkApi(login, password, config_filename=config_filename)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as e:
        print_log(f'\nError - {e}\n')
        get_token()

        return
    
    with open("token", "w") as f:
        f.write(vk_session.token.get("access_token"))
    
    print()

def main():
    if arguments.file is None:
        token = ""

        if arguments.token is None:
            try:
                if arguments.token_file is None:
                    if Path("token").exists():
                        token = open("token").read().replace("\n","").strip()
                    else:
                        get_token()
                else:
                    token = open(arguments.token_file).read().replace("\n","").strip()
            except FileNotFoundError as e:
                print_log(f'Error - {e}')
                sys.exit()
        else:
            token = arguments.token.strip()

        url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'

    if not arguments.file:
        json_file = download_file(url, Path("json"), f'{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.json')
    else:
        json_file = arguments.file

    if json_file is None:
        print_log(f'Error - json file don`t downloaded!')
        sys.exit()

    try:
        with open(json_file, "r", encoding='utf-8') as read_file:
            data = json.load(read_file)
    except FileNotFoundError as e:
        print_log(f'Error - {e}')
        sys.exit()
    except json.decoder.JSONDecodeError as e:
        print_log(f'Error - {e} in file {json_file}')
        sys.exit()

    if "error" in data:
        print_log(f'Error - {data.get("error").get("error_msg")}\nReauthorization...\n')

        get_token()
        main()

        return False

    if arguments.dump or not json_file:
        sys.exit()

    global count_t
    count, adsC, friends, public = count_stories(data.get("response"))
    count_t = count

    print_log(f'{"":10}Count stories: friends - {friends} | public - {public} | ads - {adsC} | all - {count}')
    time.sleep(5)

    for datas in data.get("response").get("items"):
        if datas.get("type") == "stories":
            print_log(f'{"":10}name - {datas.get("name")}', end="\n\n")
            user = replace_specific_chapters(datas.get("name"))
            count = stories_mod(datas, user, count)

        else:
            #if datas.get("grouped"):
            if "grouped" in datas:
                for grouped in datas.get("grouped"):
                    print_log(f'{"":10}name - {grouped.get("name")}', end="\n\n")
                    user = replace_specific_chapters(grouped.get("name"))
                    count = stories_mod(grouped, user, count)

    if ads and "ads" in data.get("response"):
        for datas in data.get("response").get("ads").get("items"):
            count = stories_mod(datas, "ADS", count)

    print_log(f'{"":10}FIN!')


parser = argparse.ArgumentParser(description='Script to download stories fron VK')
parser.add_argument('-f', '--file', type=str, dest='file', help='get stoies from file')
parser.add_argument('-v', '--video', action='store_true', dest='video', help='download only video')
parser.add_argument('-i', '--image', action='store_true', dest='image', help='download only image')
parser.add_argument('-p','--preview', action='store_true', dest='preview', help='download video preview')
parser.add_argument('-q', '--quality', type=str, default="max", dest='quality', choices=('all', 'low', 'max'), help='select quality (default: max)')
parser.add_argument('--video-quality', type=int, dest='video_quality', choices=(144, 240, 360, 480, 720), help='select quality for video if there is a chooice')
parser.add_argument('--ads', action='store_true', dest='ads', help='download ads stories')
parser.add_argument('--sleep',default=3, dest='sleep', help='Provide sleep timer', type=int)
parser.add_argument('--log', action='store_true', dest='log', help='Write to log file')
parser.add_argument('--dump', action='store_true', dest='dump', help='download only dump and exit')
parser.add_argument('--token', type=str, dest='token', help='token')
parser.add_argument('--token-file', type=str, dest='token_file', help='token file')
parser.add_argument('--path', type=str, default=".", dest='path_stories', help='The path where the stories should be downloaded.')
#parser.add_argument('--oath', action='store_true', dest='oath', help='Get token')
parser.add_argument('--version', action='version', version=f"VK stories downloader v.{version}")

arguments = parser.parse_args()

ads = arguments.ads
preview = arguments.preview
quality = arguments.quality
sleep = arguments.sleep
logs = arguments.log
video_quality = arguments.video_quality
path_stories = arguments.path_stories
count_t = 0

if arguments.video:
    download_type = "video"
elif arguments.image:
    download_type = "image"
else:
    download_type = "all"

if logs:
    create_dir("logs")
    logging.basicConfig(filename=f'logs/{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.log', encoding='utf-8', format='%(asctime)s ➤➤➤ %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
    logging.info(" ".join(sys.argv))

if __name__ == '__main__':
    main()
