import tower_cli
import sys
from faker import Factory
import random
from copy import copy
import time
import yaml
import os
from utils import load_all_creds, get_host_value, id_based_dict

fake = Factory.create()
debug = False

res_list_reference = [
    'organization', 'team', 'project', 'user', 'inventory', 'host',
    'credential', 'job_template'
]

# if desired, you can specify only a certain subset to run here
res_list = res_list_reference

# Not developed yet:
#  group
#  job
#  notifications

# Global variable for number to create
Nres = {}

res_fields = {
    'organization': ['name', 'description'],
    'team': ['name', 'description', 'organization'],
    # 'project': ['name', 'description', 'organization'],
    'project': ['name', 'description'],
    'user': ['username', 'password', 'email', 'first_name', 'last_name'],
    'inventory': ['name', 'description', 'organization'],
    'host': ['name', 'inventory'],
    'credential': ['name', 'description', 'username', 'password', 'user', ],
    'job_template': ['name', 'credential', 'description', 'inventory', 'project']
}
res_extras = {
    'project': {
        'scm_type': 'git',
        'scm_url': 'https://github.com/AlanCoding/permission-testing-playbooks.git',
        'monitor': False
    },
    'job_template': {
        'playbook': 'helloworld.yml'
    },
    'credential': {
        'kind': 'ssh'
    }
}
res_assoc = {
    'user': {
        'organization': {
            'associate': 2,
            'associate_admin': 0.5
        },
        'team': {
            'associate': 2
        }
    },
    'project': {
        'organization': {
            'associate_project': 3
        }
    }
}

def fake_kwargs(n=0):
    kwargs = {}
    prefix = '_' + str(n) + '_'
    kwargs['username'] = fake.user_name()
    kwargs['name'] = fake.company()  # .replace(' ', '-')
    # Attach an in integer on the names in sequence
    # for key in kwargs:
    #     kwargs[key] = prefix + kwargs[key]
    kwargs['password'] = fake.password()
    kwargs['first_name'] = fake.first_name()
    kwargs['last_name'] = fake.last_name()
    kwargs['email'] = fake.email()
    kwargs['description'] = fake.catch_phrase()  # text() is also good
    return kwargs

def create_resource_data(res):
    fields = copy(res_fields[res])
    # Prefetch lists with relationships to the resource
    pk_fields = []
    ref_lists = {}
    for fd in copy(fields):
        if fd in res_list_reference:
            ref_mod = tower_cli.get_resource(fd)
            list_kwargs = {'all_pages': True}
            if fd == 'credential':
                list_kwargs['kind'] = 'ssh'
            ref_lists[fd] = ref_mod.list(**list_kwargs)['results']
            fields.remove(fd)
            pk_fields.append(fd)
    if res in res_assoc:
        for fd in res_assoc[res]:
            if fd not in ref_lists:
                ref_mod = tower_cli.get_resource(fd)
                ref_lists[fd] = ref_mod.list(all_pages=True)['results']
    # Command to create the resource
    res_mod = tower_cli.get_resource(res)
    start_time = time.time()
    for i in range(Nres[res]):
        std_kwargs = fake_kwargs(i)
        kwargs = {}
        for fd in fields:
            kwargs[fd] = std_kwargs[fd]
        if res in res_extras:
            kwargs.update(res_extras[res])
        for fd in pk_fields:
            if len(ref_lists[fd]) == 0:
                print ('ERROR: one of the specified reference fields has no\n'
                       'existing records to associate with.')
            kwargs[fd] = random.choice(ref_lists[fd])['id']
        
        print ' ' + res + ' ' + ' '.join([str(k) + '=' + str(kwargs[k]) for k in kwargs])
        if not debug:
            r = res_mod.create(**kwargs)
            print '   created, pk= ' + str(r['id'])
        else:
            r_list = res_mod.list()['results']
            if len(r_list) == 0:
                r = {'id': 1}
            else:
                r = random.choice(r_list)
        # Post-creation associations
        if res in res_assoc:
            for target in res_assoc[res]:
                ref_mod = tower_cli.get_resource(target)
                targets_list = ref_lists[target]
                for method_name in res_assoc[res][target]:
                    assoc_method = getattr(ref_mod, method_name)
                    N = res_assoc[res][target][method_name]
                    if isinstance(N, float):
                        remainder = N - int(N)
                        N = int(N) + 1 if remainder > random.random() else int(N)
                    for j in range(N):
                        target_pk = random.choice(targets_list)['id']
                        ref_mod_kwargs = {res: r['id'], target: target_pk}
                        print ('   ' + target + ' ' + method_name + ' ' + 
                               ' '.join([str(k) + '=' + str(ref_mod_kwargs[k])
                               for k in ref_mod_kwargs]))
                        if not debug:
                            assoc_method(**ref_mod_kwargs)
    end_time = time.time()
    print '\n time taken for ' + str(res) + ' creation per item: ' + str((end_time - start_time)/Nres[res])

def create_pov_users(filename):
    with open(filename, 'r') as f:
        pov_data = yaml.load(f.read())
    cred_data = load_all_creds()
    towerhost = get_host_value()
    user_res = tower_cli.get_resource('user')
    print 'POV users:'
    for username in pov_data:
        print ' - ' + str(username)

    for username in pov_data:
        print '\n Managing Point-Of-View user ' + str(username)
        fake_data = fake_kwargs()
        user_data = dict((k, fake_data[k]) for k in res_fields['user'] if k in fake_data)
        user_data['username'] = username

        if username in cred_data:
            user_data['password'] = cred_data[username]['password']

        if username not in cred_data or str(cred_data[username]['host']) != str(towerhost):
            # Create new account data for user
            new_filepath = 'creds/' + username + '_creds.yml'
            if os.path.isfile(new_filepath) and username not in cred_data:
                print 'ERROR: credential for ' + username + ' does not exist'
                print '  but a filename for that user does'
                raise Exception()
            with open(new_filepath, 'w') as f:
                f.write(yaml.dump({
                    'host': towerhost, 'username': str(username),
                    'password': str(user_data['password'])
                }, default_flow_style=False))

        # Check existing user record, and leave existing fields alone
        try:
            user_obj = user_res.get(username=username)
            for fd in copy(user_data):
                if fd in ('username', 'password'):
                    continue
                if user_obj[fd] not in ('', None):
                    user_data.pop(fd)
        except:
            pass
        if len(user_data) > 2:
            # Create the user in Tower, or write over existing user
            print ('  user modify ' + ' '.join([str(k) + '=' + str(user_data[k])
                for k in user_data]))
            user_obj = user_res.write(force_on_exists=True,
                create_on_missing=True, fail_on_found=False, **user_data)

        if pov_data[username] is None:
            continue
        for target in pov_data[username]:
            res_mod = tower_cli.get_resource(target)
            targets_list = id_based_dict(res_mod.list(all_pages=True))
            if len(targets_list) == 0:
                print 'PROBLEM: no ' + str(target) + ' resources to add to'
                print '  the user. This will probably cause a problem.'
                continue
            if isinstance(pov_data[username][target], dict):
                for method_name in pov_data[username][target]:
                    assoc_method = getattr(res_mod, method_name)
                    N = pov_data[username][target][method_name]
                    # Subtract the number already owned by the user
                    if 'admin' in method_name:
                        try:
                            N_existing = res_mod.list(
                                query=[('admins__in', user_obj['id'])])['count']
                        except:
                            N_existing = res_mod.list(
                                query=[('admin_role__members__in', user_obj['id'])])['count']
                    else:
                        try:
                            N_existing = res_mod.list(
                                query=[('users__in', user_obj['id'])])['count']
                        except:
                            N_existing = res_mod.list(
                                query=[('member_role__members__in', user_obj['id'])])['count']
                    N = N - N_existing
                    if N < 0:
                        N = 0
                    print ('  found ' + str(N_existing) + ' of ' + target + 
                           ' with ' + method_name + ' associations.' +
                           ' Creating ' + str(N) + ' more.')
                    for j in range(N):
                        target_pk = random.choice(targets_list.keys())
                        ref_mod_kwargs = {'user': user_obj['id'], target: target_pk}
                        print ('   ' + target + ' ' + method_name + ' ' + 
                               ' '.join([str(k) + '=' + str(ref_mod_kwargs[k])
                               for k in ref_mod_kwargs]))
                        if not debug:
                            assoc_method(**ref_mod_kwargs)
            else:
                method_name = 'modify'
                assoc_method = getattr(res_mod, method_name)
                N = pov_data[username][target]
                # Subtract the number already associated with the user
                N_existing = res_mod.list(
                    query=[('user__in', user_obj['id'])])['count']
                N = N - N_existing
                if N < 0:
                    N = 0
                print ('  found ' + str(N_existing) + ' of ' + target + 
                       ' with ' + method_name + ' associations.' +
                       ' Creating ' + str(N) + ' more.')
                for j in range(N):
                    target_pk = random.choice(targets_list.keys())
                    ref_mod_kwargs = {'user': user_obj['id']}
                    # Special case where we have to de-associate team
                    if target == 'credential':
                        ref_mod_kwargs['team'] = None
                    print ('   ' + target + ' ' + method_name + ' ' + str(target_pk) + ' ' +
                           ' '.join([str(k) + '=' + str(ref_mod_kwargs[k])
                           for k in ref_mod_kwargs]))
                    if not debug:
                        assoc_method(target_pk, **ref_mod_kwargs)

def destroy(res):
    res_mod = tower_cli.get_resource(res)
    targets_list = id_based_dict(res_mod.list(all_pages=True))
    if res == 'user':
        cred_data = load_all_creds()
        cred_ids = []
        for username in cred_data.keys():
            try:
                user_obj = res_mod.get(username=username)
                cred_ids.append(user_obj['id'])
            except:
                pass
        print '  excluding special users: ' + ' '.join(cred_data.keys())
    for pk in targets_list.keys():
        # Don't delete the users used to log in with in the first place
        if res == 'user' and pk in cred_ids:
            continue
        print ' ' + res + ' delete ' + str(pk)
        if not debug:
            res_mod.delete(pk)

def quick_demo():
    debug = True
    for res in res_list:
        Nres[res] = 3
        print ''
        print ' ----- ' + res + ' ----- '
        create_resource_data(res)

def get_count(res):
    res_mod = tower_cli.get_resource(res)
    r = res_mod.list()
    return r['count']

def finish(start_time):
    end_time = time.time()
    print ''
    print ' total time taken: ' + str(end_time - start_time) + ' seconds'
    sys.exit(0)


if __name__ == "__main__":
    start_time = time.time()
    args = copy(sys.argv)

    # Special information commands
    if len(sys.argv) <= 1:
        print '\n  Usage patterns:'
        print 'python create_data.py <resource> <count>\n'
        print 'python create_data.py <command> <flags>\n'
        print ' resource options:'
        for res in res_list_reference:
            print '   - ' + res
        print '\n command options'
        print '   - all:    create all data in the definition file'
        print '   - demo:   show what data would be created by all command'
        print '   - counts: echo number of things in Tower already'
        sys.exit(0)
    if sys.argv[1] == 'demo':
        quick_demo()
        sys.exit(0)
    if sys.argv[1] == 'counts':
        print '\n  Running resource counts:'
        for res in res_list_reference:
            print '  ' + res + ': ' + str(get_count(res))
        finish(start_time)

    # Process options
    if args[-1].endswith('debug'):
        debug = True
        args.remove(args[-1])

    # Normal create commands
    if args[1].endswith('.yml') or args[1] == 'all':
        if args[1] == 'all':
            filename = 'run_data.yml'
        else:
            filename = args[1]
        with open(filename, 'r') as f:
            filetext = f.read()
        Nres = yaml.load(filetext)
        res_list = Nres.keys()
        for res in res_list_reference:
            if res in res_list:
                print '\n ----- ' + res + ' ----- '
                create_resource_data(res)
    elif args[1] in res_list_reference:
        res = args[1]
        if len(args) > 2 and args[2].isdigit():
            Nres[res] = int(args[2])
        create_resource_data(res)
    elif args[1] == 'pov':
        pov_filename = 'pov_users.yml'
        if len(args) > 2 and args[2].endswith('.yml'):
            pov_filename = args[2]
        create_pov_users(pov_filename)
    elif args[1] == 'destroy':
        if args[2] == 'all':
            for res in res_list_reference:
                print '\nDestroying all ' + res + ' resources.'
                destroy(res)
        else:
            destroy(args[2])
    else:
        print 'Command not understood'

    finish(start_time)
