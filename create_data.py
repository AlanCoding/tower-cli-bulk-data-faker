import tower_cli
import sys
from faker import Factory
import random
from copy import copy
import time
import yaml

fake = Factory.create()
debug = False

res_list_reference = [
    'organization', 'team', 'project', 'user', 'inventory', 'host',
    'job_template'
]

# if desired, you can specify only a certain subset to run here
res_list = res_list_reference

# Not developed yet:
#  group
#  credential
#  job

# Create this many of each resource
Nres = {
    'organization': 45,
    'team': 135,
    'project': 33,
    'user': 368,
    'inventory': 87,
    'host': 247,
    'job_template': 3216
}

res_fields = {
    'organization': ['name', 'description'],
    'team': ['name', 'description', 'organization'],
    'project': ['name', 'description', 'organization'],
    'user': ['username', 'password', 'email', 'first_name', 'last_name'],
    'inventory': ['name', 'description', 'organization'],
    'host': ['name', 'inventory'],
    'job_template': ['name', 'description', 'inventory', 'project']
}
res_extras = {
    'project': {
        'scm_type': 'git',
        'scm_url': 'https://github.com/AlanCoding/permission-testing-playbooks.git',
        'monitor': False
    },
    'job_template': {
        'credential': 5,
        'playbook': 'helloworld.yml'
    }
}
res_assoc = {
    'user': {
        'organization': 'associate',
        'team': 'associate'
    },
    'project': {
        'organization': 'associate_project'
    }
}
# Assign each user 7 organizations, etc.
Nassoc = {
    'user': {
        'organization': 2,
        'team': 2
    },
    'project': {
        'organization': 3
    }
}

def fake_kwargs(n):
    kwargs = {}
    prefix = '_' + str(n) + '_'
    kwargs['username'] = fake.user_name()
    kwargs['name'] = fake.company()  # .replace(' ', '-')
    for key in kwargs:
        kwargs[key] = prefix + kwargs[key]
    kwargs['password'] = fake.password()
    kwargs['first_name'] = fake.first_name()
    kwargs['last_name'] = fake.last_name()
    kwargs['email'] = fake.email()
    kwargs['description'] = fake.catch_phrase()  # text() is also good
    return kwargs

def create_resource_data(res):
    fields = copy(res_fields[res])
    ref_lists = {}
    for fd in copy(fields):
        if fd in res_list_reference:
            ref_mod = tower_cli.get_resource(fd)
            ref_lists[fd] = ref_mod.list(all_pages=True)['results']
            fields.remove(fd)
    if res in res_assoc:
        for fd in res_assoc[res]:
            if fd not in ref_lists:
                ref_mod = tower_cli.get_resource(fd)
                ref_lists[fd] = ref_mod.list(all_pages=True)['results']
    res_mod = tower_cli.get_resource(res)
    for i in range(Nres[res]):
        std_kwargs = fake_kwargs(i)
        kwargs = {}
        for fd in fields:
            kwargs[fd] = std_kwargs[fd]
        if res in res_extras:
            kwargs.update(res_extras[res])
        for fd in ref_lists:
            kwargs[fd] = random.choice(ref_lists[fd])['id']
        print ' ' + res + ' ' + ' '.join([str(k) + '=' + str(kwargs[k]) for k in kwargs])
        if not debug:
            r = res_mod.create(**kwargs)
            print '   created, pk= ' + str(r['id'])
        else:
            r = random.choice(res_mod.list()['results'])
        if res in res_assoc:
            for target in res_assoc[res]:
                ref_mod = tower_cli.get_resource(target)
                targets_list = ref_lists[target]
                assoc_method = getattr(ref_mod, res_assoc[res][target])
                for j in range(Nassoc[res][target]):
                    target_pk = random.choice(targets_list)['id']
                    ref_mod_kwargs = {
                        res: r['id'],
                        target: target_pk
                    }
                    print '   ' + target + ' ' + res_assoc[res][target] + ' ' + ' '.join([str(k) + '=' + str(ref_mod_kwargs[k]) for k in ref_mod_kwargs])
                    if not debug:
                        assoc_method(**ref_mod_kwargs)

def quick_demo():
    for res in res_list:
        Nres[res] = 3
        print ''
        print ' ----- ' + res + ' ----- '
        debug = True
        create_resource_data(res)

def get_count(res):
    res_mod = tower_cli.get_resource(res)
    r = res_mod.list()
    return r['count']


if __name__ == "__main__":
    start_time = time.time()
    if len(sys.argv) == 1:
        print '\n  Usage:'
        print 'python create_data.py <subset> <count>\n'
        print ' subset options:'
        for res in res_list_reference:
            print '   - ' + res
    elif sys.argv[1] == 'demo':
        quick_demo()
    elif sys.argv[1] == 'counts':
        print '\n  Running resource counts:'
        for res in res_list_reference:
            print '  ' + res + ': ' + str(get_count(res))
    elif len(sys.argv) > 1:
        if sys.argv[-1] == 'debug':
            debug = True
        if sys.argv[1] == 'all':
            for res in res_list:
                print '\n ----- ' + res + ' ----- '
                create_resource_data(res)
        elif sys.argv[1].endswith('.yml'):
            with open(sys.argv[1], 'r') as f:
                filetext = f.read()
            Nres = yaml.load(filetext)
            res_list = Nres.keys()
            for res in res_list:
                print '\n ----- ' + res + ' ----- '
                create_resource_data(res)
        else:
            res = sys.argv[1]
            if len(sys.argv) > 2 and sys.argv[2].isdigit():
                Nres[res] = int(sys.argv[2])
            create_resource_data(res)
    end_time = time.time()
    print ''
    print ' total time taken: ' + str(end_time - start_time) + ' seconds'
