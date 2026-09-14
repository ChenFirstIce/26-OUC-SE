"""Rebuild the source inventory from pinned Git objects; does not contact remotes."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs' / 'integration'
SOURCES = json.loads((DEST / 'sources.json').read_text(encoding='utf-8'))


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def destination(branch, path):
    if branch == 'main':
        return path, 'retained; README and demo config updated for integration'
    if branch in {'dl', 'yjj'}:
        if path.startswith('backend/'):
            return 'server/' + path[8:], 'dl runtime baseline; modules/ remains unregistered legacy draft'
        if path.startswith('frontend/'):
            return 'admin-web/' + path[9:], 'dl runtime baseline; patient UI adapted from lfy interactions'
        if branch == 'dl':
            if path == 'AGENTS.md':
                return 'AGENTS.md', 'rewritten for explicitly authorized cyb scope'
            if path == 'docs/API.md':
                return 'contracts/API.md', 'relocated and extended'
            return path, 'integrated; historical development log retained as history'
        return None, 'superseded by main documentation or dl implementation; original kept in Git'
    if path.startswith(('docs/', 'assets/')):
        return 'docs/references/lfy/' + path, 'reference material retained verbatim'
    if path.startswith('src/data/assessments/'):
        return 'server/app/services/scale_catalog.py', 'semantic comparison; dl server scoring retained'
    if path.startswith('src/'):
        return 'admin-web/src/views/patient/PatientPortal.vue', 'step navigation/history adapted; local mock identity and scoring superseded by API'
    return None, 'React prototype build setup superseded; original kept in Git'


def main():
    inventory = []
    contents = {}
    summaries = {}
    for branch, sha in SOURCES.items():
        contents[branch] = {}
        paths = git('ls-tree', '-r', '--name-only', '-z', sha).decode('utf-8').split('\0')[:-1]
        code_count = 0
        for path in paths:
            data = git('show', f'{sha}:{path}')
            contents[branch][path] = data
            target, decision = destination(branch, path)
            row = dict(branch=branch, commit=sha, path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), destination=target, decision=decision)
            if Path(path).suffix in {'.py', '.ts', '.tsx', '.vue', '.js', '.ps1'}:
                code_count += 1
                row['lines'] = len(data.splitlines())
            if path.endswith('.py'):
                try:
                    tree = ast.parse(data.decode('utf-8-sig'))
                    row['functions'] = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                except SyntaxError as error:
                    row['syntax_error'] = str(error)
            inventory.append(row)
        summaries[branch] = dict(files=len(paths), code_files=code_count)
    yjj, dl = contents['yjj'], contents['dl']
    code = lambda p: Path(p).suffix in {'.py', '.ts', '.tsx', '.vue', '.js'}
    comparison = {
        'yjj_code_missing_in_dl': [p for p in yjj if code(p) and p not in dl],
        'yjj_code_changed_in_dl': [p for p in yjj if code(p) and p in dl and yjj[p] != dl[p]],
        'yjj_code_identical_in_dl': sum(code(p) and p in dl and yjj[p] == dl[p] for p in yjj),
    }
    output = dict(sources=SOURCES, summaries=summaries, comparison=comparison, files=inventory)
    (DEST / 'inventory.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(summaries=summaries, comparison=comparison), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
