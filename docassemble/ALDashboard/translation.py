import hashlib
import math
import os
import re
import tempfile
from typing import Tuple
import xml.etree.ElementTree as ET
import zipfile

import docassemble.base.config
if not docassemble.base.config.loaded:
    docassemble.base.config.load()
from docassemble.base.config import in_celery

import docassemble.webapp.setup
import docassemble.base.astparser
from docassemble.base.error import DAError
import docassemble.base.functions
from docassemble.base.functions import word
import docassemble.base.DA
import docassemble.base.interview_cache
import docassemble.base.parse
import docassemble.base.pdftk
import docassemble.base.util
import docassemble.base.core  # for backward-compatibility with data pickled in earlier versions

import docassemble.webapp.backend
from docassemble.webapp.backend import url_for
import docassemble.webapp.clicksend
import docassemble.webapp.telnyx
import docassemble.webapp.machinelearning
from docassemble.webapp.translations import setup_translation
if not in_celery:
    import docassemble.webapp.worker

from flask import send_file, redirect, flash
import pandas

import xlsxwriter

from docassemble.base.util import DAFile
from docassemble.webapp.server import mako_parts
from typing import NamedTuple, Dict
DEFAULT_LANGUAGE = "en"

__all__ = [
    "Translation",
    "translation_file",
]

class Translation(NamedTuple):
    file: DAFile # an XLSX or XLIFF file
    untranslated_words: int # Word count for all untranslated segments that are not Mako or HTML
    untranslated_segments: int # Number of rows in the output that have untranslated text - one for each question, subquestion, field, etc.
    total_rows: int

def translation_file(yaml_filename:str, tr_lang:str ) -> Translation:
    """
    Return a tuple of the translation file in XLSX format, plus a count of the 
    number of words and segments that need to be translated.

    The word and segment count only apply when filetype="XLSX".

    This code was adjusted from the Flask endpoint-only version in server.py. XLIFF support was removed
    for now but can be added later.
    """
    filetype:str = "XLSX" # Look in server.py for support of XLIFF format, but we won't implement it here
    output_file = DAFile()
    setup_translation()
    if yaml_filename is None or not re.search(r'\S', yaml_filename):
        raise ValueError("YAML filename was not valid")
    if tr_lang is None or not re.search(r'\S', tr_lang):
        raise ValueError("You must provide a language")
    try:
        interview_source = docassemble.base.parse.interview_source_from_string(yaml_filename)
    except DAError:
        raise ValueError("Invalid interview")
    interview_source.update()
    interview_source.translating = True
    interview = interview_source.get_interview()
    tr_cache: Dict = {}
    if len(interview.translations) > 0:
        for item in interview.translations:
            if item.lower().endswith(".xlsx"):
                the_xlsx_file = docassemble.base.functions.package_data_filename(item)
                if not os.path.isfile(the_xlsx_file):
                    continue
                df = pandas.read_excel(the_xlsx_file, na_values=['NaN', '-NaN', '#NA', '#N/A'], keep_default_na=False)
                invalid = False
                for column_name in ('interview', 'question_id', 'index_num', 'hash', 'orig_lang', 'tr_lang', 'orig_text', 'tr_text'):
                    if column_name not in df.columns:
                        invalid = True
                        break
                if invalid:
                    continue
                for indexno in df.index:
                    try:
                        assert df['interview'][indexno]
                        assert df['question_id'][indexno]
                        assert df['index_num'][indexno] >= 0
                        assert df['hash'][indexno]
                        assert df['orig_lang'][indexno]
                        assert df['tr_lang'][indexno]
                        assert df['orig_text'][indexno] != ''
                        assert df['tr_text'][indexno] != ''
                        if isinstance(df['orig_text'][indexno], float):
                            assert not math.isnan(df['orig_text'][indexno])
                        if isinstance(df['tr_text'][indexno], float):
                            assert not math.isnan(df['tr_text'][indexno])
                    except:
                        continue
                    the_dict = {'interview': str(df['interview'][indexno]), 'question_id': str(df['question_id'][indexno]), 'index_num': df['index_num'][indexno], 'hash': str(df['hash'][indexno]), 'orig_lang': str(df['orig_lang'][indexno]), 'tr_lang': str(df['tr_lang'][indexno]), 'orig_text': str(df['orig_text'][indexno]), 'tr_text': str(df['tr_text'][indexno])}
                    if df['orig_text'][indexno] not in tr_cache:
                        tr_cache[df['orig_text'][indexno]] = {}
                    if df['orig_lang'][indexno] not in tr_cache[df['orig_text'][indexno]]:
                        tr_cache[df['orig_text'][indexno]][df['orig_lang'][indexno]] = {}
                    tr_cache[df['orig_text'][indexno]][df['orig_lang'][indexno]][df['tr_lang'][indexno]] = the_dict
            elif item.lower().endswith(".xlf") or item.lower().endswith(".xliff"):
                the_xlf_file = docassemble.base.functions.package_data_filename(item)
                if not os.path.isfile(the_xlf_file):
                    continue
                tree = ET.parse(the_xlf_file)
                root = tree.getroot()
                indexno = 1
                if root.attrib['version'] == "1.2":
                    for the_file in root.iter('{urn:oasis:names:tc:xliff:document:1.2}file'):
                        source_lang = the_file.attrib.get('source-language', 'en')
                        target_lang = the_file.attrib.get('target-language', 'en')
                        source_filename = the_file.attrib.get('original', yaml_filename)
                        for transunit in the_file.iter('{urn:oasis:names:tc:xliff:document:1.2}trans-unit'):
                            orig_text = ''
                            tr_text = ''
                            for source in transunit.iter('{urn:oasis:names:tc:xliff:document:1.2}source'):
                                if source.text:
                                    orig_text += source.text
                                for mrk in source:
                                    if mrk.text:
                                        orig_text += mrk.text
                                    if mrk.tail:
                                        orig_text += mrk.tail
                            for target in transunit.iter('{urn:oasis:names:tc:xliff:document:1.2}target'):
                                if target.text:
                                    tr_text += target.text
                                for mrk in target:
                                    if mrk.text:
                                        tr_text += mrk.text
                                    if mrk.tail:
                                        tr_text += mrk.tail
                            if orig_text == '' or tr_text == '':
                                continue
                            the_dict = {'interview': source_filename, 'question_id': 'Unknown' + str(indexno), 'index_num': transunit.attrib.get('id', str(indexno)), 'hash': hashlib.md5(orig_text.encode('utf-8')).hexdigest(), 'orig_lang': source_lang, 'tr_lang': target_lang, 'orig_text': orig_text, 'tr_text': tr_text}
                            if orig_text not in tr_cache:
                                tr_cache[orig_text] = {}
                            if source_lang not in tr_cache[orig_text]:
                                tr_cache[orig_text][source_lang] = {}
                            tr_cache[orig_text][source_lang][target_lang] = the_dict
                            indexno += 1
                elif root.attrib['version'] == "2.0":
                    source_lang = root.attrib['srcLang']
                    target_lang = root.attrib['trgLang']
                    for the_file in root.iter('{urn:oasis:names:tc:xliff:document:2.0}file'):
                        source_filename = the_file.attrib.get('original', yaml_filename)
                        for unit in the_file.iter('{urn:oasis:names:tc:xliff:document:2.0}unit'):
                            question_id = unit.attrib.get('id', 'Unknown' + str(indexno))
                            for segment in unit.iter('{urn:oasis:names:tc:xliff:document:2.0}segment'):
                                orig_text = ''
                                tr_text = ''
                                for source in transunit.iter('{urn:oasis:names:tc:xliff:document:2.0}source'):
                                    if source.text:
                                        orig_text += source.text
                                    for mrk in source:
                                        if mrk.text:
                                            orig_text += mrk.text
                                        if mrk.tail:
                                            orig_text += mrk.tail
                                for target in transunit.iter('{urn:oasis:names:tc:xliff:document:2.0}target'):
                                    if target.text:
                                        tr_text += target.text
                                    for mrk in target:
                                        if mrk.text:
                                            tr_text += mrk.text
                                        if mrk.tail:
                                            tr_text += mrk.tail
                                if orig_text == '' or tr_text == '':
                                    continue
                                the_dict = {'interview': source_filename, 'question_id': question_id, 'index_num': segment.attrib.get('id', str(indexno)), 'hash': hashlib.md5(orig_text.encode('utf-8')).hexdigest(), 'orig_lang': source_lang, 'tr_lang': target_lang, 'orig_text': orig_text, 'tr_text': tr_text}
                                if orig_text not in tr_cache:
                                    tr_cache[orig_text] = {}
                                if source_lang not in tr_cache[orig_text]:
                                    tr_cache[orig_text][source_lang] = {}
                                tr_cache[orig_text][source_lang][target_lang] = the_dict
                                indexno += 1
    if filetype == 'XLSX':        
        xlsx_filename = docassemble.base.functions.space_to_underscore(os.path.splitext(os.path.basename(re.sub(r'.*:', '', yaml_filename)))[0]) + "_" + tr_lang + ".xlsx"
        output_file.initialize(filename=xlsx_filename)
        workbook = xlsxwriter.Workbook(output_file.path())
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': 1})
        text = workbook.add_format()
        text.set_align('top')
        fixedcell = workbook.add_format()
        fixedcell.set_align('top')
        fixedcell.set_text_wrap()
        fixedunlockedcell = workbook.add_format()
        fixedunlockedcell.set_align('top')
        fixedunlockedcell.set_text_wrap()
        # fixedunlockedcell.set_locked(False)
        fixed = workbook.add_format()
        fixedone = workbook.add_format()
        fixedone.set_bold()
        fixedone.set_font_color('green')
        fixedtwo = workbook.add_format()
        fixedtwo.set_bold()
        fixedtwo.set_font_color('blue')
        fixedunlocked = workbook.add_format()
        fixedunlockedone = workbook.add_format()
        fixedunlockedone.set_bold()
        fixedunlockedone.set_font_color('green')
        fixedunlockedtwo = workbook.add_format()
        fixedunlockedtwo.set_bold()
        fixedunlockedtwo.set_font_color('blue')
        wholefixed = workbook.add_format()
        wholefixed.set_align('top')
        wholefixed.set_text_wrap()
        wholefixedone = workbook.add_format()
        wholefixedone.set_bold()
        wholefixedone.set_font_color('green')
        wholefixedone.set_align('top')
        wholefixedone.set_text_wrap()
        wholefixedtwo = workbook.add_format()
        wholefixedtwo.set_bold()
        wholefixedtwo.set_font_color('blue')
        wholefixedtwo.set_align('top')
        wholefixedtwo.set_text_wrap()
        wholefixedunlocked = workbook.add_format()
        wholefixedunlocked.set_align('top')
        wholefixedunlocked.set_text_wrap()
        # wholefixedunlocked.set_locked(False)
        wholefixedunlockedone = workbook.add_format()
        wholefixedunlockedone.set_bold()
        wholefixedunlockedone.set_font_color('green')
        wholefixedunlockedone.set_align('top')
        wholefixedunlockedone.set_text_wrap()
        # wholefixedunlockedone.set_locked(False)
        wholefixedunlockedtwo = workbook.add_format()
        wholefixedunlockedtwo.set_bold()
        wholefixedunlockedtwo.set_font_color('blue')
        wholefixedunlockedtwo.set_align('top')
        wholefixedunlockedtwo.set_text_wrap()
        # wholefixedunlockedtwo.set_locked(False)
        numb = workbook.add_format()
        numb.set_align('top')
        worksheet.write('A1', 'interview', bold)
        worksheet.write('B1', 'question_id', bold)
        worksheet.write('C1', 'index_num', bold)
        worksheet.write('D1', 'hash', bold)
        worksheet.write('E1', 'orig_lang', bold)
        worksheet.write('F1', 'tr_lang', bold)
        worksheet.write('G1', 'orig_text', bold)
        worksheet.write('H1', 'tr_text', bold)

        worksheet.set_column(0, 0, 25)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 12)
        worksheet.set_column(6, 6, 75)
        worksheet.set_column(6, 7, 75)
        row = 1
        seen = []
        untranslated_segments = 0
        untranslated_text = ""
        total_rows = 0
        for question in interview.all_questions:
            if not hasattr(question, 'translations'):
                continue
            language = question.language
            if language == '*':
                language = question.from_source.get_language()
            if language == '*':
                language = interview.default_language
            if language == tr_lang:
                continue
            indexno = 0
            if hasattr(question, 'id'):
                question_id = question.id
            else:
                question_id = question.name
            for item in question.translations:
                if item in seen:
                    continue
                total_rows += 1
                # The segment has already been translated and the translation is still valid
                if item in tr_cache and language in tr_cache[item] and tr_lang in tr_cache[item][language]:
                    tr_text = str(tr_cache[item][language][tr_lang]['tr_text'])
                else: # This string needs to be translated
                    tr_text = ''
                    untranslated_segments += 1
                worksheet.write_string(row, 0, question.from_source.get_name(), text)
                worksheet.write_string(row, 1, question_id, text)
                worksheet.write_number(row, 2, indexno, numb)
                worksheet.write_string(row, 3, hashlib.md5(item.encode('utf-8')).hexdigest(), text)
                worksheet.write_string(row, 4, language, text)
                worksheet.write_string(row, 5, tr_lang, text)
                mako = mako_parts(item)
                
                if not tr_text:
                    for phrase in mako:
                        if phrase[1] == 0:
                            untranslated_text += phrase[0]

                if len(mako) == 0: # Can this case occur? Not in tests
                    worksheet.write_string(row, 6, '', wholefixed)
                elif len(mako) == 1:
                    if mako[0][1] == 0:
                        worksheet.write_string(row, 6, item, wholefixed)
                    elif mako[0][1] == 1:
                        worksheet.write_string(row, 6, item, wholefixedone)
                    elif mako[0][1] == 2:
                        worksheet.write_string(row, 6, item, wholefixedtwo)
                else:
                    parts = [row, 6]
                    for part in mako:
                        if part[1] == 0:
                            parts.extend([fixed, part[0]])
                        elif part[1] == 1:
                            parts.extend([fixedone, part[0]])
                        elif part[1] == 2:
                            parts.extend([fixedtwo, part[0]])
                    parts.append(fixedcell)
                    worksheet.write_rich_string(*parts)
                mako = mako_parts(tr_text)
                if len(mako) == 0:
                    worksheet.write_string(row, 7, '', wholefixedunlocked)
                elif len(mako) == 1:
                    if mako[0][1] == 0:
                        worksheet.write_string(row, 7, tr_text, wholefixedunlocked)
                    elif mako[0][1] == 1:
                        worksheet.write_string(row, 7, tr_text, wholefixedunlockedone)
                    elif mako[0][1] == 2:
                        worksheet.write_string(row, 7, tr_text, wholefixedunlockedtwo)
                else:
                    parts = [row, 7]
                    for part in mako:
                        if part[1] == 0:
                            parts.extend([fixedunlocked, part[0]])
                        elif part[1] == 1:
                            parts.extend([fixedunlockedone, part[0]])
                        elif part[1] == 2:
                            parts.extend([fixedunlockedtwo, part[0]])
                    parts.append(fixedunlockedcell)
                    worksheet.write_rich_string(*parts)
                num_lines = item.count('\n')
                # if num_lines > 25:
                #    num_lines = 25
                if num_lines > 0:
                    worksheet.set_row(row, 15*(num_lines + 1))
                indexno += 1
                row += 1
                seen.append(item)
        for item, cache_item in tr_cache.items():
            if item in seen or language not in cache_item or tr_lang not in cache_item[language]:
                continue
            worksheet.write_string(row, 0, cache_item[language][tr_lang]['interview'], text)
            worksheet.write_string(row, 1, cache_item[language][tr_lang]['question_id'], text)
            worksheet.write_number(row, 2, 1000 + cache_item[language][tr_lang]['index_num'], numb)
            worksheet.write_string(row, 3, cache_item[language][tr_lang]['hash'], text)
            worksheet.write_string(row, 4, cache_item[language][tr_lang]['orig_lang'], text)
            worksheet.write_string(row, 5, cache_item[language][tr_lang]['tr_lang'], text)
            mako = mako_parts(cache_item[language][tr_lang]['orig_text'])
            if len(mako) == 1:
                if mako[0][1] == 0:
                    worksheet.write_string(row, 6, cache_item[language][tr_lang]['orig_text'], wholefixed)
                elif mako[0][1] == 1:
                    worksheet.write_string(row, 6, cache_item[language][tr_lang]['orig_text'], wholefixedone)
                elif mako[0][1] == 2:
                    worksheet.write_string(row, 6, cache_item[language][tr_lang]['orig_text'], wholefixedtwo)
            else:
                parts = [row, 6]
                for part in mako:
                    if part[1] == 0:
                        parts.extend([fixed, part[0]])
                    elif part[1] == 1:
                        parts.extend([fixedone, part[0]])
                    elif part[1] == 2:
                        parts.extend([fixedtwo, part[0]])
                parts.append(fixedcell)
                worksheet.write_rich_string(*parts)
            mako = mako_parts(cache_item[language][tr_lang]['tr_text'])
            if len(mako) == 1:
                if mako[0][1] == 0:
                    worksheet.write_string(row, 7, cache_item[language][tr_lang]['tr_text'], wholefixedunlocked)
                elif mako[0][1] == 1:
                    worksheet.write_string(row, 7, cache_item[language][tr_lang]['tr_text'], wholefixedunlockedone)
                elif mako[0][1] == 2:
                    worksheet.write_string(row, 7, cache_item[language][tr_lang]['tr_text'], wholefixedunlockedtwo)
            else:
                parts = [row, 7]
                for part in mako:
                    if part[1] == 0:
                        parts.extend([fixedunlocked, part[0]])
                    elif part[1] == 1:
                        parts.extend([fixedunlockedone, part[0]])
                    elif part[1] == 2:
                        parts.extend([fixedunlockedtwo, part[0]])
                parts.append(fixedunlockedcell)
                worksheet.write_rich_string(*parts)
            num_lines = cache_item[language][tr_lang]['orig_text'].count('\n')
            if num_lines > 0:
                worksheet.set_row(row, 15*(num_lines + 1))
            row += 1
        workbook.close()
        untranslated_words = len(re.findall(r"\w+", untranslated_text))        
        return Translation(output_file, untranslated_words,untranslated_segments, total_rows)
    raise ValueError("That's not a valid filetype for a translation file")