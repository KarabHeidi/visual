# Backend Configuration Tool

A single pane of glass that centralizes some tedious Docassemble admin configuration tasks

![image](https://user-images.githubusercontent.com/7645641/123702117-bdd7d300-d830-11eb-8c0e-8e204d912ff8.png)

Done: 

1. Install the Document Assembly Line packages (support files for [Court Forms Online](https://courtformsonline.org))
1. Searchable user management - reset passwords and change privileges.
1. Installing or updating several packages at once.
1. Listing and viewing the contents of an (unencrypted) interview to facilitate debugging errors on production servers.
1. View analytics/stats captured with store_variable_snapshot.


TODO:

1. List the files inside a particular package installed on the server.
1. Add a link to the dispatch directive for an existing file in an existing package.
1. Generating translation files [TBD].
1. Gather files from a user who left the organization/unknown username and password.

To use, you must create a docassemble API key and add it to your
configuration, like this:

`install packages api key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Some screenshots

### Main page
![image](https://user-images.githubusercontent.com/7645641/123702117-bdd7d300-d830-11eb-8c0e-8e204d912ff8.png)

### Manage users

![image](https://user-images.githubusercontent.com/7645641/123702231-e069ec00-d830-11eb-94dc-5ec0abb86bc9.png)

### Bulk install packages from GitHub

![image](https://user-images.githubusercontent.com/7645641/123702290-efe93500-d830-11eb-9fdf-a5935ff4078e.png)

### Bulk update packages

![image](https://user-images.githubusercontent.com/7645641/123702362-068f8c00-d831-11eb-9ce4-df7a67ffcfeb.png)

### View / search sessions by user and interview name

![image](https://user-images.githubusercontent.com/7645641/123702422-1d35e300-d831-11eb-84d5-5e7385deb901.png)

![image](https://user-images.githubusercontent.com/7645641/123702464-2cb52c00-d831-11eb-80fc-f2291e824eae.png)

### View interview stats captured with `store_variables_snapshot()`

![image](https://user-images.githubusercontent.com/7645641/123702623-5e2df780-d831-11eb-8937-6625df74ab22.png)

