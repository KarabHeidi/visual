from docassemble.webapp.users.models import UserModel
from docassemble.webapp.db_object import init_sqlalchemy
from github import Github  # PyGithub

# db is a SQLAlchemy Engine
from sqlalchemy.sql import text
from typing import List, Tuple, Dict, Optional
import docassemble.webapp.worker
from docassemble.webapp.server import (
    user_can_edit_package,
    get_master_branch,
    install_git_package,
    redirect,
    should_run_create,
    flash,
    url_for,
    restart_all,
    install_pip_package,
    get_package_info,
)
from docassemble.base.config import daconfig
from docassemble.webapp.backend import cloud
from docassemble.base.util import log, DAFile, DAObject, DAList, word
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import re

db = init_sqlalchemy()

__all__ = [
    "install_from_github_url",
    "reset",
    "speedy_get_users",
    "speedy_get_sessions",
    "get_users_and_name",
    "da_get_config",
    "da_get_config_as_file",
    "da_write_config",
    "ALPackageInstaller",
    "get_package_info",
    "install_from_pypi",
]


def install_from_github_url(url: str, branch: str = ""):
    giturl = url.strip().rstrip("/")
    if isinstance(branch, str):
        branch = branch.strip()
    if not branch:
        branch = get_master_branch(giturl)
    packagename = re.sub(r"/*$", "", giturl)
    packagename = re.sub(r"^git+", "", packagename)
    packagename = re.sub(r"#.*", "", packagename)
    packagename = re.sub(r"\.git$", "", packagename)
    packagename = re.sub(r".*/", "", packagename)
    packagename = re.sub(r"^docassemble-", "docassemble.", packagename)
    if user_can_edit_package(giturl=giturl) and user_can_edit_package(
        pkgname=packagename
    ):
        install_git_package(packagename, giturl, branch)
    else:
        flash(word("You do not have permission to install this package."), "error")
    return packagename


def install_from_pypi(packagename: str):
    return install_pip_package(packagename)


def reset(packagename=""):
    result = docassemble.webapp.worker.update_packages.apply_async(
        link=docassemble.webapp.worker.reset_server.s(
            run_create=should_run_create(packagename)
        )
    )
    return redirect(url_for("update_package_wait"))


def da_get_config_as_file():
    yaml = YAML()
    yaml.allow_duplicate_keys = True
    # try:
    with open(daconfig["config file"], "r", encoding="utf-8") as fp:
        content = fp.read()

    the_file = DAFile()
    the_file.initialize(filename="config.yml")
    the_file.write(content)
    return the_file


def da_get_config():
    yaml = YAML()
    yaml.allow_duplicate_keys = True
    # try:
    with open(daconfig["config file"], "r", encoding="utf-8") as fp:
        content = fp.read()
    data = yaml.load(content)
    return data
    # except:
    #  return None


def da_write_config(data: Dict):
    yaml = YAML()
    yaml.allow_duplicate_keys = True
    try:
        # ruamel.yaml has a big rant about why we shouldn't save the YAML output to a string,
        # but it's done upstream here so we will use the provided workaround
        # see https://yaml.readthedocs.io/en/latest/example.html?highlight=StringIO#output-of-dump-as-a-string
        stream = StringIO()
        yaml.dump(data, stream)
        yaml_data = stream.getvalue()
    except:
        log("Invalid configuration provided to da_write_config, skipping.")
        return None
    if cloud is not None:
        key = cloud.get_key("config.yml")
        key.set_contents_from_string(yaml_data)
    with open(daconfig["config file"], "w", encoding="utf-8") as fp:
        fp.write(yaml_data)
    restart_all()


def speedy_get_users() -> List[Dict[int, str]]:
    """
    Return a list of all users in the database. Possibly faster than get_user_list().
    """
    the_users = UserModel.query.with_entities(UserModel.id, UserModel.email).all()

    return [{user[0]: user[1]} for user in the_users]


def get_users_and_name() -> List[Tuple[int, str, str, str]]:
    users = UserModel.query.with_entities(
        UserModel.id, UserModel.email, UserModel.first_name, UserModel.last_name
    )

    return users


def speedy_get_sessions(user_id: Optional[int] = None, filename: Optional[str] = None) -> List[Tuple]:
    """
    Return a lsit of the most recent 500 sessions, optionally tied to a specific user ID.

    Each session is a tuple with named columns:
    filename,
    user_id,
    modtime,
    key
    """
    get_sessions_query = text(
        """
  SELECT  userdict.filename as filename
         ,num_keys
         ,userdictkeys.user_id as user_id
         ,modtime
         ,userdict.key as key
  FROM userdict 
  NATURAL JOIN 
  (
    SELECT  key
           ,MAX(modtime) AS modtime
           ,COUNT(key)   AS num_keys
    FROM userdict
    GROUP BY  key
  ) mostrecent
  LEFT JOIN userdictkeys
  ON userdictkeys.key = userdict.key
  WHERE (userdict.user_id = :user_id OR :user_id is null)
  AND
  (userdict.filename = :filename OR :filename is null)
  ORDER BY modtime desc 
  LIMIT 500;
  """
    )
    if not filename:
        filename = None  # Explicitly treat empty string as equivalent to None
    if not user_id:  # TODO: verify that 0 is not a valid value for user ID
        user_id = None

    with db.connect() as con:
        rs = con.execute(get_sessions_query, {"user_id":user_id, "filename":filename})
    sessions = []
    for session in rs:
        sessions.append(session)

    return sessions


class ALPackageInstaller(DAObject):
    """Methods and state for installing AssemblyLine."""

    def init(self, *pargs, **kwargs):
        super().init(*pargs, **kwargs)
        self.initializeAttribute("errors", ErrorList)

    def get_validated_github_username(self, access_token: str):
        """
        Given a valid GitHub `access_token`, returns the username associated with it.
        Otherwise, adds one or more errors to the installer.
        """
        self.errors.clear()  # Reset
        github = Github(access_token)
        github_user = github.get_user()
        try:
            # Ensure the token has the right permissions
            scopes = str(github_user.raw_headers["x-oauth-scopes"]).split(", ")
            if not "repo" in scopes and not "public_repo" in scopes:
                self.errors.appendObject(
                    template_name="github_permissions_error", scopes=scopes
                )
                return None
            else:
                return github_user.login
        except Exception as error:
            # GitHub doesn't recognize the token
            # github.GithubException.BadCredentialsException (401, 403) (specific exception not working)
            self.errors.appendObject(template_name="github_credentials_error")


class ErrorList(DAList):
    """Contains `ErrorLikeObject`s so they can be recognized by docassemble."""

    def init(self, *pargs, **kwargs):
        super().init(*pargs, **kwargs)
        self.object_type = ErrorLikeObject
        self.gathered = True


class ErrorLikeObject(DAObject):
    """
    An object with a `template_name` that identifieds the DALazyTemplate that will
    show its error. It can contain any other attributes so its template can access them
    as needed. DAObject doesn't seem to be enough to allow template definition.
    """

    def init(self, *pargs, **kwargs):
        super().init(*pargs, **kwargs)
        # `unknown_error` can be a default template for unexpected errors to use
        self.template_name = kwargs.get("template_name", "unknown_error")


#  select userdict.filename, num_keys, userdictkeys.user_id, modtime, userdict.key from userdict natural join (select key, max(modtime) as modtime, count(key) as num_keys from userdict group by key) mostrecent left join userdictkeys on userdictkeys.key = userdict.key order by modtime desc;
# db.session.query

# From server.py
#  subq = db.session.query(db.func.max(UserDict.indexno).label('indexno'), UserDict.filename, UserDict.key).group_by(UserDict.filename, UserDict.key).subquery()
#  interview_query = db.session.query(UserDictKeys.user_id, UserDictKeys.temp_user_id, UserDictKeys.filename, UserDictKeys.key, UserDict.dictionary, UserDict.encrypted, UserModel.email).join(subq, and_(subq.c.filename == UserDictKeys.filename, subq.c.key == UserDictKeys.key)).join(UserDict, and_(UserDict.indexno == subq.c.indexno, UserDict.key == UserDictKeys.key, UserDict.filename == UserDictKeys.filename)).join(UserModel, UserModel.id == UserDictKeys.user_id).filter(UserDictKeys.user_id == user_id, UserDictKeys.filename == filename, UserDictKeys.key == session).group_by(UserModel.email, UserDictKeys.user_id, UserDictKeys.temp_user_id, UserDictKeys.filename, UserDictKeys.key, UserDict.dictionary, UserDict.encrypted, UserDictKeys.indexno).order_by(UserDictKeys.indexno)
