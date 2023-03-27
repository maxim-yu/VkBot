import urllib.request
import os


def create_temp_dir_if_not_exists():
    if 'dir_with_temp_files' not in os.listdir():
        os.makedirs('dir_with_temp_files')


def go_into_temp_dir():
    os.chdir('dir_with_temp_files')


def go_back_into_work_dir():
    os.chdir('../')


def download_photo_in_temp_dir(photo_list):
    go_into_temp_dir()
    for item in photo_list:
        url = item[0]
        file_name = item[1]
        load_link = urllib.request.urlopen(url).read()
        with open(f"{file_name}.jpg", "wb") as photo:
            photo.write(load_link)
    files_list = os.listdir()
    go_back_into_work_dir()
    return files_list


def remove_temporary_files():
    go_into_temp_dir()
    for file in os.listdir():
        os.remove(file)
    go_back_into_work_dir()


