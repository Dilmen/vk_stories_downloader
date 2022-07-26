# vk_stories_downloader
Script for download stories from VK

Run `python -m pip install -r requirements.txt` for install packages
____
Code and size for `image-quality`
| Code | Size |
|:----:|:----:|
| s | 42x75 |
| m | 73x130 |
| j | 144x256 |
| x | 340x604 |
| y | 454x807 |
| z | 607x1080 |
| w | 750x1334 |
____
```
usage: vk_stories.py [-h] [-f FILE] [-v] [-i] [-p] [-q {all,low,max}]
                     [--image-quality {s,m,j,x,y,z,w}]
                     [--video-quality {144,240,360,480,720}] [--ads]
                     [--sleep SECONDS] [--log] [--dump] [--token TOKEN]
                     [--token-file FILE] [--path PATH] [--save-storie-info]
                     [--whitelist ID [ID ...]] [--blacklist ID [ID ...]]
                     [--version]

Script to download stories from VK

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  get stoies from file
  -v, --video           download only video
  -i, --image           download only image
  -p, --preview         download video preview
  -q {all,low,max}, --quality {all,low,max}
                        select quality (default: max)
  --image-quality {s,m,j,x,y,z,w}
                        select image quality (default: w)
  --video-quality {144,240,360,480,720}
                        select quality for video if there is a chooice
  --ads                 download ads stories
  --sleep SECONDS       Provide sleep timer
  --log                 Write to log file
  --dump                download only dump and exit
  --token TOKEN         token
  --token-file FILE     path to file with token
  --path PATH           The path where the stories should be downloaded.
  --save-storie-info    Save info about stories to file "storie_info.json"
  --whitelist ID [ID ...]
                        download only this storie with this user/group id
  --blacklist ID [ID ...]
                        skip stories with this user/group id
  --version             show program's version number and exit
```
