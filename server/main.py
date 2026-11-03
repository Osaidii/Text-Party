import socket
import threading
import os
import json

HOST = "127.0.0.1"
PORT = 3467

def handleClient(conn, addr):
    print(f"[+] Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            print(f"[DEBUG] recv raw={data!r}")
            if not data:
                print(f"[-] Disconnected by {addr}")
                break
            line = data.decode("utf-8").strip()
            parts = line.split(":")
            print(f"[DEBUG] line={line!r}")
            print(f"[DEBUG] parts={parts!r}  (len={len(parts)})")
            print(f"[DEBUG] parts[0]={parts[0]!r}  type={type(parts[0]).__name__}")
            print(f"[DEBUG] is handshake? {parts[0] == 'handshake'}")
            print(f"[DEBUG] is create?    {parts[0] == 'create'}")
            if parts[0] == "handshake":
                sendGreeting(conn, addr)
            elif parts[0] == "create":
                createParty(conn, addr, parts)
            else:
                print(f"Unknown Request from {addr}: {data}")
                conn.sendall(b"Unknown Request")
    except ConnectionResetError:
        print(f"[-] Connection reset by {addr}")
    except OSError as e:
        print(f"[-] SocketError from {addr}: {e}")
    finally:
        conn.close()
    
def sendGreeting(conn, addr):
    status = b"Hello"
    conn.sendall(status)
    print(f"[+] Sent greeting to {addr}")

def createParty(conn, addr, parts):
    print("hello")
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid create request")
        print(f"[-] Invalid create request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    name = parts[3]
    try:
        with open(f"parties/{party_code}.json", "w") as f:
            json.dump({"code": party_code, "password": password, "host": name}, f)
        conn.sendall(b"Party Created")
    except OSError as e:
        print(f"[-] Error creating party for {addr}: {e}")
        conn.sendall(b"Error: Could not create party")
        return
    print(f"[+] Party created by {addr}: Code={party_code}, Password={password}, Name={name}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[+] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handleClient, args=(conn, addr))
            t.start()
    except KeyboardInterrupt:
        print(f"[-] Server stopped.")
    finally:
        server.close()

if 5 > 4:
    main()