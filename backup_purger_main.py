from math import ceil
from pathlib import Path
from datetime import datetime, timedelta
import configparser
import os
import random
import string
import copy_mod
import logging
from logging.handlers import RotatingFileHandler


def get_files(target_settings):
    # Get both remote and local files
    local_files = get_files_to_dict(target_settings['dst_dir'],
                                    target_settings['filename_pattern'])

    if target_settings['src_dir'] != '':
        remote_files = get_files_to_dict(target_settings['src_dir'],
                                         target_settings['filename_pattern'])
        allfiles = remote_files
        for key, item in local_files.items():
            allfiles[key] = item
    else:
        allfiles = local_files

    out_files_list = []
    for key in sorted(allfiles, reverse=True):
        out_files_list.append(allfiles[key])

    backups_logger.debug(('Files read:', out_files_list))
    return out_files_list


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


def get_files_to_keep(all_files, storage_settings):
    today = settings['today']
    start_year = today.year - 1
    today_yday = get_yday(today, start_year)
    today_week = get_week(today, start_year)
    today_month = get_month(today, start_year)
    keep_files = {'last': {}, 'weeks': {}, 'months': {}, 'years': {}}
    count = 0

    for current_file in all_files:
        backups_logger.debug(('Processing file:', current_file))
        try:
            date = datetime.strptime(current_file.name[0:len(storage_settings['date_pattern_text'])],
                                     storage_settings['date_pattern'])
            parsed_file = {
                'date': date,
                'week': get_week(date, start_year),
                'month': get_month(date, start_year),
                'year': date.year,
                'path': current_file}
        except ValueError:
            backups_logger.critical(f'Failed reading date from "{current_file.name}", skipping')
            continue

        if count < storage_settings['keep_last'] or storage_settings['keep_last'] < 0:
            backups_logger.debug(str(count) + ' out of last ' + str(storage_settings['keep_last'])
                                 + ' that are always kept')
            keep_files['last'][count + 1] = current_file
            today_week = parsed_file['week']
            count += 1

        elif (parsed_file['week'] >= today_week - storage_settings['keep_weeks'] and
              storage_settings['keep_weeks'] > 0) or storage_settings['keep_weeks'] < 0:

            if storage_settings['keep_weeks'] < 0:
                keep_week_index = parsed_file['week']
            else:
                keep_week_index = parsed_file['week'] - (today_week - storage_settings['keep_weeks'])
            keep_files['weeks'][keep_week_index] = current_file
            backups_logger.debug('File of week ' + parsed_file['week'] +
                                 ' (keeping week ' + keep_week_index + ' out of ' +
                                 storage_settings['keep_weeks'] + ')')
            today_month = parsed_file['month']

        elif (parsed_file['month'] >= today_month - storage_settings['keep_months'] and
              storage_settings['keep_months'] > 0) or storage_settings['keep_months'] < 0:

            if storage_settings['keep_months'] < 0:
                keep_month_index = parsed_file['month']
            else:
                keep_month_index = parsed_file['month'] - (today_month - storage_settings['keep_months'])
            keep_files['months'][keep_month_index] = current_file
            backups_logger.debug('File of month ' + parsed_file['month'] +
                                 ' (keeping month ' + keep_month_index + ' out of ' +
                                 storage_settings['keep_months'] + ')')

        elif (parsed_file['year'] >= today_yday - storage_settings['keep_years'] and
              storage_settings['keep_years'] > 0) or storage_settings['keep_years'] < 0:
            if storage_settings['keep_years'] > 0:
                keep_year_index = parsed_file['year'] - (today.year - storage_settings['keep_years'])
            else:
                keep_year_index = parsed_file['year']
            keep_files['years'][keep_year_index] = current_file
            backups_logger.debug('File of year ' + parsed_file['year'] +
                                 ' (keeping year ' + keep_year_index + ' out of ' +
                                 storage_settings['keep_years'] + ')')

    return keep_files


def files_to_keep_to_list(keep_files):
    # keep_files = {'last': {}, 'weeks': {}, 'months': {}, 'years': {}}
    files_list = []
    # dump all files to keep to the list
    for item in keep_files:
        files_list += keep_files[item].values()
    # return list without duplicates
    backups_logger.debug('Converted files to keep to list\n')
    return list(dict.fromkeys(files_list))


def leave_only_removing_files(all_files, keep_list, target_settings):
    for file_to_keep in keep_list:
        while file_to_keep in all_files:
            all_files.remove(file_to_keep)

    if not target_settings['delete_remote_files']:
        temp_files_list = all_files.copy()
        for remote_file in temp_files_list:
            if remote_file.parents[0] == Path(target_settings['src_dir']):
                all_files.remove(remote_file)
    backups_logger.debug('List processed. Left only files to remove\n')
    return all_files


def unlink_files(files, is_test):
    backups_logger.info('Deleting excess files \n')
    for file_to_delete in files:
        backups_logger.info('Deleting file' + str(file_to_delete))
        if not is_test:
            file_to_delete.unlink()


def get_files_to_dict(target_dir, filename_pattern='*'):
    path = Path(target_dir)
    files = {file.name: file for file in path.glob(filename_pattern) if file.is_file()}

    return files


def read_config(config_file):
    settings_structure = {'targets': []}

    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        for section in config:
            if section == 'DEFAULT':
                continue
            elif section == 'global':
                settings_structure['dry_run'] = config['global'].getboolean('dry_run')
                if config['global']['logging_level'].lower() == 'debug':
                    backups_logger.setLevel(logging.DEBUG)
                else:
                    backups_logger.setLevel(logging.INFO)
            elif config[section].getboolean('active'):
                target_params = {}

                for param in config[section]:
                    if param in ['keep_last', 'keep_weeks', 'keep_months', 'keep_years']:
                        target_params[param] = int(config[section][param])
                    elif param in ['delete_remote_files', 'delete_copied_files']:
                        target_params[param] = config[section].getboolean(param)
                    elif param == 'active':
                        continue
                    elif param == 'filename_pattern':
                        target_params[param] = config[section][param] + config[section]['filetype']
                    else:
                        target_params[param] = config[section][param]

                settings_structure['targets'].append(target_params)

            else:
                backups_logger.info('Skipping inactive section ' + section)
    except:
        backups_logger.error('Error reading config!')
        settings_structure['dry_run'] = True

    backups_logger.debug(['Config read!', settings_structure])
    return settings_structure


def generate_test_files(date_end, location):
    today = datetime.now()
    list_hours = []
    for i in range(24):
        list_hours.append(str(i).zfill(2))
    list_min_sec = []
    for i in range(60):
        list_min_sec.append(str(i).zfill(2))

    while today > date_end:
        filename = f"ut_2019_prod_backup_%s_%s_%s_%s%s%s_%s.txt" % (today.year,
                                                                    str(today.month).zfill(2),
                                                                    str(today.day).zfill(2),
                                                                    ''.join(random.choices(list_hours, k=1)),
                                                                    ''.join(random.choices(list_min_sec, k=1)),
                                                                    ''.join(random.choices(list_min_sec, k=1)),
                                                                    ''.join(random.choices(string.digits, k=6)))
        today += timedelta(-1)
        path = Path(os.path.join(location, filename))
        with open(path, 'wb') as f_out:
            f_out.write(os.urandom(50982))


def print_files_to_keep(files_dict):
    sections = ['last', 'weeks', 'months', 'years']
    backups_logger.info('\n')
    for section in sections:

        backups_logger.info(section)
        for file in files_dict[section]:
            backups_logger.info(str(file).zfill(2) + ' ' + str(files_dict[section][file]))
        backups_logger.info('\n')


def get_remote_files_to_copy(files, target_settings):
    remote_files = []
    for file in files:
        if file.parents[0] == Path(target_settings['src_dir']):
            remote_files.append(file)
            backups_logger.debug(('Remote file marked to copy', file))
    return remote_files


def copy_remote_files(files_list, target_settings, is_test):
    dst_dir = target_settings['dst_dir']
    backups_logger.info('\n')
    for file_to_copy in files_list:
        dst_file = Path(os.path.join(dst_dir, file_to_copy.name))
        backups_logger.info('Copying remote file')

        if not is_test:
            copy_mod.cp_progress(file_to_copy, dst_file)
            backups_logger.info('Copy done')
            backups_logger.info('\n')
            backups_logger.info('Calculating hashes')
            local_hash = copy_mod.get_file_hash_sha256(dst_file)
            remote_hash = copy_mod.get_file_hash_sha256(file_to_copy)
            if local_hash == remote_hash:
                backups_logger.info('Hash matches')
                if target_settings['delete_copied_files']:
                    file_to_copy.unlink()
            else:
                backups_logger.error('Copy failed, deleting corrupt local file')
                try:
                    dst_file.unlink()
                except:
                    backups_logger.critical('Error copying and unlinking ')
            backups_logger.info('\n')


if __name__ == '__main__':
    # Generate test files from now to specified date. Store them in specified location
    # generate_test_files(datetime.strptime('2021-10-10', '%Y-%m-%d'), 'C:\\Users\\krabs\\Desktop\\bak')

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    backups_logger = logging.getLogger("backups_main_log")
    if not os.path.exists('./purger_logs'):
        os.makedirs('./purger_logs')
    log_handler = RotatingFileHandler(os.path.join('./purger_logs', 'backup_purger.log'),
                                      maxBytes=1024*1024*40,
                                      backupCount=20)
    log_handler.setFormatter(
        logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S'))
    backups_logger.addHandler(log_handler)
    backups_logger.setLevel(logging.INFO)

    backups_logger.info("Started at " + datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))

    settings = read_config('bak_config.ini')
    settings['today'] = datetime.now()

    for current_target_settings in settings['targets']:
        # collect all files from folder
        all_files_list = get_files(current_target_settings)
        # select files to keep and return readable structure
        files_to_keep = get_files_to_keep(all_files_list, current_target_settings)
        # show readable
        print_files_to_keep(files_to_keep)
        # flatten structure to list
        files_to_keep = files_to_keep_to_list(files_to_keep)
        # select files which we don't need to store anymore
        files_to_delete = leave_only_removing_files(all_files_list, files_to_keep, current_target_settings)
        remote_files_to_copy = get_remote_files_to_copy(files_to_keep, current_target_settings)
        copy_remote_files(remote_files_to_copy, current_target_settings, settings['dry_run'])
        # delete these files
        unlink_files(files_to_delete, settings['dry_run'])
    backups_logger.info("Finished at " + datetime.now().strftime("%Y/%m/%d, %H:%M:%S"))
