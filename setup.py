import os
import sys
from setuptools import setup, find_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')

def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.ALDashboard',
      version='0.19.0',
      description=('Dashboard for some admin tasks'),
      long_description='# Backend Configuration Tool\r\n\r\nA single pane of glass that centralizes some tedious Docassemble admin configuration tasks\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702117-bdd7d300-d830-11eb-8c0e-8e204d912ff8.png)\r\n\r\n1. Install the Document Assembly Line packages (support files for [Court Forms Online](https://courtformsonline.org))\r\n1. Searchable user management - reset passwords and change privileges.\r\n1. Installing or updating several packages at once.\r\n1. Listing and viewing the contents of an (unencrypted) interview to facilitate debugging errors on production servers.\r\n1. View analytics/stats captured with store_variable_snapshot.\r\n1. List the files inside a particular package installed on the server.\r\n1. Gather files from a user who left the organization/unknown username and password.\r\n1. Review screen generator\r\n1. validate DOCX Jinja2 templates\r\n\r\nIdeas:\r\n1. Add a link to the dispatch directive for an existing file in an existing package.\r\n1. Generating translation files [TBD].\r\n\r\nTo use, you must create a docassemble API key and add it to your\r\nconfiguration, like this:\r\n\r\n`install packages api key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`\r\n\r\n## Some screenshots\r\n\r\n### Main page\r\n![image](https://user-images.githubusercontent.com/7645641/123702117-bdd7d300-d830-11eb-8c0e-8e204d912ff8.png)\r\n\r\n### Manage users\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702231-e069ec00-d830-11eb-94dc-5ec0abb86bc9.png)\r\n\r\n### Bulk install packages from GitHub\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702290-efe93500-d830-11eb-9fdf-a5935ff4078e.png)\r\n\r\n### Bulk update packages\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702362-068f8c00-d831-11eb-9ce4-df7a67ffcfeb.png)\r\n\r\n### View / search sessions by user and interview name\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702422-1d35e300-d831-11eb-84d5-5e7385deb901.png)\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702464-2cb52c00-d831-11eb-80fc-f2291e824eae.png)\r\n\r\n### View interview stats captured with `store_variables_snapshot()`\r\n\r\n![image](https://user-images.githubusercontent.com/7645641/123702623-5e2df780-d831-11eb-8937-6625df74ab22.png)\r\n\r\n',
      long_description_content_type='text/markdown',
      author='Quinten Steenhuis',
      author_email='qsteenhuis@gmail.com',
      license='The MIT License (MIT)',
      url='https://docassemble.org',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=['PyGithub>=1.55'],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/ALDashboard/', package='docassemble.ALDashboard'),
     )

