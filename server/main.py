import socket
import threading
import os
import json
import shutil

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
            parts = line.split(":", 4)
            if parts[0] == "handshake":
                sendGreeting(conn, addr)
            elif parts[0] == "create":
                createParty(conn, addr, parts)
            elif parts[0] == "destroy":
                destroyParty(conn, addr, parts)
            elif parts[0] == "join":
                joinParty(conn, addr, parts)
            elif parts[0] == "leave":
                leaveParty(conn, addr, parts)
            elif parts[0] == "remove":
                removeMember(conn, addr, parts)
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
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid create request")
        print(f"[-] Invalid create request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    name = parts[3]
    try:
        if os.path.exists(f"parties/{party_code}"):
            conn.sendall(b"Code Taken")
            return
        os.makedirs(f"parties/{party_code}")
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
            conn.sendall(b"Invalid Password")
            return
        if info["host"] != name:
            conn.sendall(b"Invalid Host")
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
        conn.sendall(b"Error: Invalid join request")
        print(f"[-] Invalid join request from {addr}: {parts}")
        return
    party_code = parts[1]
    password = parts[2]
    try:
        with open(f"parties/{party_code}/info.json", "r") as f:
            t = json.load(f)
            t["members"] = parts[3:]
        if t["password"] != password:
            conn.sendall(b"Invalid Password")
            return
        conn.sendall(b"Joined Party")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error joining party for {addr}: {e}")
        conn.sendall(b"Error: Could not join party")
        return
    print(f"[+] Party joined by {addr}: Code={party_code}")

def leaveParty(conn, addr, parts):
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid leave request")
        print(f"[-] Invalid leave request from {addr}: {parts}")
        return
    party_code = parts[1]
    name = parts[2]
    try:
        with open(f"parties/{party_code}/info.json", "r") as f:
            t = json.load(f)
            if name in t["members"]:
                t["members"].remove(name)
            else:
                conn.sendall(b"Error: Member not found")
                return
        with open(f"parties/{party_code}/info.json", "w") as f:
            json.dump(t, f)
        conn.sendall(b"Left Party")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error leaving party for {addr}: {e}")
        conn.sendall(b"Error: Could not leave party")
        return
    print(f"[+] Party left by {addr}: Code={party_code}, Name={name}")

def removeMember(conn, addr, parts):
    if len(parts) != 5:
        conn.sendall(b"Erorr: Invalid remove request")
        print(f"[-] Invalid leave request from {addr}: {parts}")
        return
    party_code = parts[1]
    party_pasword = parts[2]
    party_name = parts[3]
    target_name = parts[4]
    try:
        with open(f"parties/{party_code}/info.json", "r") as f:
            t = json.load(f)
            if t.host != party_name:
                conn.sendall(b"Is not Host")
                return
            elif target_name in t["members"]:
                t["members"].remove(target_name)
            else:
                conn.sendall(b"Error: Member not found")
                return
        with open(f"parties/{party_code}/info.json", "w") as f:
            json.dump(t, f)
        conn.sendall(b"Removed Member")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error removing member for {addr}: {e}")
        conn.sendall(b"Error: Could not remove member")
        return
    print(f"[+] Member removed by {addr}: Code={party_code}, Name={target_name}")

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