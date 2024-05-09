# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess


def _init_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filenames', nargs='*',  help='Input text files.')
    parser.add_argument('-c', '--command',
                        help='special vcpkg command path', default='vcpkg')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Output more detailed information.')
    return parser.parse_args()


def main() -> int:
    options = _init_arguments()
    command = [options.command, 'format-manifest', '--x-wait-for-lock']
    command.extend(options.filenames)
    return subprocess.call(command)


if __name__ == '__main__':
    raise SystemExit(main())
