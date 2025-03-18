import os
import sys
import subprocess
from pathlib import Path

from tree_sitter import Parser
from tree_sitter_languages import get_language


PROJECT_ROOT = ''


def parse_file(path: str, code_language: str) -> list[dict]:
    parser = Parser()
    parser.set_language(get_language(code_language))
    with open(path) as f:
        code = f.read()
        tree = parser.parse(code.encode('utf-8'))

    code_splits = []
    __import__('pudb').set_trace()
    for node in tree.root_node.children:
        line_start, line_end = node.start_point[0], node.end_point[1]
        print(f'Processing node[line: {line_start}-{line_end}]...')
        blamed_lines = get_git_blame(path, line_start, line_end)
        info = {'code_type': node.type, 'code_lines': blamed_lines, 'file_path': path}
        code_splits.append(info)
    return code_splits


def get_git_blame(path: str, line_start: int, line_end: int) -> list[str]:
    line_end = (line_end or line_start) + 1
    line_start += 1
    relative_path = path.replace(PROJECT_ROOT, '')[1:]
    cmd = ['git', 'blame', '-L', f'{line_start},{line_end}', relative_path]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE, text=True, check=True)
    blamed_lines = []
    commit_history = {}
    for line in result.stdout.strip().split('\n'):
        commit_hash = line.split()[0]
        commit_log = commit_history.get(commit_hash)
        if not commit_log:
            commit_cmd = ['git', 'show', '--quiet', commit_hash]
            commit_result = subprocess.run(commit_cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE, text=True, check=True)
            commit_log = commit_result.stdout.strip().replace('\n', '  ')
        blamed_lines.append(f'({commit_log}) - {line}')
    return blamed_lines


def get_project_root(path: str) -> str:
    file_path = Path(path)
    for folder in file_path.parent.parents:
        if (folder / '.git').exists():
            return str(folder)


if __name__ == '__main__':
    filepath = os.path.realpath(os.path.expanduser(sys.argv[1]))
    lang = 'python'
    PROJECT_ROOT = get_project_root(filepath)
    parse_file(filepath, lang)
