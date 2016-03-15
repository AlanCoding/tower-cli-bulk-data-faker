# Tower-cli Bulk Fake Data Creator

This is a populator for Ansible Tower, which creates a large amount of fake
data, and it relies on the libraries from tower-cli.

Tower-cli is a command-line interface for the Ansible Tower API, but it can
also be used as a python module, and that is the type of use here.

### Usage

### Configuration Data

This relies on tower-cli configuration already existing and working.

```bash
tower-cli config username my_user
tower-cli config password p4ssword
tower-cli host http://tower.example.com

# Make sure the connection is working
tower-cli user list
```

### Running

The `create_data.py` script takes a command line argument and then creates
a batch of fake data. Data creation proceeds in phases, which mirror
the dependences of resources in Ansible Tower. These go in order of the following:

Creation order:

 - Organizations
 - Teams
 - Projects
 - Users

These don't necessarily need to go in this order, and you could draw a
graph with arrows of what's needed for others. Each of these have 
best-available isolation.

You probably want to poke around a bit before you dump a lot of data.
See the commands that a full run would produce with:

```bash
python create_data.py demo
```

Create just a few of a resource by specifying the number, and/or avoid
actually creating them with the debug option.

```bash
python create_data.py organization 3 debug
```

To run the data creation program (the FULL program) defined by the counts
in the `Nres` dictionary...

```bash
python create_data.py all
```

Alternatively, define a file with the resources and counts (as yaml)
in it and give that as an argument.

```bash
python create_data.py run_data.yml
```

For example, your file might say to create 2 users and 1 project, and this
command will carry out the creation of those.

### Getting API Response Times

Store your credentials in a yaml file.

```bash
python time_test.py creds.yml
```

This will give the response times at from all the top level endpoints.
