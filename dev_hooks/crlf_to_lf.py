# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import logging
from pathlib import Path


def _init_arguments():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('filenames', nargs='*',  help='Input text files.')
  parser.add_argument('-r', '--reverse', action='store_true', help='Convert LF to CRLF.')
  parser.add_argument('-v', '--verbose', action='store_true', help='Output more detailed information.')
  return parser.parse_args()


def main() -> int:
  options = _init_arguments()
  ret = 0
  logging.basicConfig(level=logging.INFO if options.verbose else logging.WARNING, format='%(message)s')
  for name in options.filenames:
    file = Path(name)
    if not file.is_file():
      continue
    with file.open('rb') as f:
      content: bytes = f.read()
      old_len = len(content)
      if options.reverse:
        content = content.replace(b'\n', b'\r\n')
      else:
        content = content.replace(b'\r\n', b'\n')
    if len(content) != old_len:
      with file.open('wb') as f:
        f.write(content)
        ret += 1
        logging.info('transform file %s to %s: %s', 'LF' if options.reverse else 'CRLF',
                     'CRLF' if options.reverse else 'LF', file)
  return ret


if __name__ == '__main__':
  raise SystemExit(main())
