# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import codecs
import logging
from pathlib import Path

import chardet
import yaml

try:
    from dev_hooks import color
except ModuleNotFoundError:
    import color


def _guess_file_encoding(file: Path) -> dict:
    with file.open('rb') as f:
        content = f.read()
        return chardet.detect(content)


def _hook_encoding(encoding: str) -> str:
    # gb2312 部分编码不识别,gbk完全兼容,因此替换 gb2312 为 gbk
    if encoding.lower() == 'gb2312':
        return 'gbk'
    return encoding


def is_contains_chinese(content: str):
    for c in content:
        if '\u4e00' <= c <= '\u9fff':
            return True
    return False


def _transform_file_encoding(file: Path, input_encoding: str, output_encoding: str) -> bool:
    try:
        with file.open('r', encoding=input_encoding) as f:
            content = f.read()
        content = content.encode(output_encoding)
        with file.open('wb') as f:
            f.write(content)
        return True
    except UnicodeDecodeError as e:
        logging.error('Decoding file failed, encoding error: %s', e)
    except UnicodeEncodeError as e:
        logging.error('Transcoding file failed, encoding error: %s', e)
    return False


def _transform_chinese_file_encoding(file: Path, input_encoding: str, output_encoding: str) -> bool:
    try:
        with file.open('r', encoding=input_encoding) as f:
            content = f.read()
        if is_contains_chinese(content):
            content = content.encode(output_encoding)
            with file.open('wb') as f:
                f.write(content)
            return True
    except UnicodeDecodeError as e:
        logging.error('Decoding file failed, encoding error: %s', e)
    except UnicodeEncodeError as e:
        logging.error('Transcoding file failed, encoding error: %s', e)
    return False


def _execute_restore_action(options: argparse.Namespace) -> int:
    root = Path(options.root)
    if not Path(root, '.git').is_dir():
        logging.error('Input directory does not contain .git: %s', root)
        return 0
    yaml_config = Path(root, '.git', 'post_commit_config.yaml')
    if not yaml_config.is_file():
        return 0
    ret = 0
    with yaml_config.open('r', encoding='utf-8') as f:
        changed: list[dict] = yaml.safe_load(f)
        for item in changed:
            if _transform_file_encoding(Path(item['path']), item['to_encoding'], item['from_encoding']):
                logging.info('restore encoding ==> %s, from: %s, to: %s',
                             item['path'], item['from_encoding'], item['to_encoding'])
                ret += 1
    yaml_config.unlink()
    return ret


def _execute_transform_action(options: argparse.Namespace) -> int:
    root = Path(options.root)
    if not Path(root, '.git').is_dir():
        logging.warning('Input directory does not contain .git: %s', root)
        return 0
    output_encoding = codecs.lookup(options.encoding)
    if not output_encoding:
        logging.error('Output file encoding not supported: %s',
                      options.encoding)
        return 0

    output_encoding = _hook_encoding(output_encoding.name)
    ret = 0
    changed_files = []
    yaml_config = Path(root, '.git', 'post_commit_config.yaml')

    logging.info('The files for this inspection are: %s', options.filenames)

    for file in options.filenames:
        path = Path(file).resolve()
        if not path.is_file():
            continue
        file_attr = _guess_file_encoding(path)
        input_encoding = file_attr.get('encoding')
        if file_attr.get('confidence') < options.confidence:
            logging.info('Detect file encoding accuracy is too low, path: %s, encoding: %s, confidence: %s, min confidence: %s',
                         path, input_encoding, file_attr.get('confidence'), options.confidence)
            continue

        # 规范化编码名称,后续好比较
        input_attr = codecs.lookup(input_encoding)
        if not input_attr:
            logging.error(
                'Input file encoding not supported: %s', input_encoding)
            continue
        input_encoding = _hook_encoding(input_attr.name)
        if output_encoding == input_encoding or input_encoding == 'ascii':
            continue
        # 检测上次提交结果,如果存在则不转码避免文件损坏
        if yaml_config.is_file():
            logging.error('There is a encoding change in the last submitted file. \
To prevent the file from being damaged, \
please manually repair the file code or forcefully delete the file: %s', yaml_config)
            return 10000

        changed = _transform_file_encoding(
            path, input_encoding, output_encoding)
        if changed:
            logging.info('transform encoding ==> %s, from: %s to: %s',
                         path, input_encoding, output_encoding)
            ret += 1
        if options.force or not changed:
            continue
        # 需要保存编码,等待 post-commit 时恢复编码
        item = {}
        item['path'] = str(path)
        item['from_encoding'] = input_encoding
        item['to_encoding'] = output_encoding
        changed_files.append(item)

    if changed_files:
        with yaml_config.open('w', encoding='utf-8') as f:
            yaml.dump(changed_files, f, allow_unicode=True)
    return ret


def _execute_chinese_transform_action(options: argparse.Namespace) -> int:
    """仅检测到文件包含中文时才转码

    Args:
        options (argparse.Namespace): 参数选项

    Returns:
        int: 实际被转码的文件数量
    """
    output_encoding = codecs.lookup(options.encoding)
    ret = 0
    if not output_encoding:
        logging.error('Output file encoding not supported: %s',
                      options.encoding)
        return 0
    output_encoding = _hook_encoding(output_encoding.name)
    for file in options.filenames:
        path = Path(file)
        if not path.is_file():
            continue
        file_attr = _guess_file_encoding(path)
        input_encoding = file_attr.get('encoding')
        if file_attr.get('confidence') < options.confidence:
            logging.info('Detect file encoding accuracy is too low, path: %s, encoding: %s, confidence: %s, min confidence: %s',
                         path, input_encoding, file_attr.get('confidence'), options.confidence)
            continue
        input_encoding = _hook_encoding(input_encoding)
        if output_encoding == input_encoding or input_encoding == 'ascii':
            continue
        if _transform_chinese_file_encoding(path, input_encoding, output_encoding):
            ret += 1
            logging.info('transform chinese encoding ==> %s, from: %s, to: %s',
                         path, input_encoding, output_encoding)
    return ret


def _init_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filenames', nargs='*',  help='Input text files.')
    parser.add_argument('-e', '--encoding', default='utf-8',
                        help='Set automatic conversion file encoding.')
    parser.add_argument('-v', '--verbose',
                        action='store_true', help='Show more output.')
    parser.add_argument('-r', '--restore', action='store_true',
                        help='Automatically restore file encoding.')
    parser.add_argument('-f', '--force', action='store_true',
                        help='Coercion encoding is not recoverable.')
    parser.add_argument('--chinese', action='store_true',
                        help='Convert file encodings containing chinese.')
    parser.add_argument(
        '--root', default=Path.cwd(), help='Specify the root directory of the git repository and call it from the command line.')
    parser.add_argument('--confidence', type=float, default=0.725,
                        help='Specifies the accuracy of guessing file encoding.')

    color.add_color_option(parser)

    return parser.parse_args()


def main():
    options = _init_arguments()
    color.init_logging_color(options.color, format='%(message)s')
    if options.verbose:
        logging.root.setLevel(logging.INFO)
    if options.chinese:
        return _execute_chinese_transform_action(options)
    if options.restore:
        return _execute_restore_action(options)
    else:
        return _execute_transform_action(options)


if __name__ == '__main__':
    raise SystemExit(main())
