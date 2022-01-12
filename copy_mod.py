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
import logging
import hashlib


def get_percent_progress(source_path, destination_path):
    backups_logger = logging.getLogger('backups_main_log')
    time.sleep(.24)
    if os.path.exists(destination_path):
        source_size = os.path.getsize(source_path)
        source_size_printable = int(source_size / 1000000)
        while source_size != os.path.getsize(destination_path):
            percentage_done = int(
                (float(os.path.getsize(destination_path)) / float(source_size)) * 100)
            steps = int(percentage_done / 5)
            copied_size = os.path.getsize(destination_path)
            copied_size_printable = int(copied_size / 1000000)
            # Should be 1024000 but this get's equal to Thunar file manager report (Linux - Xfce)
            backups_logger.debug('Copied ' + str(copied_size) + ' of ' + str(source_size) +
                                 ' (' + str(percentage_done) + '%)')
            sys.stdout.write(("\r         {:d} / {:d} Mb   ".format(copied_size_printable, source_size_printable)) + (
                "{:20s}".format('|' * steps)) + ("   {:d}% ".format(percentage_done)))  # BG progress
            sys.stdout.flush()
            time.sleep(.5)


def cp_progress(source, destination):
    backups_logger = logging.getLogger('backups_main_log')
    if os.path.isdir(destination):
        dst_file = os.path.join(destination, os.path.basename(source))
    else:
        dst_file = destination
    backups_logger.info("FROM:   " + str(source))
    backups_logger.info("TO:     " + str(dst_file))
    threading.Thread(name='progress_bar', target=get_percent_progress, args=(source, dst_file)).start()
    shutil.copy2(source, destination)
    backups_logger.info("File copied!")
    time.sleep(.02)
    sys.stdout.write(("\r         {:d} / {:d} Mb   ".format((int(os.path.getsize(dst_file) / 1000000)),
                                                            (int(os.path.getsize(source) / 1000000)))) + (
                         "{:20s}".format('|' * 20)) + (
                         "   {:d}% \n".format(100)))  # BG progress 100%
    sys.stdout.flush()


def get_file_hash_sha256(target_file):
    # BUF_SIZE is totally arbitrary, change for your app!
    buf_size = 32 * 1024 * 1024  # lets read stuff in 16mb chunks!
    backups_logger = logging.getLogger('backups_main_log')
    backups_logger.info('Calculating hash of ' + str(target_file))
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
            backups_logger.debug('Processed ' + str(read_size) + ' of ' + str(source_size) +
                                 ' (' + str(percentage_done) + '%)')
            sys.stdout.write(("\r         {:d} / {:d} Mb   ".format(read_size_printable, source_size_printable)) + (
                "{:20s}".format('|' * steps)) + ("   {:d}% ".format(percentage_done)))
            sys.stdout.flush()

    sys.stdout.write(("\r         {:d} / {:d} Mb   ".format(source_size_printable, source_size_printable)) + (
        "{:20s}".format('|' * 20)) + ("   {:d}% \n".format(100)))

    result_hash = sha256.hexdigest()
    backups_logger.info('Hash calculated! ' + str(result_hash))
    return result_hash
