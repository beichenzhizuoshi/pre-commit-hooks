# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import logging
import os
import sys

if sys.platform == 'win32':  # pragma: no cover (windows)
  def _enable() -> None:
    from ctypes import POINTER
    from ctypes import windll
    from ctypes import WinError
    from ctypes import WINFUNCTYPE
    from ctypes.wintypes import BOOL
    from ctypes.wintypes import DWORD
    from ctypes.wintypes import HANDLE

    STD_ERROR_HANDLE = -12
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 4

    def bool_errcheck(result, func, args):
      if not result:
        raise WinError()
      return args

    GetStdHandle = WINFUNCTYPE(HANDLE, DWORD)(
        ('GetStdHandle', windll.kernel32), ((1, 'nStdHandle'),),
    )

    GetConsoleMode = WINFUNCTYPE(BOOL, HANDLE, POINTER(DWORD))(
        ('GetConsoleMode', windll.kernel32),
        ((1, 'hConsoleHandle'), (2, 'lpMode')),
    )
    GetConsoleMode.errcheck = bool_errcheck

    SetConsoleMode = WINFUNCTYPE(BOOL, HANDLE, DWORD)(
        ('SetConsoleMode', windll.kernel32),
        ((1, 'hConsoleHandle'), (1, 'dwMode')),
    )
    SetConsoleMode.errcheck = bool_errcheck

    # As of Windows 10, the Windows console supports (some) ANSI escape
    # sequences, but it needs to be enabled using `SetConsoleMode` first.
    #
    # More info on the escape sequences supported:
    # https://msdn.microsoft.com/en-us/library/windows/desktop/mt638032(v=vs.85).aspx
    stderr = GetStdHandle(STD_ERROR_HANDLE)
    flags = GetConsoleMode(stderr)
    SetConsoleMode(stderr, flags | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

  try:
    _enable()
  except OSError:
    terminal_supports_color = False
  else:
    terminal_supports_color = True
else:  # pragma: win32 no cover
  terminal_supports_color = True

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
TURQUOISE = '\033[46;30m'
SUBTLE = '\033[2m'
NORMAL = '\033[m'


def format_color(text: str, color: str, use_color_setting: bool) -> str:
  """Format text with color.

  Args:
      text - Text to be formatted with color if `use_color`
      color - The color start string
      use_color_setting - Whether or not to color
  """
  if use_color_setting:
    return f'{color}{text}{NORMAL}'
  else:
    return text


COLOR_CHOICES = ('auto', 'always', 'never')


def use_color(setting: str) -> bool:
  """Choose whether to use color based on the command argument.

  Args:
      setting - Either `auto`, `always`, or `never`
  """
  if setting not in COLOR_CHOICES:
    raise ValueError(setting)

  return (
      setting == 'always' or (setting == 'auto' and sys.stderr.isatty()
                              and terminal_supports_color and os.getenv('TERM') != 'dumb')
  )


def add_color_option(parser: argparse.ArgumentParser) -> None:
  parser.add_argument(
      '--color', default=os.environ.get('PRE_COMMIT_COLOR', 'always'),
      type=use_color,
      metavar='{' + ','.join(COLOR_CHOICES) + '}',
      help='Whether to use color in output.  Defaults to `%(default)s`.',
  )


LOG_LEVEL_COLORS = {
    'DEBUG': '',
    'INFO': GREEN,
    'WARNING': YELLOW,
    'ERROR': RED,
}


class LoggingHandler(logging.StreamHandler):
  def __init__(self, use_color: bool) -> None:
    super().__init__(sys.stdout)
    self.use_color = use_color

  def format(self, record: logging.LogRecord) -> str:
    msg = super().format(record)
    return format_color(msg, LOG_LEVEL_COLORS[record.levelname], self.use_color)


def init_logging_color(use_color: bool = True, **kwargs):
  if not use_color: #or not sys.stdout.isatty():
    logging.basicConfig(**kwargs)
    return

  handlers = kwargs.pop('handlers', [])
  handlers.insert(0, LoggingHandler(use_color))
  logging.basicConfig(handlers=handlers, **kwargs)
