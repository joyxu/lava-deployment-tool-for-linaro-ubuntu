#!/usr/bin/python
import bzrlib.branch
import bzrlib.errors
import os
import sys

branches = os.listdir('/srv/lava/branches')

if sys.argv[1:]:
    branches = sys.argv[1:]

for branch_name in sorted(branches):
    print branch_name,
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
                released_revnos.append((revno, tag[len('release-'):]))
        released_revno, release = max(released_revnos)
        print release,
        revid = branch.last_revision()
        unreleased_revs = []
        while True:
            rev = branch.repository.get_revision(revid)
            revno = branch.revision_id_to_dotted_revno(rev.revision_id)
            if revno <= released_revno:
                break
            unreleased_revs.append((rev, revno))
            revid = rev.parent_ids[0]
        if unreleased_revs:
            print len(unreleased_revs), 'unreleased revisions'
            for rev, revno in unreleased_revs:
                print ' ', revno[0], rev.message.splitlines()[0][:100]
        else:
            print ' no unreleased revisions'
    finally:
        branch.unlock()
