# mypy: disable-error-code="override, assignment"
from typing import Callable, Optional
from jinja2 import Undefined, DebugUndefined, ChainableUndefined
from jinja2.utils import missing
from docxtpl import DocxTemplate
from jinja2 import Environment, BaseLoader
from jinja2.ext import Extension
from jinja2.lexer import Token
import jinja2.exceptions
import re

__all__ = ["CallAndDebugUndefined", "get_jinja_errors", "Environment", "BaseLoader"]


class DAIndexError(IndexError):
    pass


class DAAttributeError(AttributeError):
    pass


nameerror_match = re.compile(
    r"\'(.*)\' (is not defined|referenced before assignment|is undefined)"
)


def extract_missing_name(the_error):
    m = nameerror_match.search(str(the_error))
    if m:
        return m.group(1)
    raise the_error


class DAEnvironment(Environment):
    def from_string(self, source, **kwargs):  # pylint: disable=arguments-differ
        source = re.sub(r"({[\%\{].*?[\%\}]})", fix_quotes, source)
        return super().from_string(source, **kwargs)

    def getitem(self, obj, argument):
        try:
            return obj[argument]
        except (DAAttributeError, DAIndexError) as err:
            varname = extract_missing_name(err)
            return self.undefined(obj=missing, name=varname)
        except (AttributeError, TypeError, LookupError):
            return self.undefined(obj=obj, name=argument, accesstype="item")

    def getattr(self, obj, attribute):
        try:
            return getattr(obj, attribute)
        except DAAttributeError as err:
            varname = extract_missing_name(err)
            return self.undefined(obj=missing, name=varname)
        except:
            return self.undefined(obj=obj, name=attribute, accesstype="attribute")


def fix_quotes(match):
    instring = match.group(1)
    n = len(instring)
    output = ""
    i = 0
    while i < n:
        if instring[i] == "\u201c" or instring[i] == "\u201d":
            output += '"'
        elif instring[i] == "\u2018" or instring[i] == "\u2019":
            output += "'"
        elif instring[i] == "&" and i + 4 < n and instring[i : i + 5] == "&amp;":
            output += "&"
            i += 4
        else:
            output += instring[i]
        i += 1
    return output


class CallAndDebugUndefined(DebugUndefined):
    """Handles Jinja2 undefined errors by printing the name of the undefined variable.
    Extended to handle callable methods.
    """

    def __call__(self, *pargs, **kwargs):
        return self

    def __getattr__(self, _: str) -> "CallAndDebugUndefined":
        return self

    __getitem__ = __getattr__  # type: ignore


null_func: Callable = lambda y: y

registered_jinja_filters: dict = {}

builtin_jinja_filters = {
    "ampersand_filter": null_func,
    "markdown": null_func,
    "add_separators": null_func,
    "inline_markdown": null_func,
    "paragraphs": null_func,
    "manual_line_breaks": null_func,
    "RichText": null_func,
    "groupby": null_func,
    "max": null_func,
    "min": null_func,
    "sum": null_func,
    "unique": null_func,
    "join": null_func,
    "attr": null_func,
    "selectattr": null_func,
    "rejectattr": null_func,
    "sort": null_func,
    "dictsort": null_func,
    "nice_number": null_func,
    "ordinal": null_func,
    "ordinal_number": null_func,
    "currency": null_func,
    "comma_list": null_func,
    "comma_and_list": null_func,
    "capitalize": null_func,
    "salutation": null_func,
    "alpha": null_func,
    "roman": null_func,
    "word": null_func,
    "bold": null_func,
    "italic": null_func,
    "title_case": null_func,
    "single_paragraph": null_func,
    "phone_number_formatted": null_func,
    "phone_number_in_e164": null_func,
    "country_name": null_func,
    "fix_punctuation": null_func,
    "redact": null_func,
    "verbatim": null_func,
    "map": null_func,
    "chain": null_func,
    "any": any,
    "all": all,
}


class DAExtension(Extension):
    def parse(self, parser):
        raise NotImplementedError()

    def filter_stream(self, stream):
        # in_var = False
        met_pipe = False
        for token in stream:
            if token.type == "variable_begin":
                # in_var = True
                met_pipe = False
            if token.type == "variable_end":
                # in_var = False
                if not met_pipe:
                    yield Token(token.lineno, "pipe", None)
                    yield Token(token.lineno, "name", "ampersand_filter")
            # if in_var and token.type == 'pipe':
            #     met_pipe = True
            yield token


def get_jinja_errors(the_file: str) -> Optional[str]:
    """Just try rendering the DOCX file as a Jinja2 template and catch any errors.
    Returns a string with the errors, if any.
    """
    env = DAEnvironment(undefined=CallAndDebugUndefined, extensions=[DAExtension])
    env.filters.update(registered_jinja_filters)
    env.filters.update(builtin_jinja_filters)

    doc = DocxTemplate(the_file)
    try:
        doc.render({}, jinja_env=env)
        return None
    except jinja2.exceptions.TemplateSyntaxError as the_error:
        errmess = str(the_error)
        extra_context = the_error.docx_context if hasattr(the_error, "docx_context") else []  # type: ignore
        if extra_context:
            errmess += "\n\nContext:\n" + "\n".join(
                map(lambda x: "  " + x, extra_context)
            )
        return errmess
