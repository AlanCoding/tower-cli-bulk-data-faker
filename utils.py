import os
import yaml
import sys
import cStringIO

from tower_cli.commands.config import echo_setting

def get_tower_cli_config(key):
    stdout_save = sys.stdout
    stream = cStringIO.StringIO()
    sys.stdout = stream
    echo_setting(key)
    sys.stdout = stdout_save
    printed_str = stream.getvalue()
    return_str = printed_str.strip('\n')
    return_str = return_str[return_str.index(':')+1:]
    return return_str

def get_host_value():
    stdout_save = sys.stdout
    stream = cStringIO.StringIO()
    sys.stdout = stream
    echo_setting('host')
    sys.stdout = stdout_save
    variable = stream.getvalue()
    return variable[6:].strip('\n')

def tower_cli_creds():
    cred_dict = {}
    for key in ('username', 'password', 'host'):
        cred_dict[key] = get_tower_cli_config(key)
    return cred_dict

def id_based_dict(resp_json):
    return_dict = {}
    if 'count' not in resp_json:
        return {}
    try:
        for item in resp_json['results']:
            return_dict[int(item['id'])] = item
    except:
        pass
    return return_dict

def load_all_creds():
    creds_dir = 'creds/'
    filelist = os.listdir('creds/')
    cred_dict = {}
    for filename in filelist:
        if 'gitignore' in filename:
            continue
        with open(os.path.join(creds_dir, filename), 'r') as f:
            user_dict = yaml.load(f.read())
        cred_dict[user_dict['username']] = user_dict
    return cred_dict