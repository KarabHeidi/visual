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
      version='0.5',
      description=('Dashboard for some admin tasks'),
      long_description='# Backend Configuration Tool\r\n\r\nA single pane of glass that centralizes some tedious Docassemble admin configuration tasks:\r\n\r\nDone: \r\n\r\n1. Installing or updating several packages at once\r\n1. Listing and viewing the contents of an (unencrypted) interview to facilitate debugging errors on production servers\r\n1. View analytics/stats captured with store_variable_snapshot\r\n\r\n\r\nTODO:\r\n\r\n1. List the files inside a particular package installed on the server\r\n1. Add a link to the dispatch directive for an existing file in an existing package\r\n1. Generating translation files [TBD]\r\n1. Gather files from a user who left the organization/unknown username and password\r\n\r\nTo use, you must create a docassemble API key and add it to your\r\nconfiguration, like this:\r\n\r\n`install packages api key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`\r\n',
      long_description_content_type='text/markdown',
      author='Quinten Steenhuis',
      author_email='qsteenhuis@gmail.com',
      license='The MIT License (MIT)',
      url='https://docassemble.org',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=[],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/ALDashboard/', package='docassemble.ALDashboard'),
     )

