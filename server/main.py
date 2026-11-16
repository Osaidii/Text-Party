import socket
import threading
import os
import json
import shutil
import threading
import time
import random
import base64

VERSION = "1.0"
HOST = "0.0.0.0"
PORT = 3467
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

active_conns = 0
max_conns = 50
party_lock = threading.Lock()

subs = {}

def handleClient(conn, addr):
    global active_conns
    try:
        conn.settimeout(120.0)
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
                elif parts[0] == "edit":
                    handleEdit(conn, addr, parts)
                else:
                    print(f"Unknown Request from {addr}: {data}")
                    conn.sendall(b"Unknown Request")
        except socket.timeout:
            print(f"[-] Timeout from {addr}")
        except ConnectionResetError:
            print(f"[-] Connection reset by {addr}")
        except OSError as e:
            print(f"[-] SocketError from {addr}: {e}")
    finally:
        with party_lock:
            active_conns -= 1
        with party_lock:
            for party_list in subs.values():
                if conn in party_list:
                    party_list.remove(conn)
        conn.close()
    
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
        os.makedirs(os.path.join(BASE_DIR, "parties", party_code), exist_ok=False)
    except FileExistsError:
        conn.sendall(b"Code Taken")
        return
    try:
        with party_lock:
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json"), "w") as f:
                json.dump({"code": party_code, "password": password, "host": name, "members": [name]}, f)
            with open(os.path.join(BASE_DIR, "parties", party_code, "text.txt"), "w") as f:
                f.write("")
        conn.sendall(b"Party Created")
    except OSError as e:
        print(f"[-] Error creating party for {addr}: {e}")
        conn.sendall(b"Error: Could not create party")
        return
    print(f"[+] Party created by {addr}: Code={party_code}, Password={password}, Name={name}")
    updateFolderMTime(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__))), "parties", party_code))

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
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json"), "r") as f:
                info = json.load(f)
        if info["password"] != password or info["host"] != name:
            conn.sendall(b"Invalid Request")
            return
        shutil.rmtree(os.path.join(BASE_DIR, "parties", party_code))
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
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json"), "r") as f:
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
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json"), "w") as f:
                json.dump(t, f)
                updateFolderMTime(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__))), "parties", party_code))
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
    if len(parts) != 4:
        conn.sendall(b"Error: Invalid Request")
        print(f"[-] Invalid leave request from {addr}: {parts}")
        return
    party_code = parts[1]
    party_password = parts[2]
    name = parts[3]
    if not (party_code.isdigit() and len(party_code) == 6):
        conn.sendall(b"Invalid Request")
        return
    try:
        with party_lock:
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json"), "r") as f:
                t = json.load(f)
        if party_password != t["password"]:
            conn.sendall(b"Invalid Request")
            return
        if name not in t["members"]:
            conn.sendall(b"Error: Member not found")
            return
        t["members"].remove(name)
        if name == t["host"]:
            t["host"] = t["members"][0] if t["members"] else ""
        with party_lock:
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json"), "w") as f:
                json.dump(t, f)
                updateFolderMTime(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__))), "parties", party_code))
        conn.sendall(b"Left Party")
    except (OSError, json.JSONDecodeError) as e:
        print(f"[-] Error leaving party for {addr}: {e}")
        conn.sendall(b"Error: Could not leave party")
        return
    print(f"[+] Party left by {addr}: Code={party_code}, Name={name}")

def askedForUpdate(conn, addr, parts):
    if len(parts) != 3:
        conn.sendall(b"Invalid Request\n")
        print(f"[-] Invalid Update request from {addr}: {parts}")
        return
    party_code = parts[1]
    name = parts[2]
    if not (party_code.isdigit() and len(party_code) == 6):
        conn.sendall(b"Invalid Request\n")
        return
    try:
        with party_lock:
            with open(os.path.join(BASE_DIR, "parties", party_code, "info.json")) as f:
                t = json.load(f)
    except (OSError, json.JSONDecodeError):
        conn.sendall(b"Destroyed\n")
        return
    try:
        with open(os.path.join(BASE_DIR, "parties", party_code, "text.txt"), encoding="utf-8") as f:
            current = f.read()
        b64 = base64.b64encode(current.encode()).decode()
        conn.sendall(f"text:{b64}\n".encode())
    except OSError:
        conn.sendall(b"text:\n")
    if name == t["host"]:
        conn.sendall(b"New Host\n")
    else:
        conn.sendall(b"Alive\n")
    conn.settimeout(None)
    with party_lock:
        subs.setdefault(party_code, []).append(conn)

def handleEdit(conn, addr, parts):
    print(f"[EDIT] received: {parts}")
    kind, index = parts[1], int(parts[2])
    with party_lock:
        party_code = next((c for c, l in subs.items() if conn in l), None)
        with open(os.path.join(BASE_DIR, "parties", party_code, "text.txt"), encoding="utf-8") as f:
            current = f.read()
    if kind == "add":
        text = base64.b64decode(parts[3]).decode("utf-8")
        new_text = current[:index] + text + current[index:]
    else:
        new_text = current[:index] + current[index + int(parts[3]):]
    with party_lock:
        with open(os.path.join(BASE_DIR, "parties", party_code, "text.txt"), "w", encoding="utf-8" ) as f:
            f.write(new_text)
        for c in subs.get(party_code, []):
            if c is not conn:
                try: c.sendall(("edit:" + ":".join(parts[1:]) + "\n").encode("utf-8"))
                except OSError: pass
    print(f"[+] Edit from {addr}: {parts}")
    conn.sendall(b"OK\n")

def deleteInactiveParties():
    while True:
        try:
            self_dir = os.path.dirname(os.path.abspath(__file__))
            parties_dir = os.path.join(self_dir, "parties")
            dirs = [e.name for e in os.scandir(parties_dir) if e.is_dir()]
            for i in dirs:
                seconds_ago = time.time() - os.path.getmtime(os.path.join(parties_dir, i))
                if seconds_ago > 3600:
                    shutil.rmtree(os.path.join(parties_dir, i))
        except FileNotFoundError:
            pass
        time.sleep(600)

def updateFolderMTime(dir):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.~:"
    random_string = ''.join(random.choice(chars) for _ in range(15))
    temp_path = os.path.join(dir, random_string)
    try:
        with open(temp_path, "x"):
            pass
        os.remove(temp_path)
    except OSError:
        pass

def main():
    global active_conns, max_conns
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[+] Listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            with party_lock:
                if active_conns >= max_conns:
                    conn.close()
                    continue
                active_conns += 1
            t = threading.Thread(target=handleClient, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print(f"[-] Server stopped.") 
    finally:
        server.close()

if __name__ == "__main__":
    threading.Thread(target=deleteInactiveParties, daemon=True).start()
    main()