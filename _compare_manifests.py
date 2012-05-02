#!/usr/bin/python

import sys

def load(fname):
    d = {}
    for line in open(fname):
        line = line.strip()
        if line.startswith('-e'):
            # This bit is a total hack.
            _, stuff = line.split('#egg=')
            package, version, _ = stuff.split('-', 2)
            package = package.replace('_', '-')
        else:
            package, version = line.split('==')
        d[package] = version
    return d

cur = load(sys.argv[1])
new = load(sys.argv[2])

not_present = set(cur) - set(new)
new_packaged = set(new) - set(cur)
changed = {}
for package in set(cur) & set(new):
    if cur[package] != new[package]:
        changed[package] = (cur[package], new[package])

if not_present:
    print "Already installed, but not in bundle:"
    w1 = max(len(p) for p in not_present)
    for k in sorted(not_present):
        print "    %-*s %s" % (w1, k, cur[k])
if changed:
    print "To be upgraded:"
    w1 = max(len(p) for p in changed)
    w2 = max(len(t[0]) for t in changed.itervalues())
    w3 = max(len(t[1]) for t in changed.itervalues())
    for k in sorted(changed):
        print "    %-*s %-*s -> %-*s" % (w1, k, w2, changed[k][0], w3, changed[k][1])
if new_packaged:
    print "To be installed:"
    w1 = max(len(p) for p in new_packaged)
    for k in sorted(new_packaged):
        print "    %-*s %s" % (w1, k, new[k])
