import requests
import yaml
import re
import warnings
# from copy import copy
import sys
import random
import time
import json
from utils import load_all_creds, id_based_dict
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

def dig_out_yaml(some_text):
    try:
        ret_dict = json.loads(some_text)
        assert isinstance(ret_dict, dict)
    except:
        html = some_text
        html = html.replace('&quot;', '"')
        p = re.compile('\<\/(span|div)\>(?P<yaml>\{(.|\n)*\})\<\/pre\>')
        m = p.match(html)
        # import pdb; pdb.set_trace()
        if m is None:
            print ' failed to correct get data\n first part of text\n'
            print some_text[:30] + '\n'
        yaml_text = m.group('yaml')
        ret_dict = yaml.load(yaml_text)
    return ret_dict

def load_endpoint(suffix, creds, soft_error=False):
    if suffix.startswith('/api/v1/'):
        # suffix = suffix.strip('/api/v1/')
        suffix = suffix[8:]
    built_url = creds['host'].strip('/') + '/api/v1/' + suffix.strip('/') + '/?format=json'
    if suffix == '':
        built_url = creds['host'].strip('/') + '/api/v1/?format=json'
    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(
            built_url,
            headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8'
            },
            auth=(creds['username'], creds['password']), 
            verify=False)
    if r.status_code != 200:
        if soft_error:
            return r.status_code
        print 'Encountered an error getting a response'
        print '  response: ' + str(r.text[:50])
        print '  status_code: ' + str(r.status_code)
        print '  url: ' + built_url
        raise Exception()
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
        fields = [v[8:].strip('/') for v in r.values() if 'authtoken' not in v and 'system_job' not in v]
    except:
        print 'NOTICE: failed to load JSON response from server'
        fields = [
            'organizations', 'teams', 'projects', 'users', 'credentials',
            'inventories', 'hosts', 'groups', 'job_templates'
        ]
    return fields

def get_endpoint_data(res, **kwargs):
    endpoint_start_time = time.time()
    r = load_endpoint(res, **kwargs)
    endpoint_end_time = time.time()
    manual_time = round(endpoint_end_time - endpoint_start_time, 3)
    if isinstance(r, int):
        return (r, 0, 0, 0, 0)
    def give_header_value(v, r):
        if v in r.headers:
            val = r.headers.get(v, None)
            if val:
                return val
        try:
            return parse_api_time(r.text, v)
        except:
            return None
    api_time = give_header_value('X-API-Time', r)
    qu_time = give_header_value('X-API-Query-Time', r)
    qu_count = give_header_value('X-API-Query-Count', r)

    return (r, api_time, qu_time, qu_count, manual_time)


def tabulated_format(heading, *cells):
    return heading.ljust(col_1) + ''.join([str(cell).ljust(col_width) for cell in cells])

def force_float(in_arg):
    try:
        val = float(in_arg)
    except:
        val = float(in_arg.strip('s'))
    return val


def run_timer(creds_file, sample_sublist_views=False, 
              sample_detail_views=False, detail_sample_size=5):
    error_dict = {}
    creds = read_creds(creds_file)
    stored_lists = {}
    fields = find_field_list(creds)
    print '\nTable of API response times:'
    print '\n top-level list view results'
    print tabulated_format('endpoint', 'time', 'query', 'queries', 'manual')
    for res in fields:
        r, api_time, qu_time, qu_count, man_time = get_endpoint_data(res, creds=creds, soft_error=True)
        if isinstance(r, int):
            print res.ljust(col_1) + 'error status_code: ' + str(r)
        else:
            print tabulated_format(res, api_time, qu_time, qu_count, man_time)
            r_json = dig_out_yaml(r.text)
            if 'count' in r_json:
                stored_lists[res] = id_based_dict(r_json)
    print ''

    if sample_detail_views:
        print '\n detail view statistics (averages)'
        print tabulated_format('endpoint', 'time', 'query', 'queries', 'manual')
        for res in fields:
            if res not in stored_lists:
                continue
            at_total = 0.0
            qt_total = 0.0
            qu_total = 0
            man_total = 0.0
            N = detail_sample_size
            res_ids = stored_lists[res]
            if len(res_ids) == 0:
                print res.ljust(col_1) + 'no_records'
                continue
            for i in range(N):
                res_id = random.choice(res_ids.keys())
                # endpoint = res + '/' + str(res_id)
                endpoint = res_ids[res_id]['url']
                r, api_time, qu_time, qu_count, man_time = get_endpoint_data(endpoint, creds=creds, soft_error=True)
                at_float = force_float(api_time)
                if qu_time is None:
                    qt_float = 0.0
                    qu_count = 0
                else:
                    qt_float = force_float(qu_time)
                at_total += at_float or 0
                qt_total += qt_float or 0
                man_total += man_time
                qu_total += int(qu_count)
            print tabulated_format(res, at_total/N, qt_total/N, qu_total*1.0/N, man_total*1.0/N)


    if sample_sublist_views:
        print '\n sublist view results'
        for res in fields:
            if res not in stored_lists:
                continue
            print '\nrelated field load times for ' + str(res)
            print '    ' + tabulated_format('endpoint', 'time', 'query', 'queries')
            res_dict = stored_lists[res]
            N = 1
            if len(res_dict) == 0:
                print '    ' + res.ljust(col_1) + 'no_records'
                continue
            for i in range(N):
                res_id = random.choice(res_dict.keys())
                item_dict = res_dict[res_id]
                related_dict = item_dict['related']
                for relationship in related_dict:
                    endpoint = related_dict[relationship]
                    if not isinstance(endpoint, basestring):
                        if len(endpoint) == 1:
                            endpoint = endpoint[0]
                        else:
                            print '    error: bad endpoint type: ' + str(endpoint)
                            continue
                    r, api_time, qu_time, qu_count, man_time = get_endpoint_data(endpoint, creds=creds, soft_error=True)
                    if isinstance(r, int):
                        print '    ' + relationship.ljust(col_1) + 'error: ' + str(r)
                    else:
                        print '    ' + tabulated_format(relationship, api_time, qu_time, qu_count, man_time)


def pov_run(sample_sublist_views, 
            sample_detail_views, detail_sample_size):
    # user_res = tower_cli.get_resource('user')
    # user_data = user_res.get(username=username)
    import os
    filelist = os.listdir('creds/')
    for filename in filelist:
        if 'gitignore' in filename:
            continue
        print '\n------running user batch----'
        print '  filename: ' + filename + '\n'
        run_timer('creds/' + filename, sample_sublist_views, 
                  sample_detail_views, detail_sample_size)


def multiple_pov_run(pov_file, sample_sublist_views, 
            sample_detail_views, detail_sample_size):
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

    # Does user ask for stats on detail views?
    for i in range(len(args)):
        arg = args[i]
        if arg.endswith('-details') or arg.endswith('-detail'):
            sample_detail_views = True
            if i+1 < len(args) and args[i+1].isdigit():
                number = args[i+1]
                detail_sample_size = int(number)
                args.remove(number)
            args.remove(arg)
            print '    printing detail view stats'
            break

    # Does the user ask for stats on subviews?
    for i in range(len(args)):
        arg = args[i]
        if arg.endswith('-subviews') or arg.endswith('-subview'):
            sample_sublist_views = True
            args.remove(arg)
            print '    printing subview stats'
            break

    # Does the user want this run for each user in the POV file?
    # for i in range(len(args)):
    #     arg = args[i]
    #     if arg.endswith('pov'):
    #         if i+1 <= len(args):
    #             multiple_pov_run('pov_users.yml')
    #         elif is_this_file_yaml(args[i+1]):
    #             multiple_pov_run(args[i+1])
    #         else:
    #             pov_run(args[i+1])
    if any([arg.endswith('pov') for arg in args]):
        # pov_file = 'pov_users.yml'
        # for arg in args:
        #     if is_this_file_yaml(arg):
        #         pov_file = arg
        # Run the analysis for the POV users
        pov_run(sample_sublist_views,
                  sample_detail_views, detail_sample_size)
    else:

        # Is a credential file specifically specified?
        creds_file = 'creds.yml'
        if any([arg.endswith('.yml') or arg.endswith('.yaml') for arg in args]):
            for arg in args:
                if arg.endswith('.yml') or arg.endswith('.yaml'):
                    creds_file = arg

        # Run the analysis once
        run_timer(creds_file, sample_sublist_views,
                  sample_detail_views, detail_sample_size)

    end_time = time.time()
    print ''
    print ' total time taken: ' + str(end_time - start_time) + ' seconds'

