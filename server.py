import os
from subprocess import call
from file import File
import threading



class Server:
    def __init__(self, pull_path, push_path):
        self.pull_path = pull_path if pull_path.endswith("/") else f"{pull_path}/"
        self.push_path = push_path if push_path.endswith("/") else f"{push_path}/"
        self.push_server = "Local"
        self.pull_server = "Local"

    def pull(self, days):
        print(f"pulling streams to:{self.pull_path}")
        for day in days:
            day.downloader(day, self.pull_path)

    def push(self, days, delete=True):
        def _push():
            for day in days:
                src = f"{self.pull_path}{day.final_file.filename}"
                cp_command = f"rsync -v '{src}' '{self.push_path}'"
                call(cp_command, shell=True)
            if delete:
                self.delete_locals(days)
        print(f"pushing streams to:{self.push_path}")
        push_thread = threading.Thread(target=_push)
        push_thread.start()

    def delete_locals(self, days):
        for day in days:
            all_files = day.get_all_filenames()
            all_files.append(day.final_file.filename)
            for a_file in all_files:
                to_delete = f"{self.pull_path}{a_file}"
                if os.path.isfile(to_delete) and os.path.exists(to_delete):
                    os.remove(to_delete)
