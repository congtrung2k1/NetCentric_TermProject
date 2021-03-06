import sys
import socket
import selectors
import types
import threading
import urllib.parse

def process(client, caddr):
    while True:
        mess = client.recv(1024)
        if mess == None:
            return

        request = mess.split(b'\r\n')[0]
        req_method = request.split(b' ')[0]
        req_url = request.split(b' ')[1].strip(b'/')

        print(f"[*] Request from user: {request}")

        if req_method == b'GET':
            flag = 0
            param = ''

            if req_url == b"":
                url = 'music.html'
                ctype = "text/html"
            elif b"song.html" in req_url:
                url = 'song.html'
                ctype = "text/html"
                flag = 2
                param = req_url.split(b'?id=')[1]
                param = param.split(b'_')
            elif b"song_info.html" in req_url:
                url = 'song_info.html'
                ctype = "text/html"
                flag = 1
                param = req_url.split(b'?id=')[1]

            elif req_url == b"favicon.ico": 
                url = req_url
                ctype = "image/x-icon"

            elif req_url == b"music_info.json":
                url = "music_info.json"
                ctype = "text/json"
            elif req_url == b"listAllMusic.js":
                url = "listAllMusic.js"
                ctype = "text/javascript"
            else:
                url = req_url
                ctype = "text/html"

            if flag == 1:
                #print(param)
                with open(url, 'rb') as f:
                    data = f.read()
                    data = data % param
            elif flag == 2:
                #print(param)
                with open(url, 'rb') as f:
                    data = f.read()
                    data = data % tuple(param)
            else:
                url = urllib.parse.unquote(url)
                #print(url)
                with open(url, 'rb') as f:
                    data = f.read()
            
            header  = "HTTP/1.1 200\r\n"
            header += f"Content-length: {len(data)}\r\n"
            header += f"Content-Type: {ctype}\r\n\r\n"

            response = header.encode() + data
            client.send(response)
            client.close()
            return

if (len(sys.argv) != 3):
    print(f"[*] Usage: {sys.argv[0]} <hostname> <port>")
    exit(0)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.bind((HOST, PORT))
        print(f"[*] Successfully bind on {HOST}:{PORT}!")
    except Exception as e:
        print(f"[*] Error on bind: {e}")
        exit(0)

    try:
        s.listen()
        print(f"[*] Successfully listen on {HOST}:{PORT}!")
    except Exception as e:
        print(f"[*] Error on listen: {e}")
        exit(0)

    print(f"[*] Web successfully start on http://{HOST}:{PORT}")

    while True:
        client, caddr = s.accept()
        thread = threading.Thread(target=process, args=(client,caddr))
        thread.start()






