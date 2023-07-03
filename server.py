import os
import music_tag
from file import File
import requests
from subprocess import call
from tqdm import tqdm


class Server:
    def __init__(self, pull_path, push_path):
        self.pull_path = pull_path
        self.push_path = push_path
        self.push_server = "Local"
        self.pull_server = "Local"

    def delete_locals(self, days):
        self._delete(days)

    def push(self, days):
        print(f"pushing streams to:{self.push_path}")
        for day in days:
            src = day.final_file.local_path
            cp_command = f"rsync -v '{src}' '{self.push_path}'"
            call(cp_command, shell=True)

    def _delete(self, days):
        for day in days:
            rm_command = f"rm {day.get_all_filenames()}"
            call(rm_command, shell=True)


    def pull(self, days):
        print(f"pulling streams to:{self.pull_path}")
        for day in days:
            self._download(day)

    def _download(self, day):
        for file in day.files:
            file.local_path = f"{self.pull_path}"
            self._save(file)
        final_path = self._concat_files(day)
        day.final_file = File(local_path=final_path)
        self.apply_tags(day)

    def apply_tags(self,day):
        # Apply new mp3 tags
        the_file = music_tag.load_file(day.final_file.local_path)
        the_file['artist'] = day.show.persons
        the_file['title'] = day.description
        the_file['album'] = day.show.station.title
        # set artwork
        day.show.logo.local_path = f"{self.pull_path}"
        self._save(day.show.logo)
        img_file = day.show.logo.local_path + day.show.logo.filename
        with open(img_file, 'rb') as img_in:
            the_file['artwork'] = img_in.read()
        the_file['artwork'].first.thumbnail([64, 64])
        the_file['artwork'].first.raw_thumbnail([64, 64])
        the_file.save()



    def _save(self, file):
        resume_byte_pos = 0
        the_file = file.local_path+file.filename
        if os.path.exists(the_file):
            resume_byte_pos = os.path.getsize(the_file)
        headers = {"Range":f"bytes={resume_byte_pos}-"}
        response = requests.get(file.url, headers=headers, stream=True)
        total_size = int(response.headers.get('content-length', 0)) + resume_byte_pos
        block_size = 1024  # 1 KB
        progress_bar = tqdm(total=total_size,
                            desc=file.filename,
                            unit='B',
                            initial=resume_byte_pos,
                            unit_scale=True,
                            colour='BLUE')

        with open(the_file, 'ab') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

        progress_bar.close()

    def _concat_files(self, day):
        final_filename = f"{self.pull_path}{day.description.replace('/','_')}.mp3"
        if len(day.files) > 1:
            ffmpeg_concat_string = "ffmpeg -hide_banner -loglevel error -y -i 'concat:"
            for file in day.files:
                ffmpeg_concat_string += f"{file.local_path}{file.filename}|"
            ffmpeg_concat_string = ffmpeg_concat_string[:-1]
            ffmpeg_concat_string += f"' -acodec copy '{final_filename}'"
            call(ffmpeg_concat_string, shell=True)
        else:
            src = final_filename
            cp_command = f"rsync -v '{src}' '{self.push_path}'"
            call(cp_command, shell=True)
        print("--------------------------------")
        return final_filename
