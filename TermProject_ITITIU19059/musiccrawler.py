import re
import os
import hmac
import json
import hashlib
import eventlet
import requests
import datetime
from urllib.parse import urlencode


with open("HEADERS.json") as f:
    HEADERS = json.load(f)

_time = str(int(datetime.datetime.now().timestamp()))

json_local = []
if os.path.exists("music_info.json"):
    with open('music_info.json', encoding='utf-8') as f:
        json_local = json.load(f)

def checking(response: str) -> None:
    if b'"err":-201' in response.content:
        print("\n[*] Error: Cookie expired! Trying update the new one!")
        updateCookie()
        main()
        exit(0)
    elif b'"err":0' not in response.content:
        print(response.headers)
        print(response.content)
        exit(0)

def updateCookie() -> None:
    with eventlet.Timeout(10):
        url = "https://zingmp3.vn/api/v2/page/get/newrelease-chart?ctime=1652468472&version=1.6.25&sig=bef1414d14477c5a658c95ad053b348752c11073ab7aca46c122b99c18fd5df1922fdd3e2aa43624120902195f321c96a897ac1ef9f11b8422700b0e2980e58c&apiKey=88265e23d4284f25963e6eedac8fbfa3"
        response = requests.get(url)
        HEADERS["Cookie"] = response.headers["Set-Cookie"].split(';')[0]
        with open("HEADERS.json",'w') as f:
            f.write(json.dumps(HEADERS))

def urlGeneration(name_api: str, param: dict) -> str:
    API_KEY = '88265e23d4284f25963e6eedac8fbfa3'
    SECRET_KEY = b'2aa2d1c561e809b267f3638c4a307aab'

    def get_hash256(string):
        return hashlib.sha256(string.encode('utf-8')).hexdigest()

    def get_hmac512(string):
        return hmac.new(SECRET_KEY, string.encode('utf-8'), hashlib.sha512).hexdigest()

    text = "".join([f"{k}={v}" for k,v in param.items()])
    sha256 = get_hash256(text)

    data = {
        'ctime': param["ctime"],
        'sig': get_hmac512(f"{name_api}{sha256}"),
        'apiKey': API_KEY
    }
    data.update(param)
    return f"https://zingmp3.vn{name_api}?{urlencode(data)}"

def getTopList(name_api:str = '/api/v2/page/get/newrelease-chart', param:dict = None) -> list:
    print('\n[*] Getting list of song')
    with eventlet.Timeout(10):
        if param:
            url = urlGeneration(name_api, {'ctime':_time,'id':param["id"],'version':'1.6.25'})
        else:
            url = urlGeneration(name_api, {'ctime':_time,'version':'1.6.25'})
        response = requests.get(url,headers=HEADERS)
        checking(response)

        data = re.findall(r'\"items\"\s*:\s*\[.*\]', response.content.decode('utf-8'))
        data = json.loads(data[0].split("\"items\":")[1])

        res = []
        for items in data:
            res.append([items["encodeId"], items["link"]])
    return res

def getStreamInfo(target_id: str) -> dict:
    with eventlet.Timeout(10):
        url = urlGeneration('/api/v2/song/get/streaming', {'ctime':_time,'id':target_id,'version':'1.6.25'})
        response = requests.get(url,headers=HEADERS)
        if b'"err":-1150' in response.content:
            print('[*] Error : VIP requirement!')
            return {}
        checking(response)

        data = re.findall(r'\"data\"\s*:\s*{.*},', response.content.decode('utf-8'))[0][:-1]
        data = (data.split('"data":')[1][1:-1]).split(',')
        
        streams = {"streams" : []}
        for i in data:
            i = '{' + i + '}'
            streams["streams"].append(json.loads(i))
    return streams

def downloadLyric(target_id: str) -> str:
    with eventlet.Timeout(10):
        url = urlGeneration('/api/v2/lyric/get/lyric', {'ctime':_time,'id':target_id,'version':'1.6.25'})
        response = requests.get(url,headers=HEADERS)
        checking(response)
        #print(response.content)

        lyric = ""
        
        data = re.findall(r'{\"sentences\"\s*:\s*\[.*\]}\]', response.content.decode('utf-8'))
        if data == []:
            data = re.findall(r'{\"lyric\"\s*:\s*\".*?\"', response.content.decode('utf-8'))
            if data == []:
                data = re.findall(r'{\"file\"\s*:\s*\".*?\",', response.content.decode('utf-8'))
                data = data[0].split("file\":\"")[1][:-2]
                os.system(f"curl -s \"{data}\" -o temp")
                with open('temp','r',encoding='utf-8') as f:
                    data = f.read()
                    data = (data.split("length: ")[1]).split('\n')[1:-1]
                    for i in range(len(data)):
                        data[i] = data[i].split(']')[1] if data[i].split(']') != [] else ''
                os.system(f"rm temp")
                lyric = '\n'.join(data)
            else:
                data = json.loads(data[0] + '}')
                #print(data)
                lyric = data["lyric"]
        else:
            data = json.loads(data[0].split("{\"sentences\":")[1])
            #print(data)
            for x in data: 
                lyric += ' '.join([i["data"] for i in x["words"]]) + '\n'
    return lyric

def downloadMedia(link, title, quality) -> None:
    if link == "VIP":
        return

    DirDownload = os.path.join(os.getcwd(), "DOWNLOAD")
    if not os.path.exists(DirDownload): 
        os.mkdir(DirDownload)

    filename = f"{title}_{quality}"
    if os.path.exists(f"{DirDownload}/{filename}"):
        return

    link = link.replace('https://', "https://vnno-vn-5-tf-")
    os.system(f"curl -s \"{link}\" -o \"{DirDownload}/{filename}\"")

def getMediaFile(url: str) -> None:
    obj = re.search(r'/.*?/(?P<slug>.*?)\/(?P<id>.*?)\W', url)
    if not obj:
        print('\n[*] Error : not existed!')
        return
    obj___id = obj.group('id')
    obj_slug = obj.group('slug')
    
    with eventlet.Timeout(10):
        url = urlGeneration('/api/v2/page/get/song', {'ctime':_time,'id':obj___id,'version':'1.6.25'})
        response = requests.get(url,headers=HEADERS)
        checking(response)

        #print(response.content.decode('utf-8'))
        data = re.findall(r'\"data\"\s*:\s*{.*},\"timestam', response.content.decode('utf-8'))[0][:-10]
        data = json.loads(data.split("\"data\":")[1])

        title = data["title"]

        lyric = ""
        if "hasLyric" not in data:
            print(f"\n[*] \"{title}\" does not has lyric!")
        elif data["hasLyric"]:
            print(f"\n[*] Download \"{title}\" lyric...")
            lyric = downloadLyric(obj___id)
        else:
            print(f"\n[*] \"{title}\" does not has lyric!")
        
        if "composers" in data: del data["composers"]
        if "sections" in data: del data["sections"]
        data.update({"lyric": lyric})

        print(f'[*] Download \"{title}\" audio...')
        streams = getStreamInfo(obj___id)
        if streams == {}:
            return
        else:
            data.update(streams)

        for i in streams["streams"]:
            for quality,link in i.items():
                downloadMedia(link, title, quality)

    #print(json.dumps(data))
    json_local.append(data)

def main() -> None:
    # Default, 100 new songs
    listOfSong = getTopList()
    print(f"[*] Number of song: {len(listOfSong)}\n{listOfSong}")
    # Custom, get 100 songs of one playlist
    #listOfSong = getTopList('/api/v2/page/get/playlist', {"id":"ZWZB96A9"})
    
    for x in listOfSong: 
        flag = 0
        for i in json_local:
            if x[0] == i["encodeId"]:
                flag = 1
                break
        if flag:
            continue

        getMediaFile(x[1])
        #print(json_local)
        #input()
    with open("music_info.json",'w',encoding='utf-8') as f:
        f.write(json.dumps(json_local))

    print('\n[*] Crawling done!')

main()
    



""" Headers
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Connection: keep-alive
Cookie: zmp3_rqid=MHwyNy43Ni4xMTAdUngMjA5fHYxLjYdUngMjV8MTY1MjUyODgzNTE5Nw
Cache-Control: max-age=0
"""

# https://zingmp3.vn/api/v2/page/get/newrelease-chart?ctime=1652468472&version=1.6.25&sig=bef1414d14477c5a658c95ad053b348752c11073ab7aca46c122b99c18fd5df1922fdd3e2aa43624120902195f321c96a897ac1ef9f11b8422700b0e2980e58c&apiKey=88265e23d4284f25963e6eedac8fbfa3
# https://zingmp3.vn/api/v2/page/get/song?id=ZZBUE7ZA&ctime=1652534700&version=1.6.25&sig=fa906944628776791050d19321ce2ade1227667cb1d032a77801e52461c62687fbcea9509e04c7f741f1c656ac0f562d2f8d7fc5554767c3051332e27f92234a&apiKey=88265e23d4284f25963e6eedac8fbfa3
# https://zingmp3.vn/api/v2/lyric/get/lyric?id=ZW6I979F&ctime=1652539551&version=1.6.25&sig=0c781dd12f369c3f062af7ee0fee8298c6c17edbb38ea87fac73cb989c239ccca94f4eb7fcee6e80468b014380ea08a74c94b3f2170deb4756d54ffb5a81f1bc&apiKey=88265e23d4284f25963e6eedac8fbfa3
# https://zingmp3.vn/api/v2/song/get/streaming?id=ZW8I8008&ctime=1652557397&version=1.6.25&sig=5eaf301e68e2ab68eea41b906af684344d8fc109d5382ba533c70f4d2950a6542b233eb88fe171df1e1e6c431981c54efdc10b653fd1428c9ffea9334a0b5cdf&apiKey=88265e23d4284f25963e6eedac8fbfa3


# Referrer: https://github.com/hatienl0i261299/Zingmp3