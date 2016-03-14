import requests
import yaml
import re
import warnings
import sys

def parse_api_time(html):
    p = re.compile('\<b\>X-API-Time:\</b\>\s\<span\sclass=\"lit\"\>(?P<time>[0-9]+.[0-9]+s)\<\/span\>')
    m = p.match(html)
    return m.group('time')

filename = 'creds.yml'

if len(sys.argv) > 1:
    filename = sys.argv[1]

with open(filename, 'r') as f:
    creds = f.read()

cred_dict = yaml.load(creds)

fields = [
    'organizations', 'teams', 'projects', 'users', 'credentials',
    'inventories', 'hosts', 'groups', 'job_templates'
]

print ''
print 'Table of API response times:'
for res in fields:
    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore", requests.packages.urllib3.exceptions.InsecureRequestWarning)
        built_url = cred_dict['host'].strip('/') + '/api/v1/' + res + '/?format=json'
        r = requests.get(
            built_url,
            auth=(cred_dict['username'], cred_dict['password']), 
            verify=False)
    if 'X-API-Time' in r.headers:
        time_str = r.headers['X-API-Time']
    else:
        time_str = parse_api_time(r.text)
    print res.ljust(15) + time_str

print ''
