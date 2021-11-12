#!/usr/bin/env python
#
#
# Author: Thamme Gowda
# Created: 10/28/21

from pathlib import Path
import sys
import argparse
import logging
import pandas as pd

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(ch)

MISSING = ''
MAX_SECT = 31


def read_tsv(path: Path):
    res = [[] for _ in range(MAX_SECT)]
    for line in path.read_text(encoding='utf-8').splitlines(keepends=False):
        seg_id, text = line.split('\t')
        sec_id, para_id = seg_id.strip().split('-')
        sec_id, para_id = int(sec_id), int(para_id)
        assert 0 <= sec_id < MAX_SECT
        # res[sec_id][para_id] = text
        if para_id > len(res[sec_id]):
            n_missing = para_id - len(res[sec_id])
            for _ in range(n_missing):
                res[sec_id].append(MISSING)
        assert para_id == len(res[sec_id]), f'{path} :: {seg_id}; but {res[sec_id]}'
        res[sec_id].append(text)
    return res


def read_tsvs(data_dir: Path):
    assert data_dir.exists()
    lang_files = list(sorted(data_dir.glob("udhr_*.tsv")))
    log.info(f"Found {len(lang_files)} files in {data_dir}")
    all_data = {}
    for lang_file in lang_files:
        name = lang_file.name.replace('.tsv', '').replace('udhr_', '')
        assert name not in all_data
        all_data[name] = read_tsv(lang_file)
    return all_data


def align_tsvs(data_dir: Path):
    raw_data = read_tsvs(data_dir)

    max_para_ids = [-1 for _ in range(MAX_SECT)]
    for name, data in raw_data.items():
        assert len(data) <= MAX_SECT
        for sec_id, paras in enumerate(data):
            max_para_ids[sec_id] = max(len(paras), max_para_ids[sec_id])
    # each row is a language
    row_ids = list(sorted(raw_data.keys()))
    # each column is a segment
    col_ids = [(sec_id, para_id) for sec_id, max_id in enumerate(max_para_ids) for para_id in range(max_id)]
    log.info(f"Creating a table of Langs x Segs = {len(row_ids)}x{len(col_ids)}")
    table = [[None for c in col_ids] for r in row_ids]
    for r, lang_name in enumerate(row_ids):
        for c, (sec_id, para_id) in enumerate(col_ids):
            sec = raw_data[lang_name][sec_id] if sec_id < len(raw_data[lang_name]) else []
            table[r][c] = sec[para_id] if para_id < len(sec) else MISSING
    col_ids = ['Lang'] + [f'{x:02d}-{y:02d}' for x, y in col_ids]
    for i in range(len(row_ids)):
        table[i] = [row_ids[i]] + table[i]
    df = pd.DataFrame.from_records(table, columns=col_ids)
    return df


def main(**kwargs):
    args = kwargs or vars(parse_args())
    df = align_tsvs(data_dir=args['data_dir'])
    out = args['out']
    df.to_excel(f'{out}.xlsx', sheet_name="Aligned UDHR", encoding='utf-8')
    df.to_csv(f'{out}.tsv', sep='\t', index=False)
    log.info("done")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inp", dest='data_dir', type=Path, required=True,
                        help="Input dir containing tsvs.")
    parser.add_argument("-o", "--out", required=True, help="Output file prefix")
    return parser.parse_args()


if __name__ == '__main__':
    main()
