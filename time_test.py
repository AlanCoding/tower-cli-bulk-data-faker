import requests
import yaml
import re
import warnings
# from copy import copy
import sys
import random
import time
import json
from utils import list_ids
import tower_cli

# Global parameters
sample_detail_views = False
detail_sample_size = 5
sample_sublist_views = False
# Formatting of output
col_width = 9
col_1 = 30

def parse_api_time(html, name):
    p = re.compile('\<b\>' + str(name) + ':\</b\>\s\<span\sclass=\"lit\"\>(?P<time>[0-9]+.[0-9]+s)\<\/span\>')
    m = p.match(html)
    return m.group('time')

def load_endpoint(suffix, creds):
    if suffix.startswith('/api/v1/'):
        suffix = suffix.strip('/api/v1/')
    built_url = creds['host'].strip('/') + '/api/v1/' + suffix #+ '/?format=json'
    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(
            built_url,
            params={'format': 'json'},
            auth=(creds['username'], creds['password']), 
            verify=False)
    return r

def load_json(suffix, creds):
    r = load_endpoint(suffix, creds)
    return json.loads(r.text)

def read_creds(filename):
    with open(filename, 'r') as f:
        flat_creds = f.read()
    return yaml.load(flat_creds)
    

def find_field_list(creds):
    try:
        r = load_json('', creds)
        fields = [v[8:].strip('/') for v in r.values()]
    except:
        print 'NOTICE: failed to load JSON response from server'
        fields = [
            'organizations', 'teams', 'projects', 'users', 'credentials',
            'inventories', 'hosts', 'groups', 'job_templates'
        ]
    return fields

def get_endpoint_data(res, creds):
    r = load_endpoint(res, creds)
    # print ' response: ' + r.text
    if 'X-API-Time' in r.headers:
        api_time = r.headers.get('X-API-Time', None)
        qu_time = r.headers.get('X-API-Query-Time', None)
        qu_count = r.headers.get('X-API-Query-Count', None)
    else:
        try:
            # Fallback option #1, maybe got API html?
            api_time = parse_api_time(r.text, 'X-API-Time')
            qu_time = parse_api_time(r.text, 'X-API-Query-Time')
            qu_count = parse_api_time(r.text, 'X-API-Query-Count')
        except:
            # Fallback option #2, not getting data
            api_time = None
            qu_time = None
            qu_count = None
    return (r, api_time, qu_time, qu_count)


def tabulated_format(heading, *cells):
    return heading.ljust(col_1) + ''.join([str(cell).ljust(col_width) for cell in cells])


def run_timer(creds_file):
    creds = read_creds(creds_file)
    stored_lists = {}
    fields = find_field_list(creds)
    print ''
    print 'Table of API response times:'
    print ''
    print ' list view results'
    print '\njob_templates  '
    print tabulated_format('endpoint', 'time', 'query', 'queries')
    for res in fields:
        r, api_time, qu_time, qu_count = get_endpoint_data(res, creds)
        print tabulated_format(res, api_time, qu_time, qu_count)
        stored_lists[res] = list_ids(yaml.load(r.text))
    print ''


def load_all_creds():
    return {}


def pov_run(username):
    user_res = tower_cli.get_resource('user')
    user_data = user_res.get(username=username)
    run_timer()


def multiple_pov_run(pov_file):
    with open(pov_file, 'r') as f:
        pov_dict = yaml.load(f.read())
    for username in pov_dict:
        pov_run(username)


def is_this_file_yaml(filename):
    if filename.endswith('.yml') or filename.endswith('.yaml'):
        try:
            with open(filename, 'r') as f:
                yaml.load(f.read())
            return True
        except:
            return False
    else:
        return False

if __name__ == "__main__":
    start_time = time.time()
    args = sys.argv

    # Does user ask for stats on detial views?
    for i in range(len(args)):
        arg = args[i]
        if arg.endswith('-details'):
            sample_detail_views = True
            if i+1 < len(args) and args[i+1].isdigit():
                number = args[i+1]
                detail_sample_size = int(number)
                args.remove(number)
            args.remove(arg)
            break

    # Does the user ask for stats on subviews?
    for i in range(len(args)):
        arg = args[i]
        if arg.endswith('-subviews'):
            sample_sublist_views = True
            args.remove(arg)
            break

    # Does the user want this run for each user in the POV file?
    for i in range(len(args)):
        arg = args[i]
        if arg.endswith('pov'):
            if i+1 < len(args):
                multiple_pov_run('pov_users.yml')
            elif is_this_file_yaml(args[i+1]):
                multiple_pov_run(args[i+1])
            else:
                pov_run(args[i+1])
    if any([arg.endswith('pov') for arg in args]):
        pov_file = 'pov_users.yml'
        for arg in args:
            if is_this_file_yaml(arg):
                pov_file = arg
        # Run the analysis for the POV users
        pov_run(pov_file)

    # Is a credential file specifically specified?
    creds_file = 'creds.yml'
    if any([is_this_file_yaml(arg) for arg in args]):
        for arg in args:
            if is_this_file_yaml(arg):
                creds_file = arg

    # Run the analysis once
    run_timer(creds_file)

    end_time = time.time()
    print ''
    print ' total time taken: ' + str(end_time - start_time) + ' seconds'

