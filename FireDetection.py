# Purpose: Input images or video and detect fire, if detected connect to FTP server and send the Image with BBbox, GPS location
import os
import sys
import glob
import datetime
import time
import torch
from ftplib import FTP_TLS

# Purpose: Initial configuration for the ftp and yolov5
HOSTNAME = '192.168.1.14'
USERNAME = 'anish'
PASSWORD = 'anonomous'

WEIGHT_PATH = './models/best.pt'
IMAGE_PATH = 'mpv-shot0001.jpg'
PATH_TO_YOLO = './yolov5/'
OUTPUT = 'output'
folder_ext = '000'
current_longitude = 38.001451
current_latitude = 23.668016

sys.path.append(PATH_TO_YOLO)


# Purpose: Utility function for ftp and fire detection
def connect_ftp_server(host_address, username, passwd, port=4444):
    ftp_server = FTP_TLS()
    ftp_server.connect(host_address, port)
    # force UTF-8 encoding
    ftp_server.encoding = "utf-8"
    return ftp_server


def upload_file_to_ftp(filename_path):
    # Read file in binary mode
    with open(filename_path, "rb") as file:
        # extract the file name
        try:
            filename_path = filename_path.split('/')[-1]
        except:
            pass
        #upload the file to the server
        ftp_server.storbinary(f"STOR {filename_path}", file)


def download_file_from_ftp(filename_path):
    with open(filename_path, 'wb') as file:
        ftp_server.retrbinary(f"RETR {filename_path}", file.write)


def append_content_to_file(filename_path, in_content):
    with open(filename_path, 'a') as f:
        f.write(in_content)


def read_file(filename_path):
    file = open(filename_path, "r")
    print('File Content:', file.read())
    return file


# Check the folder number and get the highest folder number, list sort didn't work for this.
def get_latest_folder(folders):
    highest = 0
    latest_out_folder = ''
    for folder_name in folders:
        if int(folder_name.split('/')[-1]) > highest:
            highest = int(folder_name.split('/')[-1])
            latest_out_folder = folder_name
    return latest_out_folder


def get_fire_detection_output(in_outfolder):
    folders = glob.glob(in_outfolder + "*")
    folders.sort()
    latest_out_folder = get_latest_folder(folders)

    try:
        # Check if there are any bbox label if yes we have detected fire else no fire
        output_bbox = glob.glob(latest_out_folder + '/labels/*')
        if len(output_bbox) > 0:
            return latest_out_folder + '/' + IMAGE_PATH
        else:
            return ""
    except:
        print('No fire detected')


def detect_fire(input_files):
    os.system(f'python3 {PATH_TO_YOLO}/detect.py --weights {WEIGHT_PATH} \
        --img 640 --conf 0.2 --source {input_files} --save-txt --project={OUTPUT} --name {folder_ext}'
              )


# Purpose: Connect to ftp server and download the evenlist.csv file
ftp_server = connect_ftp_server(HOSTNAME, USERNAME, PASSWORD)
download_file_from_ftp('EventList.csv')
# Purpose: detect fire in the given image
detect_fire('./mpv-shot0001.jpg')
detect_fire('./no_fire.png')

# Purpose: Check the latest output file and see if there is any fire detection, if yes get the file path
latest_out = get_fire_detection_output(OUTPUT + '/' + folder_ext)
print(latest_out)

# Purpose: If fire is detected upload it and create a new event in event list
if len(latest_out) > 0:
    upload_file_to_ftp(latest_out)
    text = f"\n1005,Fire, fire, {current_longitude}, {current_latitude}, http://{HOSTNAME}:8000/{latest_out.split('/')[-1]}"
    append_content_to_file('EventList.csv', text)
    upload_file_to_ftp('EventList.csv')
