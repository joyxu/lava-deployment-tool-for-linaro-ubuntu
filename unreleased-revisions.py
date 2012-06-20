#!/usr/bin/python
import bzrlib.branch
import bzrlib.errors
import os
import sys


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
    print 'component', 'unreleased', 'latest release',
    for instance_name in sorted(instances):
        print instance_name,
    print
    for name, component in sorted(components.items()):
        print name, len(component.unreleased_revisions), component.last_release,
        for instance_name, instance in sorted(instances.items()):
            print instance.get(name, 'xx'),
        print
#        for rev, revno in component.unreleased_revisions:
#            print ' ', revno[0], rev.message.splitlines()[0][:100]
