# ALDashboard: a docassemble Admin and Configuration Tool

[![PyPI version](https://badge.fury.io/py/docassemble.ALDashboard.svg)](https://badge.fury.io/py/docassemble.ALDashboard)

A single tool and interview to centralizes some tedious Docassemble admin configuration tasks

![A screenshot of the ALDashboard menu with choices: "Admin only - manage users", "Admin only - stats", "Install assembly line", "Verify API Keys", "Install packages", "update packages", "Package scanner", "View Answer files", "generate review screen draft", "validate docx template", "validation translation files", "prepare translation files", "validate an attachment fields block", "PDF tools", and "Compile Bootstrap theme"](https://github.com/SuffolkLITLab/docassemble-ALDashboard/assets/6252212/29539eec-3891-476b-b248-dd3db986d899)

1. Install the Document Assembly Line packages (support files for [Court Forms Online](https://courtformsonline.org))
1. Searchable user management - reset passwords and change privileges.
1. Installing or updating several packages at once.
1. Listing and viewing the contents of an (unencrypted) interview to facilitate debugging errors on production servers.
1. View analytics/stats captured with `store_variable_snapshot`.
1. List the files inside a particular package installed on the server.
1. Gather files from a user who left the organization/unknown username and password.
1. Review screen generator
1. validate DOCX Jinja2 templates
1. Generating a [custom bootstrap theme](https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/customization/overview#creating-a-custom-theme-from-source-instead-of-with-a-theme-generator) for your interviews.

Ideas:
1. Add a link to the dispatch directive for an existing file in an existing package.
1. Generating translation files [TBD].

To use, you must create a docassemble API key and add it to your
configuration, like this:

`install packages api key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Some screenshots

### Main page
![A screenshot of the ALDashboard menu with choices: "Admin only - manage users", "Admin only - stats", "Install assembly line", "Verify API Keys", "Install packages", "update packages", "Package scanner", "View Answer files", "generate review screen draft", "validate docx template", "validation translation files", "prepare translation files", "validate an attachment fields block", "PDF tools", and "Compile Bootstrap theme"](https://github.com/SuffolkLITLab/docassemble-ALDashboard/assets/6252212/29539eec-3891-476b-b248-dd3db986d899)

### Manage users

![A screenshot that says "Manage users" with the fields User, What do you want want to do? Reset password, Change user permissions, New Password, Verify new Password](https://user-images.githubusercontent.com/7645641/123702231-e069ec00-d830-11eb-94dc-5ec0abb86bc9.png)

### Bulk install packages from GitHub

![A screenshot that says "What packages do you want to install? Github URL, YAML filename, Shor name or alias (no spaces)"](https://user-images.githubusercontent.com/7645641/123702290-efe93500-d830-11eb-9fdf-a5935ff4078e.png)

### Bulk update packages

![A screenshot that says "What packages do you want to update? docassemble.209aPlaintiffMotionToModify, docassemble.ALAffidavitOfIndigency" and more](https://user-images.githubusercontent.com/7645641/123702362-068f8c00-d831-11eb-9ce4-df7a67ffcfeb.png)

### View / search sessions by user and interview name

![A screenshot that says "What interview do you want to view sessions for? File name, User (leave blank to view all sessions)"](https://user-images.githubusercontent.com/7645641/123702422-1d35e300-d831-11eb-84d5-5e7385deb901.png)

![A screenshot that says "Recently generated sessions for docassemble.MA209AProtectiveOrder:data/questions/209a_package.yml" with 5 sessions below](https://user-images.githubusercontent.com/7645641/123702464-2cb52c00-d831-11eb-80fc-f2291e824eae.png)

### View interview stats captured with `store_variables_snapshot()`

![A screenshot that says "Stats for Eviction Moratorium: 9 Total submissions: 9 Group by: zip | state | modtime, Excel Download" followed by a map](https://user-images.githubusercontent.com/7645641/123702623-5e2df780-d831-11eb-8937-6625df74ab22.png)

### Generate a bootstrap theme

![A screenshot that says "Your file is compiled! You can view and copy your file, or download it directly by right clicking the link to save it as a CSS file". Below are examples of Bootstrap components like buttons and nav bars.](https://github.com/SuffolkLITLab/docassemble-ALDashboard/assets/6252212/079e428d-4cae-4f75-8b1b-227c28f32a44)
