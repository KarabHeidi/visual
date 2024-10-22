from docassemble.base.util import log, space_to_underscore, bold, DAObject, DAList, DAFile, DAFileList, path_and_mimetype, user_info
from docassemble.webapp.files import SavedFile
from docassemble.webapp.backend import directory_for
import datetime
import zipfile
import os
import re
from typing import Any, Dict, List, Tuple, Union #, Set

__all__ = ['get_files','get_list_of_projects', 'create_user_playground_zip', 'create_package_zip']

#def get_playground_files(userid:int, project:str=None):

def get_files(user_id, section='playground', project='default'):
  area = SavedFile(user_id, fix=True, section=section)
  the_directory = directory_for(area, project)
  files = [os.path.join(the_directory,f) for f in os.listdir(the_directory) if os.path.isfile(os.path.join(the_directory, f))]
  return files

def get_list_of_projects(user_id):
    playground = SavedFile(user_id, fix=False, section='playground')
    return playground.list_of_dirs()

def project_name(name):
    return '' if name == 'default' else name

def create_user_playground_zip(user_id:int, name:str, project:str='default', fileobj:DAFile=None):
  folders_and_files = {}
  for section in (('playground','questions'), ('playgroundtemplate', 'templates'), ('playgroundstatic','static'), ('playgroundsources','sources'), ('playgroundmodules','modules')):
    folders_and_files[section[1]] = get_files(user_id, section[0], project)
  
  return create_package_zip(f"{name}-{project}",
    info = {
      "license": "MIT",
      "author_name": name,
      "readme": "readme",
      "description": "playground backup",
      "url": "https://docassemble.org",
      "version": "1.0",
      "dependencies": ""
    },
    author_info = {
      "author name and email": name
    },
    folders_and_files=folders_and_files,
    fileobj=fileobj)
  
def create_package_zip(pkgname: str, info: dict, author_info: dict, folders_and_files: dict, fileobj:DAFile=None)->DAFile:
  """
  Given a dictionary of lists, with the keys representing folders and the values
  representing a list of DAFiles, create a Python package with Docassemble conventions.
  info: (created by DAInterview.package_info()) 
    license
    author_name
    readme
    description
    url
    version
    dependencies
    // interview_files replaced with folders_and_files
    // template_files
    // module_files
    // static_files
  author_info:
    author name and email  
  folders_and_files:
    questions->list of absolute file paths on the local filesystem
    templates
    modules
    static
    sources

  Strucure of a docassemble package:
  + docassemble-PKGNAME/
      LICENSE
      MANIFEST.in
      README.md
      setup.cfg
      setup.py
      +-------docassemble
          __init__.py
          +------PKGNAME
              __init__.py
              SOME_MODULE.py
              +------data
                  +------questions
                      README.md
                  +------sources
                      README.md  
                  +------static
                      README.md  
                  +------templates
                      README.md
  """
  pkgname = space_to_underscore(pkgname)
  if fileobj:
    zip_download = fileobj
  else: 
    zip_download = DAFile()
  pkg_path_prefix = "docassemble-" + pkgname
  pkg_path_init_prefix = os.path.join(pkg_path_prefix, "docassemble")
  pkg_path_deep_prefix = os.path.join(pkg_path_init_prefix, pkgname)
  pkg_path_data_prefix = os.path.join(pkg_path_deep_prefix, "data")
  pkg_path_questions_prefix = os.path.join(pkg_path_data_prefix,"questions")
  pkg_path_sources_prefix = os.path.join(pkg_path_data_prefix,"sources")
  pkg_path_static_prefix = os.path.join(pkg_path_data_prefix,"static")
  pkg_path_templates_prefix = os.path.join(pkg_path_data_prefix,"templates")

  zip_download.initialize(filename="docassemble-" + pkgname + ".zip")
  zip_obj = zipfile.ZipFile(zip_download.path(),'w')

  dependencies = ",".join(['\'' + dep + '\'' for dep in info['dependencies']])

  initpy = """\
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    __path__ = __import__('pkgutil').extend_path(__path__, __name__)
"""
  licensetext = str(info['license'])
  if re.search(r'MIT License', licensetext):
    licensetext += '\n\nCopyright (c) ' + str(datetime.datetime.now().year) + ' ' + str(info.get('author_name', '')) + """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
  if info['readme'] and re.search(r'[A-Za-z]', info['readme']):
    readme = str(info['readme'])
  else:
    readme = '# docassemble.' + str(pkgname) + "\n\n" + info['description'] + "\n\n## Author\n\n" + author_info['author name and email'] + "\n\n"
  manifestin = """\
include README.md
"""
  setupcfg = """\
[metadata]
description-file = README.md
"""
  setuppy = """\
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
"""
  setuppy += "setup(name='docassemble." + str(pkgname) + "',\n" + """\
      version=""" + repr(info.get('version', '')) + """,
      description=(""" + repr(info.get('description', '')) + """),
      long_description=""" + repr(readme) + """,
      long_description_content_type='text/markdown',
      author=""" + repr(info.get('author_name', '')) + """,
      author_email=""" + repr(info.get('author_email', '')) + """,
      license=""" + repr(info.get('license', '')) + """,
      url=""" + repr(info['url'] if info['url'] else 'https://docassemble.org') + """,
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=[""" + dependencies + """],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/""" + str(pkgname) + """/', package='docassemble.""" + str(pkgname) + """'),
     )
"""
  templatereadme = """\
# Template directory
If you want to use templates for document assembly, put them in this directory.
"""
  staticreadme = """\
# Static file directory
If you want to make files available in the web app, put them in
this directory.
"""
  sourcesreadme = """\
# Sources directory
This directory is used to store word translation files,
machine learning training files, and other source files.
"""
  templatesreadme = """\
# Template directory
This directory is used to store templates.
"""
  # Write the standard files
  zip_obj.writestr(os.path.join(pkg_path_prefix,"LICENSE"), licensetext)
  zip_obj.writestr(os.path.join(pkg_path_prefix,"MANIFEST.in"), manifestin)
  zip_obj.writestr(os.path.join(pkg_path_prefix,"README.md"), readme)
  zip_obj.writestr(os.path.join(pkg_path_prefix,"setup.cfg"), setupcfg)
  zip_obj.writestr(os.path.join(pkg_path_prefix,"setup.py"), setuppy)
  zip_obj.writestr(os.path.join(pkg_path_init_prefix,"__init__.py"), initpy)
  zip_obj.writestr(os.path.join(pkg_path_deep_prefix,"__init__.py"), ("__version__ = " + repr(info.get('version', '')) + "\n") )
  zip_obj.writestr(os.path.join(pkg_path_questions_prefix,"README.md"), templatereadme )
  zip_obj.writestr(os.path.join(pkg_path_sources_prefix,"README.md"), sourcesreadme )
  zip_obj.writestr(os.path.join(pkg_path_static_prefix,"README.md"), staticreadme)
  zip_obj.writestr(os.path.join(pkg_path_templates_prefix,"README.md"), templatesreadme)
  
  # Modules
  for f in folders_and_files.get('modules',[]):
    try:
      zip_obj.write(f,os.path.join(pkg_path_deep_prefix, os.path.basename(f)))
    except:
      log('Unable to add file ' + repr(file))        
  # Templates
  for f in folders_and_files.get('templates',[]):
    try:
      zip_obj.write(f,os.path.join(pkg_path_templates_prefix, os.path.basename(f)))
    except:
      log('Unable to add file ' + repr(file))
  # sources
  for f in folders_and_files.get('sources',[]):
    try:
      zip_obj.write(f,os.path.join(pkg_path_sources_prefix, os.path.basename(f)))
    except:
      log('Unable to add file ' + repr(file))
  # static
  for f in folders_and_files.get('static',[]):
    try:
      zip_obj.write(f,os.path.join(pkg_path_static_prefix, os.path.basename(f)))
    except:
      log('Unable to add file ' + repr(file))
  # questions
  for f in folders_and_files.get('questions',[]):
    try:
      zip_obj.write(f,os.path.join(pkg_path_questions_prefix, os.path.basename(f)))
    except:
      log('Unable to add file ' + repr(file))
  
  zip_obj.close()
  zip_download.commit()
  return zip_download
