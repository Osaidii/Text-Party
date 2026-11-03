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
            if not data:
                print(f"[-] Disconnected by {addr}")
                break
            line = data.decode("utf-8").strip()
            parts = line.split(":")
            if parts[0] == "handshake":
                sendGreeting(conn, addr)
            elif parts[0] == "create":
                createParty(conn, addr, parts)
            elif parts[0] == "destroy":
                destroyParty(conn, addr, parts)
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
        os.makedirs(f"parties/{party_code}", exist_ok=True)
        with open(f"parties/{party_code}/info.json", "w") as f:
            json.dump({"code": party_code, "password": password, "host": name}, f)
        conn.sendall(b"party created")
    except OSError as e:
        print(f"[-] Error creating party for {addr}: {e}")
        conn.sendall(b"Error: Could not create party")
        return
    print(f"[+] Party created by {addr}: Code={party_code}, Password={password}, Name={name}")

def destroyParty(conn, addr, parts):
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid destroy request")
        print(f"[-] Invalid destroy request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    name = parts[3]
    try:
        with open(f"parties/{party_code}/info.json", "r") as f:
            info = json.load(f)
        if info["password"] != password:
            conn.sendall(b"invalid password")
            return
        if info["host"] != name:
            conn.sendall(b"invalid host")
            return
        os.remove(f"parties/{party_code}/info.json")
        os.rmdir(f"parties/{party_code}")
        conn.sendall(b"party destroyed")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error destroying party for {addr}: {e}")
        conn.sendall(b"Error: Could not destroy party")
        return
    print(f"[+] Party destroyed by {addr}: Code={party_code}")

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