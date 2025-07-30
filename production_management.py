"""Simple production management script

This script can parse SWOOD ReportLists XML to summarise material stock,
load piece lists from Excel, filter pieces requiring Homag processing
(tempo > 0), and export results back to Excel.
"""

import os
import pandas as pd
import xmltodict


def parse_material_stock_from_xml(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        data = xmltodict.parse(f.read())
    generics = data.get('CATEGORY', {}).get('GENERIC', [])
    if isinstance(generics, dict):
        generics = [generics]
    records = []
    for g in generics:
        if str(g.get('GENERIC_TYPE', '')).upper() == 'MATERIAL_STOCK':
            name = g.get('ID') or g.get('STR1')
            qty = float(g.get('STR5') or 0)
            area = float(g.get('STR2') or g.get('STR4') or 0)
            time = float(g.get('STR7') or 0)
            if name:
                records.append({'Material': name, 'Quantity': qty, 'Area': area, 'Time': time})
    return pd.DataFrame(records)


def load_piece_list_from_excel(path):
    return pd.read_excel(path, engine='openpyxl')


def filter_homag_pieces(df, time_col='Tempo (s)'):
    return df[df[time_col].fillna(0) > 0].copy()


def export_to_excel(df, path):
    df.to_excel(path, index=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Production management utility')
    parser.add_argument('--xml', type=str)
    parser.add_argument('--excel', type=str)
    parser.add_argument('--outdir', default='.')
    args = parser.parse_args()
    if args.xml and os.path.exists(args.xml):
        mdf = parse_material_stock_from_xml(args.xml)
        print(mdf)
        export_to_excel(mdf, os.path.join(args.outdir, 'material_summary.xlsx'))
    if args.excel and os.path.exists(args.excel):
        df = load_piece_list_from_excel(args.excel)
        hdf = filter_homag_pieces(df)
        print(hdf)
        export_to_excel(hdf, os.path.join(args.outdir, 'homag_pieces.xlsx'))
