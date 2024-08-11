from docassemble.webapp.users.models import UserModel
from docassemble.webapp.db_object import init_sqlalchemy
# db is a SQLAlchemy Engine
from sqlalchemy.sql import text
from typing import List, Tuple

db = init_sqlalchemy()

__all__ = ['speedy_get_users','speedy_get_sessions']


def speedy_get_users()->List[Tuple[int, str]]:
  """
  Return a list of all users in the database. Possibly faster than get_user_list().
  """
  the_users = UserModel.query.with_entities(UserModel.id, UserModel.email).all()
  
  return [tuple(user) for user in the_users]

def speedy_get_sessions(user_id:int=None, filename:str=None):
  """
  Return a lsit of the most recent 500 sessions, optionally tied to a specific user ID
  """
  get_sessions_query = text("""
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
  """)
  if not filename:
    filename = None # Explicitly treat empty string as equivalent to None
  if not user_id: # TODO: verify that 0 is not a valid value for user ID
    user_id = None
  
  with db.connect() as con:
    rs = con.execute(get_sessions_query, user_id=user_id, filename=filename)
  sessions = []
  for session in rs:
    sessions.append(session)
  
  return sessions

#  select userdict.filename, num_keys, userdictkeys.user_id, modtime, userdict.key from userdict natural join (select key, max(modtime) as modtime, count(key) as num_keys from userdict group by key) mostrecent left join userdictkeys on userdictkeys.key = userdict.key order by modtime desc;
# db.session.query

# From server.py
#  subq = db.session.query(db.func.max(UserDict.indexno).label('indexno'), UserDict.filename, UserDict.key).group_by(UserDict.filename, UserDict.key).subquery()
#  interview_query = db.session.query(UserDictKeys.user_id, UserDictKeys.temp_user_id, UserDictKeys.filename, UserDictKeys.key, UserDict.dictionary, UserDict.encrypted, UserModel.email).join(subq, and_(subq.c.filename == UserDictKeys.filename, subq.c.key == UserDictKeys.key)).join(UserDict, and_(UserDict.indexno == subq.c.indexno, UserDict.key == UserDictKeys.key, UserDict.filename == UserDictKeys.filename)).join(UserModel, UserModel.id == UserDictKeys.user_id).filter(UserDictKeys.user_id == user_id, UserDictKeys.filename == filename, UserDictKeys.key == session).group_by(UserModel.email, UserDictKeys.user_id, UserDictKeys.temp_user_id, UserDictKeys.filename, UserDictKeys.key, UserDict.dictionary, UserDict.encrypted, UserDictKeys.indexno).order_by(UserDictKeys.indexno) 