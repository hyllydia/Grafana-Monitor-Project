# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 0:02
# @Author  : Yuling Hou
# @File    : delete_syslog_files.py
# @Software: PyCharm
import os
import time
import subprocess

def delete_files_in_directory(directory):
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            elif os.path.isdir(file_path):
                print(f"Skipping directory: {file_path}")
            else:
                print(f"Unknown file type: {file_path}")
    except Exception as e:
        print(f"Error deleting files: {e}")

def restart_rsyslog_service():
    try:
        subprocess.run(['systemctl', 'restart', 'rsyslog'], check=True)
        print("rsyslog service successfully restarted")
    except subprocess.CalledProcessError as e:
        print(f"Error restarting rsyslog service: {e}")

if __name__ == "__main__":
    log_directory = "/var/log/rsyslog"

    # Run every 10 days
    interval_days = 10
    interval_seconds = interval_days * 24 * 60 * 60

    while True:
        delete_files_in_directory(log_directory)
        restart_rsyslog_service()
        print(f"Waiting {interval_days} days before next cleanup...")
        time.sleep(interval_seconds)
