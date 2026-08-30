#!/usr/bin/env python3
"""Zero-dependency validator for workflow.yaml (schema v1.1, see workflow-definition skill).

Usage:  python validate-workflow.py workflow.yaml [--skills-dir PATH]
Exit:   0 = valid, 1 = invalid (errors printed). Warnings printed but do not fail.

Supports the YAML subset used by workflow definitions: nested maps, list items,
scalars (strings / ints / bools), inline lists [a, b], comments, single/double
quoted strings. No anchors, no multi-line strings.
"""
import sys, os, re

# ---------------------------------------------------------------- parser ---

def _strip_comment(line):
    in_q = None
    for i, ch in enumerate(line):
        if ch in "\"'":
            if in_q == ch:
                in_q = None
            elif in_q is None:
                in_q = ch
        elif ch == '#' and in_q is None and (i == 0 or line[i - 1] in ' \t'):
            return line[:i].rstrip()
    return line.rstrip()

def _scalar(s):
    s = s.strip()
    if not s:
        return None
    if s.startswith('[') and s.endswith(']'):
        inner = s[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in inner.split(',')]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s == 'true':
        return True
    if s == 'false':
        return False
    if re.fullmatch(r'-?\d+', s):
        return int(s)
    return s

def parse_yaml(text):
    """Line-indentation parser for the supported subset. Returns (root, errors)."""
    root = {}
    stack = []   # (indent, container) — containers are dicts or lists
    pend = []    # parallel: pending key (list under construction) per level
    root_pend = None
    errors = []

    def target():
        return stack[-1][1] if stack else root

    def pend_of():
        return pend[-1] if stack else root_pend

    def set_pend(k):
        nonlocal root_pend
        if stack:
            pend[-1] = k
        else:
            root_pend = k

    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(' '))
        content = line.strip()
        while stack and stack[-1][0] > indent:
            stack.pop()
            pend.pop()

        if content.startswith('- '):
            body = content[2:].strip()
            parent = target()
            if isinstance(parent, dict):
                pk = pend_of()
                if pk is None:
                    errors.append('list item without an owning key: %r' % line)
                    continue
                lst = parent.get(pk)
                if not isinstance(lst, list):
                    lst = []
                    parent[pk] = lst
            else:
                lst = parent
            if ':' in body and not (body[0] in "\"'"):
                k, _, v = body.partition(':')
                k, v = k.strip(), v.strip()
                item = {k: _scalar(v)}
                lst.append(item)
                stack.append((indent + 2, item))
                pend.append(k if not v else None)
            else:
                lst.append(_scalar(body))
        else:
            if ':' not in content:
                errors.append('unparsable line: %r' % line)
                continue
            k, _, v = content.partition(':')
            k, v = k.strip(), v.strip()
            t = target()
            if isinstance(t, dict):
                t[k] = _scalar(v)
                set_pend(k if not v else None)
            else:
                errors.append('key under a scalar list item: %r' % line)
    return root, errors

# ------------------------------------------------------------- validation ---

VALID_ROLES = {'intake', 'router', 'context-builder', 'executor', 'coordinator',
               'validator', 'knowledge', 'closeout'}

def load_skills(skills_dir):
    """Return set of installed skill names found under skills_dir."""
    names = set()
    for dirpath, _dirs, files in os.walk(skills_dir):
        if 'SKILL.md' not in files:
            continue
        p = os.path.join(dirpath, 'SKILL.md')
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                for ln in f:
                    m = re.match(r'^name:\s*(\S+)', ln)
                    if m:
                        names.add(m.group(1))
                        break
        except OSError:
            continue
    return names

def check(data, skills_dir):
    errors, warnings = [], []

    for k in ('name', 'version', 'nodes', 'edges', 'final'):
        if k not in data or data[k] in (None, [], ''):
            errors.append('missing required field: %s' % k)

    if 'nodes' not in data or not isinstance(data['nodes'], list):
        return errors, warnings
    if 'edges' not in data or not isinstance(data['edges'], list):
        return errors, warnings

    nodes, edges, final = data['nodes'], data['edges'], data.get('final')

    # 3. node identity
    ids = []
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            errors.append('node #%d is not a mapping' % i)
            continue
        nid = n.get('id')
        if not nid:
            errors.append('node #%d missing id' % i)
            continue
        if nid in ids:
            errors.append('duplicate node id: %s' % nid)
        ids.append(nid)
        if not n.get('skill'):
            errors.append('node %s missing skill' % nid)
        if n.get('role') not in VALID_ROLES:
            errors.append('node %s: invalid role %r (valid: %s)'
                          % (nid, n.get('role'), ', '.join(sorted(VALID_ROLES))))

    idset = set(ids)

    # 4. edge integrity
    out = {i: [] for i in ids}   # normal out-edges (loop edges excluded)
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            errors.append('edge #%d is not a mapping' % i)
            continue
        f, t = e.get('from'), e.get('to')
        if f not in idset:
            errors.append('edge #%d: unknown from %r' % (i, f))
        if t not in idset:
            errors.append('edge #%d: unknown to %r' % (i, t))
        if f == t and f in idset:
            errors.append('edge #%d: self-loop on %s' % (i, f))
        if e.get('kind') not in (None, 'normal', 'on_pass', 'on_failure'):
            errors.append('edge #%d: invalid kind %r' % (i, e.get('kind')))
        if not isinstance(e.get('loop', False), bool):
            errors.append('edge #%d: loop must be boolean' % i)
        if f in idset and t in idset and not e.get('loop') and e.get('kind') != 'on_failure':
            out[f].append(t)

    # 5. cycle check (DFS over non-loop edges)
    VIS, STACK = 1, 2
    state = {}
    cyc = []

    def dfs(u):
        state[u] = STACK
        for v in out.get(u, []):
            if state.get(v) == STACK:
                cyc.append((u, v))
            elif state.get(v) != VIS:
                dfs(v)
        state[u] = VIS

    for u in ids:
        if state.get(u) != VIS:
            dfs(u)
    if cyc:
        errors.append('cycle(s) not marked with loop: true -> %s' % cyc[:5])

    # 6. artifact closure
    produced = set()
    for n in nodes:
        produced.update(n.get('outputs') or [])
    for n in nodes:
        for a in (n.get('inputs') or []):
            if a not in produced:
                errors.append('node %s input %r produced by no node' % (n.get('id'), a))
    # ancestor-closure warnings (approximation: any non-loop edge path)
    anc = {i: set() for i in ids}
    changed = True
    while changed:
        changed = False
        for e in edges:
            if e.get('loop') or e.get('from') not in anc or e.get('to') not in anc:
                continue
            f, t = e['from'], e['to']
            new = anc[f] | {f}
            if not new <= anc[t]:
                anc[t] |= new
                changed = True
    for n in nodes:
        nid = n.get('id')
        for a in (n.get('inputs') or []):
            upstream = set()
            for u in anc.get(nid, set()):
                for nn in nodes:
                    if nn.get('id') == u:
                        upstream.update(nn.get('outputs') or [])
            if a not in upstream:
                warnings.append('node %s input %r not produced by its ancestor closure '
                                '(ok for branch/loop products)' % (nid, a))

    # 7. router labels
    for i in ids:
        outs = [e for e in edges if e.get('from') == i and not e.get('loop')]
        if len(outs) >= 2:
            for e in outs:
                if not e.get('label'):
                    warnings.append('router node %s: edge to %s has no label (condition?)' % (i, e.get('to')))

    # 8. gate completeness
    for i in ids:
        kinds = [e.get('kind') for e in edges if e.get('from') == i and not e.get('loop')]
        has_p, has_f = 'on_pass' in kinds, 'on_failure' in kinds
        if has_p != has_f:
            errors.append('gate node %s must have BOTH on_pass and on_failure edges' % i)
        if has_p and kinds.count('on_pass') != 1 or has_f and kinds.count('on_failure') != 1:
            errors.append('gate node %s: exactly one on_pass and one on_failure edge required' % i)

    # 9. independent-axis rule
    indeg = {i: [e for e in edges if e.get('to') == i and not e.get('loop')] for i in ids}
    for n in nodes:
        if n.get('independent') and indeg.get(n.get('id')):
            errors.append('independent node %s must have no incoming edges (except loop)' % n.get('id'))

    # 10. terminal rule
    if final in idset:
        outs = [e for e in edges if e.get('from') == final and not e.get('loop')]
        if outs:
            errors.append('final node %s has outgoing edges: %s' % (final, [e.get('to') for e in outs]))
    else:
        errors.append('final %r is not a defined node' % final)

    # 11. skill existence
    if skills_dir:
        installed = load_skills(skills_dir)
        for n in nodes:
            s = n.get('skill')
            if s and s not in installed:
                errors.append('node %s: skill %r not found under %s' % (n.get('id'), s, skills_dir))

    return errors, warnings

# ------------------------------------------------------------------ main ---

def main(argv):
    if not argv:
        print('usage: validate-workflow.py workflow.yaml [--skills-dir PATH]')
        return 2
    path, skills_dir = argv[0], None
    if '--skills-dir' in argv:
        skills_dir = argv[argv.index('--skills-dir') + 1]
    if not os.path.isfile(path):
        print('ERROR: file not found: %s' % path)
        return 1
    with open(path, encoding='utf-8', errors='replace') as f:
        text = f.read()
    data, perr = parse_yaml(text)
    if perr:
        print('PARSE ERRORS:')
        for e in perr:
            print('  - %s' % e)
        return 1
    if skills_dir is None:
        default = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'hermes', 'skills')
        # Hermes-installed default; absent on non-Hermes machines -> existence check skipped
        skills_dir = default if os.path.isdir(default) else None
    errors, warnings = check(data, skills_dir)
    print('workflow: %s v%s (nodes=%d, edges=%d, final=%s)'
          % (data.get('name', '?'), data.get('version', '?'),
             len(data.get('nodes', [])), len(data.get('edges', [])), data.get('final', '?')))
    for w in warnings:
        print('WARN: %s' % w)
    if errors:
        print('INVALID (%d error(s)):' % len(errors))
        for e in errors:
            print('  - %s' % e)
        return 1
    print('VALID')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
