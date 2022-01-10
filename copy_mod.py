#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cp_progress(source, destination)

I made this to give shutil.copy() [or shutil.copy2() in this case] a progress bar.

You can use cp_progress(source, destination) just like shutil.copy(src, dst). source must be a file path and
destination a file or folder path.

It will give you a progress bar for each file copied. Just copy this code above the place where you want to use
cp_progress(source, destination) in your code.

You can easily change the look of the progress bar: - To keep the style and just change the colors, replace the
colors values of progressCOLOR and finalCOLOR (orange code at the end of the lines). - The use a solid block progress
bar, # -*- coding: utf-8 -*- is required. Otherwise, you will get an encoding error. Some basic terminals,
like xterm, may not show the progress bar because of the utf-8 characters. To use this style, remove the comments
#STYLE# in lines ###COLORS### - BlueCOLOR and endBLOCK. In def get_percent_progress() remove the comments  #STYLE#
AND COMMENT THE PREVIOUS line. Do the same in def cp_progress() If you don't want the utf-8 encoding, delete the four
lines beginning with #STYLE#.

NOTE: If you want to copy lots of small files, the copy process for file is so fast
      that all you will see is a lot of lines scrolling in you terminal window - not enough time for a 'progress'.
      In that case, I use an overall progress that shows only one progress bar to the complete job.   nzX
"""
import os
import shutil
import sys
import threading
import time

import hashlib

# COLORS

progressCOLOR = '\033[38;5;33;48;5;236m'
# \033[38;5;33;48;5;236m# copy inside '' for colored progressbar| orange:#\033[38;5;208;48;5;235m
finalCOLOR = '\033[38;5;33;48;5;33m'
# \033[38;5;33;48;5;33m# copy inside '' for colored progressbar| orange:#\033[38;5;208;48;5;208m
# STYLE#BlueCOLOR = '\033[38;5;33m'
# #\033[38;5;33m# copy inside '' for colored progressbar Orange#'\033[38;5;208m'# # BG progress# #STYLE#
# STYLE#endBLOCK = ''
# ▌ copy OR '' for none # BG progress# #STYLE# requires utf8 coding header
########

BOLD = '\033[1m'
UNDERLINE = '\033[4m'
CEND = '\033[0m'


def get_percent_progress(source_path, destination_path):
    time.sleep(.24)
    if os.path.exists(destination_path):
        source_size = os.path.getsize(source_path)
        source_size_printable = int(source_size / 1000000)
        while source_size != os.path.getsize(destination_path):
            percentage_done = int(
                (float(os.path.getsize(destination_path)) / float(source_size)) * 100)
            steps = int(percentage_done / 5)
            copied_size_printable = int(os.path.getsize(
                destination_path) / 1000000)  # Should be 1024000 but this get's equal to Thunar file manager report
            # (Linux - Xfce)

            sys.stdout.write('\r')
            sys.stdout.write(("         {:d} / {:d} Mb   ".format(copied_size_printable, source_size_printable)) + (
                    BOLD + progressCOLOR + "{:20s}".format('|' * steps) + CEND) + (
                                 "   {:d}% ".format(percentage_done)))  # BG progress
            # STYLE#sys.stdout.write(("         {:d} / {:d} Mb   ".format(copied_size_printable,
            # source_size_printable)) +  (BOLD + BlueCOLOR + "▐" + "{:s}".format('█'*steps) + CEND) + ("{:s}".format(
            # ' '*(20-steps))+ BOLD + BlueCOLOR + endBLOCK+ CEND) +("   {:d}% ".format(percentage_done))) #STYLE# #
            # BG progress# closer to GUI but less compatible (no block bar with xterm) # requires utf8 coding header
            sys.stdout.flush()
            time.sleep(.01)


def cp_progress(source, destination):
    if os.path.isdir(destination):
        dst_file = os.path.join(destination, os.path.basename(source))
    else:
        dst_file = destination
    print(" ")
    print(BOLD + UNDERLINE + "FROM:" + CEND + "   ", source)
    print(BOLD + UNDERLINE + "TO:" + CEND + "     ", dst_file)
    print(" ")
    threading.Thread(name='progress_bar', target=get_percent_progress, args=(source, dst_file)).start()
    shutil.copy2(source, destination)
    time.sleep(.02)
    sys.stdout.write('\r')
    sys.stdout.write(("         {:d} / {:d} Mb   ".format((int(os.path.getsize(dst_file) / 1000000)),
                                                          (int(os.path.getsize(source) / 1000000)))) + (
                             BOLD + finalCOLOR + "{:20s}".format('|' * 20) + CEND) + (
                         "   {:d}% ".format(100)))  # BG progress 100%
    # STYLE#sys.stdout.write(("         {:d} / {:d} Mb   ".format((int(os.path.getsize(dst_file)/1000000)),
    # (int(os.path.getsize(source)/1000000)))) +  (BOLD + BlueCOLOR + "▐" + "{:s}{:s}".format(('█'*20), endBLOCK) +
    # CEND) + ("   {:d}% ".format(100))) #STYLE# # BG progress 100%# closer to GUI but less compatible (no block bar
    # with xterm) # requires utf8 coding header
    sys.stdout.flush()
    print(" ")
    print(" ")


'''
#Ex. Copy all files from root of the source dir to destination dir

folderA = '/path/to/source' # source
folderB = '/path/to/destination' # destination
for FILE in os.listdir(folderA):
    if not os.path.isdir(os.path.join(folderA, FILE)):
        if os.path.exists(os.path.join(folderB, FILE)): continue 
        # as we are using shutil.copy2() that overwrites destination, this skips existing files
        cp_progress(os.path.join(folderA, FILE), folderB) 
        # use the command as if it was shutil.copy2() but with progress


         75 / 150 Mb  ||||||||||         |  50%
'''


def get_file_hash_sha256(target_file):
    # BUF_SIZE is totally arbitrary, change for your app!
    buf_size = 16 * 1024 * 1024  # lets read stuff in 16mb chunks!

    source_size = os.path.getsize(target_file)
    source_size_printable = int(source_size / 1000000)

    read_size = 0
    sha256 = hashlib.sha256()

    with open(target_file, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            sha256.update(data)

            read_size += buf_size
            percentage_done = int((float(read_size) / float(source_size)) * 100)
            steps = int(percentage_done / 5)
            read_size_printable = int(read_size / 1000000)

            sys.stdout.write('\r')
            sys.stdout.write(("         {:d} / {:d} Mb   ".format(read_size_printable, source_size_printable)) + (
                    BOLD + progressCOLOR + "{:20s}".format('|' * steps) + CEND) + (
                                 "   {:d}% ".format(percentage_done)))
            sys.stdout.flush()

    # print("SHA1: {0}".format(sha256.hexdigest()))

    sys.stdout.write('\r')
    sys.stdout.write(("         {:d} / {:d} Mb   ".format(source_size_printable, source_size_printable)) + (
            BOLD + finalCOLOR + "{:20s}".format('|' * 20) + CEND) + (
                         "   {:d}% ".format(100)))

    result_hash = sha256.hexdigest()
    print('\n')
    print('Hash calculated!', result_hash)
    return result_hash


# cp_progress(os.path.join('\\\\filegs.light.local\\1c_full_bak$\\ut_2019_prod',
#                          'ut_2019_prod_backup_2022_01_02_021245_1894637.trn'),
#             'C:\\Users\\krabs\\Desktop\\bak')
# get_file_hash_sha256(os.path.join('C:\\Users\\krabs\\Desktop\\bak',
#                                   'ut_2019_prod_backup_2022_01_02_021245_1894637.trn'))
