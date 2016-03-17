import requests
import yaml
import re
import warnings
import sys

def parse_api_time(html, name):
    p = re.compile('\<b\>' + str(name) + ':\</b\>\s\<span\sclass=\"lit\"\>(?P<time>[0-9]+.[0-9]+s)\<\/span\>')
    m = p.match(html)
    return m.group('time')

def load_endpoint(suffix):
    if suffix.startswith('/api/v1/'):
        suffix = suffix.strip('/api/v1/')
    built_url = cred_dict['host'].strip('/') + '/api/v1/' + suffix #+ '/?format=json'
    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(
            built_url,
            params={'format': 'json'},
            auth=(cred_dict['username'], cred_dict['password']), 
            verify=False)
    return r

def load_json(suffix):
    r = load_endpoint(suffix)
    return yaml.load(r.text)

filename = 'creds.yml'

if len(sys.argv) > 1:
    filename = sys.argv[1]

with open(filename, 'r') as f:
    creds = f.read()

cred_dict = yaml.load(creds)

try:
    r = load_json('')
    fields = [v[8:].strip('/') for v in r.values()]
except:
    fields = [
        'organizations', 'teams', 'projects', 'users', 'credentials',
        'inventories', 'hosts', 'groups', 'job_templates'
    ]

col_width = 9
col_1 = 30
print ''
print 'Table of API response times:'
print '\njob_templates  '
print '\nendpoint       '.ljust(col_1) + 'time'.ljust(col_width) + 'query'.ljust(col_width) + 'queries'.ljust(col_width)
for res in fields:
    r = load_endpoint(res)
    if 'X-API-Time' in r.headers:
        api_time = r.headers['X-API-Time']
        qu_time = r.headers['X-API-Query-Time']
        qu_count = r.headers['X-API-Query-Count']
    else:
        try:
            api_time = parse_api_time(r.text, 'X-API-Time')
            qu_time = parse_api_time(r.text, 'X-API-Query-Time')
            qu_count = parse_api_time(r.text, 'X-API-Query-Count')
        except:
            api_time = None
            qu_time = None
            qu_count = None
    print res.ljust(col_1) + str(api_time).ljust(col_width) + str(qu_time).ljust(col_width) + str(qu_count).ljust(col_width)

print ''
