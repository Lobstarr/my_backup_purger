from math import ceil
from pathlib import Path
from datetime import datetime
import configparser
import os

today = datetime.now()

config = configparser.ConfigParser()
config.read('bak_config.ini')
# The target directory
target_dir = config['files']['target_dir']
# Glob pattern for matching files (so that you select only what you want)
glob_pattern = config['files']['glob_pattern']
# Pattern for extracting date out of the filenames (gets passed to datetime.strptime)
date_pattern_text = config['files']['date_pattern_text']
date_pattern_text_len = len(date_pattern_text)
date_pattern = config['files']['date_pattern']

extensions = config['files']['extensions']
if ';' in extensions:
    extensions = extensions.split(';')
else:
    extensions = [extensions]
all_storage_settings = []
for filetype in extensions:
    if filetype not in config:
        print('No config for ' + filetype + '!')
        continue
    all_storage_settings.append({
        'filetype': filetype,
        'keep_last': int(config[filetype]['keep_last']),
        'keep_weeks': int(config[filetype]['keep_weeks']),
        'keep_months': int(config[filetype]['keep_months']),
        'keep_years': int(config[filetype]['keep_years'])
    })

dry_run = config['global'].getboolean('dry_run')


def get_files(target, file_ext):
    path = Path(target)
    files = [file for file in path.glob(glob_pattern) if file.is_file() and os.path.splitext(file)[1] == file_ext]
    # files = [file for file in path.glob(glob_pattern) if file.is_file()]
    # for file in files:
    #     print(os.path.splitext(file))
    files.sort(reverse=True)

    return files


def get_week(date, year_start=datetime.now().year - 1):
    today_yday = get_yday(date, year_start)
    start_weekday = date.replace(day=1, month=1, year=year_start).weekday()

    return ceil((today_yday + start_weekday) / 7)


def get_month(date, year_start=datetime.now().year - 1):
    return date.month + (date.year - year_start) * 12


def get_yday(date, year_start=datetime.now().year - 1):
    today_yday = date.timetuple().tm_yday
    # prev_year_days = today_date.replace(day=31, month=12, year=year_start).timetuple().tm_yday
    for i in range(1, date.year - year_start + 1):
        prev_year_days = date.replace(day=31, month=12, year=date.year - i).timetuple().tm_yday
        today_yday = prev_year_days + today_yday

    return today_yday


def get_files_to_keep(files, storage_settings):
    start_year = today.year - 1
    today_yday = get_yday(today, start_year)
    today_week = get_week(today, start_year)
    today_month = get_month(today, start_year)
    keep_files = {'last': [], 'weeks': {}, 'months': {}, 'years': {}}
    count = 0

    for file in files:

        try:
            date = datetime.strptime(file.name[0:date_pattern_text_len], date_pattern)
            parsed_file = {
                'date': date,
                'week': get_week(date, start_year),
                'month': get_month(date, start_year),
                'year': date.year,
                'path': file}
        except ValueError:
            print(f'Failed reading date from "{file.name}", skipping')
            continue

        if count < storage_settings['keep_last']:

            keep_files['last'].append(file)
            # print(f'{count} out of last {keep_last} that are always kept')
            today_week = parsed_file['week']

        elif parsed_file['week'] > today_week - storage_settings['keep_weeks'] and storage_settings['keep_weeks'] > 0:

            keep_week_index = parsed_file['week'] - (today_week - storage_settings['keep_weeks'])
            keep_files['weeks'][keep_week_index] = file
            # print('File of week', file['week'], '(keeping week', keep_week_index, 'out of', keep_weeks,')')
            today_month = parsed_file['month']

        elif parsed_file['month'] > today_month - storage_settings['keep_months'] and \
                storage_settings['keep_months'] > 0:

            keep_month_index = parsed_file['month'] - (today_month - storage_settings['keep_months'])
            keep_files['months'][keep_month_index] = file
            # print('File of month', file['month'], '(keeping month', keep_month_index, 'out of', keep_months,')')

        elif (parsed_file['year'] >= today_yday - storage_settings['keep_years'] and
              storage_settings['keep_years'] > 0) or storage_settings['keep_years'] < 0:
            if storage_settings['keep_years'] > 0:
                keep_year_index = parsed_file['year'] - (today.year - storage_settings['keep_years'])
            else:
                keep_year_index = parsed_file['year']
            keep_files['years'][keep_year_index] = file
            # print('File of year', file['year'], '(keeping year', keep_year_index, 'out of', keep_years,')')
        count += 1

    return keep_files


def files_to_keep_to_list(keep_files):
    # keep_files = {'last': [], 'weeks': {}, 'months': {}, 'years': {}}
    files_list = []
    files_list += keep_files['last']
    files_list += keep_files['weeks'].values()
    files_list += keep_files['months'].values()
    files_list += keep_files['years'].values()

    return files_list


def delete_excess_files(all_files, keep_list):
    for file in keep_list:
        while file in all_files:
            all_files.remove(file)
    return all_files


def unlink_files(files, is_test):
    for file in files:
        if not is_test:
            continue
        else:
            continue

if __name__ == '__main__':
    for settings in all_storage_settings:
        all_files_list = get_files(target_dir, settings['filetype'])
        files_to_keep = get_files_to_keep(all_files_list, settings)
        files_to_keep = files_to_keep_to_list(files_to_keep)
        print(delete_excess_files(all_files_list, files_to_keep))
        print(files_to_keep)
