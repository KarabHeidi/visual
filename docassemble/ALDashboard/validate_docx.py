from jinja2 import Undefined, DebugUndefined, ChainableUndefined
from jinja2.utils import missing
from docxtpl import DocxTemplate
from jinja2 import Environment, BaseLoader
import jinja2.exceptions
from docassemble.base.util import DAFile
from docassemble.base.parse import fix_quotes
import re

__all__ = ['CallAndDebugUndefined', 'get_jinja_errors', 'Environment', 'BaseLoader', 'DASkipUndefined']

class CallAndDebugUndefined(DebugUndefined):
    """Handles Jinja2 undefined errors by printing the name of the undefined variable.
    Extended to handle callable methods.
    """      
    def __call__(self, *pargs, **kwargs):
        return self
      
    def __getattr__(self, _: str) -> "CallAndDebugUndefined":
        return self

    __getitem__ = __getattr__  # type: ignore      
    
class DASkipUndefined(ChainableUndefined):
    """Undefined handler for Jinja2 exceptions that allows rendering most
    templates that have undefined variables. It will not fix all broken
    templates. For example, if the missing variable is used in a complex
    mathematical expression it may still break (but expressions with only two
    elements should render as ''). 
    """
    def __init__(self, *pargs, **kwargs):
        # Handle the way Docassemble DAEnvironment triggers attribute errors
        pass

    def __str__(self) -> str:
        return ''

    def __call__(self, *pargs, **kwargs)->"DASkipUndefined":
        return self

    __getitem__ = __getattr__ = __call__

    def __eq__(self, *pargs) -> bool:
        return False
        
    # need to return a bool type
    __bool__ = __ne__ = __le__ = __lt__ = __gt__ = __ge__ = __nonzero__ = __eq__

    # let undefined variables work in for loops
    def __iter__(self, *pargs)->"DASkipUndefined":
        return self
    
    def __next__(self, *pargs)->None:
        raise StopIteration        

    # need to return an int type
    def __int__(self, *pargs)->int:
        return 0

    __len__ = __int__
    
    # need to return a float type
    def __float__(self, *pargs)->float:
        return 0.0
    
    # need to return complex type
    def __complex__(self, *pargs)->complex:
        return 0j

    def __add__(self, *pargs, **kwargs)->str:
        return self.__str__()

    # type can be anything. we want it to work with `str()` function though
    # and we do not want to silently give wrong math results.
    # note that this means 1 + (undefined) or (undefined) + 1 will work but not 1 + (undefined) + 1
    __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __pow__ = __rpow__ = \
        __sub__ = __rsub__= __hash__ = __add__ 
    
    
def get_jinja_errors(the_file:DAFile, env=None)->str:
  """Just try rendering the DOCX file as a Jinja2 template and catch any errors.
  Returns a string with the errors, if any.
  """
  if not env:
    env = Environment(loader=BaseLoader,undefined=CallAndDebugUndefined)
  
  docx_template = DocxTemplate(the_file.path())
  
  try: 
    the_xml = docx_template.get_xml()
    the_xml = re.sub(r'<w:p>', '\n<w:p>', the_xml)
    the_xml = re.sub(r'({[\%\{].*?[\%\}]})', fix_quotes, the_xml)
    the_xml = docx_template.patch_xml(the_xml)
    docx_template.render({}, jinja_env=env)
  except jinja2.exceptions.TemplateSyntaxError as the_error:
    errmess = str(the_error)
    if hasattr(the_error, 'docx_context'):
      errmess += "\n\nContext:\n" + "\n".join(map(lambda x: "  " + x, the_error.docx_context))
    return errmess
  