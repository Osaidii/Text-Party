import socket
import threading
import os
import json
import shutil
import threading

VERSION = "1.0"
HOST = "127.0.0.1"
PORT = 3467

party_lock = threading.Lock()

def handleClient(conn, addr):
    print(f"[+] Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"[-] Disconnected by {addr}")
                break
            line = data.decode("utf-8").strip()
            if not line:
                continue
            parts = line.split(":", 4)
            if parts[0] == "handshake":
                if len(parts) < 2:
                    conn.sendall(b"Invalid Request")
                    return
                if parts[1] != VERSION:
                    return conn.sendall(b"Wrong Version")
                sendGreeting(conn, addr)
            elif parts[0] == "create":
                createParty(conn, addr, parts)
            elif parts[0] == "destroy":
                destroyParty(conn, addr, parts)
            elif parts[0] == "join":
                joinParty(conn, addr, parts)
            elif parts[0] == "leave":
                leaveParty(conn, addr, parts)
            elif parts[0] == "update":
                askedForUpdate(conn, addr, parts)
            else:
                print(f"Unknown Request from {addr}: {data}")
                conn.sendall(b"Unknown Request")
    except ConnectionResetError:
        print(f"[-] Connection reset by {addr}")
    except OSError as e:
        print(f"[-] SocketError from {addr}: {e}")
    
def sendGreeting(conn, addr):
    status = b"Hello"
    conn.sendall(status)
    print(f"[+] Sent greeting to {addr}")

def createParty(conn, addr, parts):
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid Request")
        print(f"[-] Invalid create request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    name = parts[3]
    if party_code is None or party_code == "" or password is None or password == "" or name is None or name == "":
        conn.sendall(b"Invalid Request")
        return
    if not (party_code.isdigit() and len(party_code) == 6):
        conn.sendall(b"Invalid Request")
        return
    try:
        os.makedirs(f"parties/{party_code}", exist_ok=False)
    except FileExistsError:
        conn.sendall(b"Code Taken")
        return
    try:
        with party_lock:
            with open(f"parties/{party_code}/info.json", "w") as f:
                json.dump({"code": party_code, "password": password, "host": name, "members": [name]}, f)
        conn.sendall(b"Party Created")
    except OSError as e:
        print(f"[-] Error creating party for {addr}: {e}")
        conn.sendall(b"Error: Could not create party")
        return
    print(f"[+] Party created by {addr}: Code={party_code}, Password={password}, Name={name}")

def destroyParty(conn, addr, parts):
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid Request")
        print(f"[-] Invalid destroy request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    name = parts[3]
    if not (party_code.isdigit() and len(party_code) == 6):
        conn.sendall(b"Invalid Request")
        return
    try:
        with party_lock:
            with open(f"parties/{party_code}/info.json", "r") as f:
                info = json.load(f)
        if info["password"] != password or info["host"] != name:
            conn.sendall(b"Invalid Request")
            return
        shutil.rmtree(f"parties/{party_code}")
        conn.sendall(b"Party Destroyed")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error destroying party for {addr}: {e}")
        conn.sendall(b"Error: Could not destroy party")
        return
    print(f"[+] Party destroyed by {addr}: Code={party_code}")

def joinParty(conn, addr, parts):
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid Request")
        print(f"[-] Invalid join request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    try:
        with party_lock:
            with open(f"parties/{party_code}/info.json", "r") as f:
                t = json.load(f)
        if t["password"] != password:
            conn.sendall(b"Invalid Request")
            return
        new_name = parts[3]
        if new_name in t["members"]:
            conn.sendall(b"Name Already Exists")
            return
        if new_name not in t["members"]:
            t["members"].append(new_name)
        with party_lock:
            with open(f"parties/{party_code}/info.json", "w") as f:
                json.dump(t, f)
        conn.sendall(b"Joined Party")
    except FileNotFoundError:
        conn.sendall(b"Invalid Code")
        return
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error joining party for {addr}: {e}")
        conn.sendall(b"Error: Could not join party")
        return
    print(f"[+] Party joined by {addr}: Code={party_code}")

def leaveParty(conn, addr, parts):
    if len(parts) != 3:
        conn.sendall(b"Error: Invalid Request")
        print(f"[-] Invalid leave request from {addr}: {parts}")
        return
    party_code = parts[1]
    name = parts[2]
    if not (party_code.isdigit() and len(party_code) == 6):
        conn.sendall(b"Invalid Request")
        return
    try:
        with party_lock:
            with open(f"parties/{party_code}/info.json", "r") as f:
                t = json.load(f)
        if name not in t["members"]:
            conn.sendall(b"Error: Member not found")
            return
        t["members"].remove(name)
        if name == t["host"]:
            t["host"] = t["members"][0] if t["members"] else ""
        with party_lock:
            with open(f"parties/{party_code}/info.json", "w") as f:
                json.dump(t, f)
        conn.sendall(b"Left Party")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error leaving party for {addr}: {e}")
        conn.sendall(b"Error: Could not leave party")
        return
    print(f"[+] Party left by {addr}: Code={party_code}, Name={name}")

def askedForUpdate(conn, addr, parts):
    if len(parts) != 3:
        conn.sendall(b"Invalid Request")
        print(f"[-] Invalid Update request from {addr}: {parts}")
        return
    party_code = parts[1]
    name = parts[2]
    if not (party_code.isdigit() and len(party_code) == 6):
        conn.sendall(b"Invalid Request")
        return
    try:
        with party_lock:
            with open(f"parties/{party_code}/info.json") as f:
                t = json.load(f)
    except (OSError, json.JSONDecodeError):
        conn.sendall(b"Destroyed")
        return
    if name == t["host"]:
        conn.sendall(b"New Host")
        return
    conn.sendall(b"Alive")

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

if __name__ == "__main__":
    main()