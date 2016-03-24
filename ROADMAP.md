## Features to add

 - Indepodent creation of data
   - that is, creating enough to satisfy a total quota, instead of creating
     the number the user specifies
   - POV user definition can specify `associate with 50% of organizations`
 - Point-Of-View teams
   - this needs to link to a Point-Of-View user in order to stress RBAC correctly
 - Store statistics on resource creation
 - Smarter fake data creator, giving convincing names for
   - projects
   - hosts
   - credentials
   - teams
   - job templates
     - Scrape Galaxy for data?
 - Data moving crew
   - A command to download remote data and put into YAML file
   - A command to migrate local credentials to Tower
   - A command to migrate local Ansible host files to Tower 

## Packaging and Collaboration

 - Command line packaging
 - PiPy package
   - Probably as a separate package (too dangerous for tower-cli inclusion)
