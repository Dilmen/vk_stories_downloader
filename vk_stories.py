#!/usr/bin/env python3
import os
import string
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

__version__ = "0.4.1"

def download_file(url: str, path: Path, title: str = None, attempt: int = 0):
    if attempt >= 10:
        return None

    if not create_dir(path):
        download_file(url, path, title, attempt + 1)
        return None

    title = title or Path(url).stem + Path(url).suffix.split("?")[0]
    file_stories = path.joinpath(title)

    try:
        if file_stories.is_file():
            if not check_in_completed(path, title):
                request = urllib.request.urlopen(url)
                file_size = request.getheader('Content-Length')

                if file_stories.stat().st_size == int(file_size):
                    completed(path, title)
                    return None
            else:
                return None

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
            if i + 1 == sleep:
                sys.stdout.write(f'\r{"":20}')
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

    return None


def check_on_emptyfolder_and_remove(path: Path):
    try:
        if not list(path.iterdir()):
            path.rmdir()

        if not list(path.parent.iterdir()):
            path.parent.rmdir()

    except OSError as e:
        print_log(f'\nOps! Error : {e}')


def download_progress(blocks_read: int, block_size: int, total_size: int):
    if blocks_read == 0:
        widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.ETA(), ' ',
                   pb.FileTransferSpeed()]
        download_progress.progress_bar = pb.ProgressBar(
            widgets=widgets, maxval=total_size + block_size).start()

    download_progress.progress_bar.update(blocks_read * block_size)


def change_modification_date(path: Path, modTime: int):
    if not path.exists():
        return None

    try:
        os.utime(path, (modTime, modTime))

        for i in path.parents:
            os.utime(i, (modTime, modTime))

    except OSError as e:
        print_log(f'\nOps! Error : {e}')

    return None


def create_dir(path: Path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True

    except OSError as e:
        print_log(f'\nOps! Error : {e}')
        return False


def replace_specific_chapters(name: str):
    return name.translate(remove_punctuation_map)


def bar_gen(f: int):
    return f'[{"".join(["#" if x * 10 <= f else "_" for x in range(1,11)])}]'


def print_count(count: int, count_all: int):
    count_ = ((count_all - count) / count_all) * 100

    print_log(f'\n{"":5}Remain stories - {count} | Completed on {count_}% {bar_gen(count_)} {int(count_)}%', end="\n\n")


def count_stories(datas: dict):
    ads_count = 0
    friends = 0
    public = 0

    if ads and (data := datas.get("ads", {}).get("items", 0)):
        for ads_stories in data:
            ads_count += len(ads_stories.get("stories"))

    for stories in datas.get("items"):
        if i := stories.get("stories", 0):
            friends += len(i)
        elif i := stories.get("grouped", 0):
            for public_stories in i:
                public += len(public_stories.get("stories"))

    return ads_count, friends, public


def print_info_stories(block: dict):
    print_log(f'id - {block.get("id")} | type - {block.get("type")} | date - {datetime.fromtimestamp(block.get("date")).strftime("%d/%m/%Y, %H:%M:%S")}')


def stories_mod(datas: dict, user: str, count: int, count_all: int):
    for stories in datas.get("stories"):
        print_info_stories(stories)

        if (stories_type := stories.get("type", 0)) in ("photo", "video"):
            download_stories(stories, stories_type, user)

        count -= 1

        print_count(count, count_all)

    return count


def get_sizes(data: dict):
    sizes = {}

    for size in data:
        sizes.update({size.get("type"): {"size": f'{size.get("width")}x{size.get("height")}', "url": size.get("url")}})

    return sizes


def ar(url: str, output: Path, date: int, title: str = None):
    check_file = download_file(url, output, title)

    if check_file is not None:
        change_modification_date(check_file, date)


def stf(block: dict, lsd: list):
    if block.get("type") == "stories":
        if arguments.whitelist:
            return str(block.get("stories", [{}])[0].get("owner_id")) not in lsd
        elif arguments.blacklist:
            return str(block.get("stories", [{}])[0].get("owner_id")) in lsd

    return False


def stories_filter(block: dict):
    user_list = [[],[]]
    grouped = -1
    lsd = arguments.whitelist if arguments.whitelist else arguments.blacklist

    if not lsd:
        return block

    for num, stories in enumerate(block.get("response").get("items")):
        if stf(stories, lsd):
            user_list[0].append(num)
        elif stories.get("grouped", 0):
            grouped = num

            for num, stories_grouped in enumerate(stories.get("grouped")):
                if stf(stories_grouped, lsd):
                    user_list[1].append(num)

    for user in reversed(user_list[1]):
        del block.get("response").get("items")[grouped].get("grouped")[user]

    for user in reversed(user_list[0]):
        del block.get("response").get("items")[user]

    return block


def download_stories(block: dict, stories_type: str, user: str):
    output = path_stories.joinpath(f'stories/{user} ({block.get("owner_id")})/{block.get("id")}')
    date = block.get("date")

    if stories_type == "photo" and download_type in ("photo", "all"):

        sizes = get_sizes(block.get(stories_type).get("sizes"))

        if arguments.image_quality is not None and (arguments.image_quality in sizes):
            stories = {arguments.image_quality : sizes.get(arguments.image_quality)}
        else:
            if quality == "max":
                stories = {"w": sizes.get("w", {"url": ""})}
            elif quality == "low":
                stories = {"s": sizes.get("s", {"url": ""})}
            else:
                stories = sizes

        for key, value in stories.items():
            print_log(f'size - {value.get("size")} | url - {value.get("url")}')
            ar(value.get("url"), output, date)

        # sizes s, m, j, x, y, z, w
        # sisze = width x height
        # s : 42x75
        # m : 73x130
        # j : 144x256
        # x : 340x604
        # y : 454x807
        # z : 607x1080
        # w : 750x1334
    elif stories_type == "video" and download_type in ("all", "video"):
        videos = {key : value for key, value in block.get("video", {}).get("files").items() if "mp4" in key}
        videos_quality = tuple(videos.keys())
        choose_quality = f'mp4_{video_quality}'

        #    added choose quality if selected quality is not available

        if video_quality is None:
            if quality == "max":
                videos = {videos_quality[-1]: videos.get(videos_quality[-1])}
            elif quality == "low":
                videos = {videos_quality[-1]: videos.get(videos_quality[0])}
        else:
            videos = {video_quality: videos.get(choose_quality, 0)} if choose_quality in videos_quality else {videos_quality[0]: videos.get(videos_quality[0])}

        for qulity, url in videos.items():
            title = None

            if "mycdn" in url:
                title = f'{qulity}.{url.split("=")[-1]}.mp4'

            print_log(f'size - {qulity} | url - {url}')
            ar(url, output, date, title)

    if preview:
        download_preview(block.get("video", {}), "image", output.joinpath("image"), date)
        download_preview(block.get("video", {}), "first_frame", output.joinpath("first_frame"), date)

    save_stories_info(block, output)


def download_preview(block: dict, name: str, output: Path, date: int):
    if images := block.get(name, 0):
        print_log(f"{'':5}video image | type - {name}")

        for image in images:
            print_log(f'size - {image.get("width")}x{image.get("height")} | url - {image.get("url")}')

            if (path := download_file(image.get("url"), output, f'{name} {image.get("width")}x{image.get("height")}.jpg')) is not None:
                change_modification_date(path, date)

        print()


def print_log(*string_: str, end: str = "\n", out = sys.stdout, sep: str = " "):
    string_ = " ".join(string_)

    if logs:
        logging.info(string_.replace("\n", "").strip())

    print(string_, end=end, file=out, sep=sep)


def completed(path: Path, name: str):
    with open(Path(path, ".completed"), "a+", encoding="utf-8") as f:
        f.write(f'{name}\n')


def check_in_completed(path: Path, name):
    if (path := Path(path, ".completed")).is_file():
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.rstrip("\n") == name:
                    return True

    return False


def sto(stories: dict, count: int, count_all: int):
    name = stories.get("name")
    user = replace_specific_chapters(name)

    print_log(f'{"":10}name - {name}', end="\n\n")

    return stories_mod(stories, user, count, count_all)


def captcha_handler(captcha):
    key = input(f"Enter captcha code {captcha.get_url()} : ").strip()

    return captcha.try_again(key)


def auth_handler():
    key = input("Enter authentication code: ")
    remember_device = True

    return key, remember_device

def get_token():
    print("Leave empty for exit\n")

    config_filename = ".vk_config.v2.json"
    login = input("Enter phone number input: ")
    password = input("Enter password input: ")

    if not login or not password:
        sys.exit()

    vk_session = vk_api.VkApi(login, password, config_filename=config_filename, captcha_handler=captcha_handler, auth_handler=auth_handler)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as e:
        print_log(f'\nError - {e}\n')
        get_token()

        return None

    with open(".token", "w", encoding="utf-8") as f:
        f.write(vk_session.token.get("access_token"))

    print()

    return None


def custom_file_name():
    return None


def save_stories_info(stories: dict, output: Path):
    if arguments.ssi and not (file := output.joinpath('storie_info.json')).is_file() and output.exists():
        with open(file, "w", encoding="utf-8") as fp:
            json.dump(stories, fp, indent=4)


def main():
    if arguments.file is None:
        token = arguments.token.strip()

        if not token:
            if Path(arguments.token_file).is_file():
                with open(arguments.token_file, encoding="utf-8") as fp:
                    token = fp.read().replace("\n","").strip()
            elif arguments.token_file != ".token":
                print_log(f"Error - file {arguments.token_file} not found")
                return None
            else:
                get_token()
                main()

                return None

        url = f'https://api.vk.com/method/stories.get?access_token={token}&v=5.126'

    if not arguments.file:
        json_file = download_file(url, Path("json"), f'{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.json')
    else:
        json_file = arguments.file

    if json_file is None:
        print_log('Error - json file don`t downloaded!')
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
    
    data = stories_filter(data)
    adsC, friends, public = count_stories(data.get("response"))
    count_all = count = adsC + friends + public

    print_log(f'{"":5}Count stories: friends - {friends} | public - {public} | ads - {adsC} | all - {count}')
    time.sleep(5)

    for stories in data.get("response").get("items"):
        if stories.get("type", 0) == "stories":
            count = sto(stories, count, count_all)
        elif stories := stories.get("grouped", 0):
            for stories_grouped in stories:
                count = sto(stories_grouped, count, count_all)

    if ads and (data := data.get("response").get("ads", {}).get("items", 0)):
        for ads_stories in data:
            count = stories_mod(ads_stories, "ADS", count, count_all)

    print_log(f'{"":5}FIN!')

    return None


parser = argparse.ArgumentParser(description='Script to download stories from VK')
parser.add_argument('-f', '--file', type=str, dest='file', help='get stoies from file')
parser.add_argument('-v', '--video', action='store_true', dest='video', help='download only video')
parser.add_argument('-i', '--image', action='store_true', dest='image', help='download only image')
parser.add_argument('-p','--preview', action='store_true', dest='preview', help='download video preview')
parser.add_argument('-q', '--quality', type=str, default="max", dest='quality', choices=('all', 'low', 'max'), help='select quality (default: max)')
parser.add_argument('--image-quality', type=str, dest='image_quality', choices=('s', 'm', 'j', 'x', 'y', 'z', 'w'), help='select image quality (default: w)')
parser.add_argument('--video-quality', type=int, dest='video_quality', choices=(144, 240, 360, 480, 720), help='select quality for video if there is a chooice')
parser.add_argument('--ads', action='store_true', dest='ads', help='download ads stories')
parser.add_argument('--sleep',default=3, dest='sleep', help='Provide sleep timer', type=int, metavar="SECONDS")
parser.add_argument('--log', action='store_true', dest='log', help='Write to log file')
parser.add_argument('--dump', action='store_true', dest='dump', help='download only dump and exit')
parser.add_argument('--token', default="", type=str, dest='token', help='token')
parser.add_argument('--token-file', type=str, default=".token", dest='token_file', help='path to file with token', metavar="FILE")
parser.add_argument('--path', type=str, default=".", dest='path_stories', help='The path where the stories should be downloaded.', metavar="PATH")
parser.add_argument('--save-storie-info', action='store_true', dest='ssi', help='Save info about stories to file "storie_info.json"')
parser.add_argument('--whitelist', action='extend', dest="whitelist", nargs="+", default=[], help="download only this storie with this user/group id", metavar="ID")
parser.add_argument('--blacklist', action='extend', dest="blacklist", nargs="+", default=[], help="skip stories with this user/group id", metavar="ID")
parser.add_argument('--version', action='version', version=f"VK stories downloader v.{__version__}")

arguments = parser.parse_args()
ads = arguments.ads
preview = arguments.preview
quality = arguments.quality
sleep = arguments.sleep
logs = arguments.log
video_quality = arguments.video_quality
path_stories = Path(arguments.path_stories)
download_type = "all"
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

if arguments.video:
    download_type = "video"
elif arguments.image:
    download_type = "photo"

if logs:
    create_dir("logs")
    logging.basicConfig(filename=f'logs/{datetime.now().strftime("%d-%m-%Y_%H.%M.%S")}.log', encoding='utf-8', format='%(asctime)s ➤➤➤ %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
    logging.info(" ".join(sys.argv))

if __name__ == '__main__':
    main()
