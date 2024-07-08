#!/usr/bin/env python

import argparse
import json
import yaml

from gptlabel import run_label

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input_file_path', type=str, required=True)
    argparser.add_argument('--output_file', type=str, required=True)
    argparser.add_argument('--start_idx', type=int, required=True)
    argparser.add_argument('--sleep_time', type=float, required=True)
    args = argparser.parse_args()
    """在config.yaml中添加你要使用的apikey。

    reference link:
        https://ones.ainewera.com/wiki/#/team/JNwe8qUX/share/8Ucs4Ax7/page/4JBtq1bW
    """
    with open("config.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    run_label(args.input_file_path, args.output_file, args.start_idx,
              args.sleep_time, config)
