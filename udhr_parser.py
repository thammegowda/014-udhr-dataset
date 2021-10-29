#!/usr/bin/env python
#
#
# Author: Thamme Gowda
# Created: 10/18/21
import sys
import argparse
from pathlib import Path
import xmltodict
from typing import TextIO
import logging as log

log.basicConfig(level=log.INFO)
MISSING = "[missing]"


def parse_udhr_segs(xml_path: Path, out: TextIO):

    def write_line(rec, delim='\t'):
        rec = [r and r.replace('\n', ' ').replace('\t', '') or '' for r in rec]
        out.write(delim.join(rec) + '\n')

    data = xmltodict.parse(xml_path.read_text(encoding='utf8'))
    data = data['udhr']
    lang, name, script = data['@key'], data['@n'],data['@iso15924']
    # out.write(f'=== {lang} {name} {script} === \n')
    title = data.get("title") or MISSING
    write_line(['00-00', title])
    if 'preamble' in data:
        para = data['preamble']["para"]
        if isinstance(para, str):
            write_line([f'00-01', para])
        elif isinstance(para, list):
            for i, line in enumerate(para, start=1):
                write_line([f'00-{i:02d}', line])
        else:
            raise Exception(f'Unable to parse preamble {xml_path}')

    for i, art in enumerate(data['article'], start=1):
        try:
            title = art.get('title')
            if isinstance(title, str):
                pass
            elif isinstance(title, dict):
                title = title['#text']
            elif isinstance(title, list):
                title = [t for t in title if t]  # exclude Nulls
                assert len(title) == 1
                title = title[0]
            else:
                raise Exception("Dont know how to parse {title}")
            write_line([f'{i:02d}-00', title])
            if 'para' in art:
                if isinstance(art['para'], list):
                    j = 1
                    for para in art['para']:
                        if not para:
                            continue
                        write_line([f"{i:02d}-{j:02d}", para])
                        j += 1
                else:
                    write_line([f"{i:02d}-01", art['para']])
            else:
                assert 'orderedlist' in art
                assert 'listitem' in art['orderedlist']
                j = 1
                for it in art['orderedlist']['listitem']:
                    if it.get('para'):
                        write_line([f"{i:02d}-{j:02d}", it['para']])
                        j += 1
        except:
            log.warning(f"Unable to parse Article {i} in {xml_path} \n {art}")
            raise


def main(**kwargs):
    args = kwargs or vars(parse_args())
    inp, out = args['inp'], args['out']
    # inp = Path('data/xmls/udhr_eng.xml')
    parse_udhr_segs(inp, out=out)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inp", type=Path, help="Path to XML file having UDHR doc.")
    parser.add_argument("-o", "--out", type=argparse.FileType('w', encoding='utf-8'), default=sys.stdout,
                        help="Input file. Default: STDOUT")
    args = parser.parse_args()
    if args.out is sys.stdout:
        assert sys.getdefaultencoding().lower() in ('utf-8', 'utf8'), \
            f'Please set PYTHONIOENCODING=utf-8; Current encoding: {sys.getdefaultencoding()}'
    return args


if __name__ == '__main__':
    main()
