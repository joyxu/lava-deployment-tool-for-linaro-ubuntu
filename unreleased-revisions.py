#!/usr/bin/python

import bzrlib.branch
import bzrlib.errors

from twisted.web.template import flattenString, tags

import os
import sys


def flatten(t):
    r =[]
    def _(result):
        r.append(result)
    flattenString(None, t).addCallback(_)
    return r[0]


class Component(object):

    def __init__(self, name):
        self.name = name
        self.last_release = None
        self.tip_revno = None
        self.unreleased_revisions = None


def load_manifest(fname):
    d = {}
    for line in open(fname):
        line = line.strip()
        if line.startswith('#'):
            continue
        package, version = line.split('==')
        d[package.lower().strip()] = version.strip()
    return d


def create_components_from_branches(branches=None):

    if branches is None:
        branches = os.listdir('/srv/lava/branches')

    components = {}

    for branch_name in branches:
        component = Component(branch_name)
        branch = bzrlib.branch.Branch.open(
            os.path.join('/srv/lava/branches', branch_name))
        branch.lock_read()
        try:
            tags = branch.tags.get_tag_dict()
            released_revnos = []
            for tag, revid in tags.iteritems():
                if tag.startswith('release-'):
                    try:
                        revno = branch.revision_id_to_dotted_revno(revid)
                    except bzrlib.errors.NoSuchRevision:
                        pass
                    else:
                        released_revnos.append((revno, tag[len('release-'):]))
            released_revno, release = max(released_revnos)
            component.last_release = release
            revid = branch.last_revision()
            unreleased_revs = []
            while True:
                rev = branch.repository.get_revision(revid)
                revno = branch.revision_id_to_dotted_revno(rev.revision_id)
                if revno <= released_revno:
                    break
                if rev.message != 'post release bump':
                    unreleased_revs.append((rev, revno))
                revid = rev.parent_ids[0]
            component.unreleased_revisions = unreleased_revs
        finally:
            branch.unlock()
        components[branch_name] = component

    return components

LAVA_INSTANCES =  '/srv/lava/instances'
if __name__ == '__main__':
    components = create_components_from_branches()
    instances = {}
    for instance_name in os.listdir(LAVA_INSTANCES):
        manifest_path = os.path.join(
                LAVA_INSTANCES, instance_name, 'code/current/manifest.txt')
        if not os.path.exists(manifest_path):
            continue
        instances[instance_name] = load_manifest(manifest_path)
    table = tags.table()
    heading_row = tags.tr()
    for heading in  'component', 'unreleased', 'latest release':
        heading_row(tags.th(heading))
    for instance_name in sorted(instances):
        heading_row(tags.th(instance_name))
    table(heading_row)
    for name, component in sorted(components.items()):
        row = tags.tr()
        row(tags.td(name))
        row(tags.td(str(len(component.unreleased_revisions))))
        row(tags.td(component.last_release))
        for instance_name, instance in sorted(instances.items()):
            row(tags.td(instance.get(name, 'xx')))
##        for rev, revno in component.unreleased_revisions:
##            print ' ', revno[0], rev.message.splitlines()[0][:100]
        table(row)
    print flatten(table)
