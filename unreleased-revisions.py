#!/usr/bin/python

import bzrlib.branch
import bzrlib.errors

from twisted.web.template import CDATA, flattenString, tags

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
            branch_tags = branch.tags.get_tag_dict()
            released_revnos = []
            for tag, revid in branch_tags.iteritems():
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


def load_instances():
    instances = {}
    for instance_name in os.listdir(LAVA_INSTANCES):
        manifest_path = os.path.join(
                LAVA_INSTANCES, instance_name, 'code/current/manifest.txt')
        if not os.path.exists(manifest_path):
            continue
        instances[instance_name] = load_manifest(manifest_path)
    return instances


css = '''
body {
  font-family: "Ubuntu", "Lucida Sans Unicode", "Lucida Grande", Sans-Serif;
}
td.version {
  text-align: center;
}
.highlight {
  font-weight: bold;
}
.hidden {
  display: none;
}
table.main {
  border-collapse: collapse;
  width: 80ex;
}
table.main > thead > tr > th {
  padding: 10px 8px;
  border:  1px solid #ccc;
  border-bottom: 2px solid black;
}
table.main > tbody > tr > td {
  padding: 6px 8px;
  border: 1px solid #ccc;
}
'''

js = '''
$(document).ready(function () {
  $("td.clickable").click(
    function (e) {
      $("#show-" + $(this).attr("id")).toggle();
    });
});
'''

DOCTYPE = '''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
'''

def format_revlist(revlist):
    revs = tags.table()
    for rev, revno in revlist:
        r = tags.tr()
        r(tags.td(str(revno[0])))
        r(tags.td(rev.message.splitlines()[0][:100],
                  style="text-align: left"))
        revs(r)
    return revs

_id = 0
def get_id():
    global _id
    _id += 1
    return 'id' + str(_id)

def make_html(components, instances):
    table = tags.table(class_='main')
    heading_row = tags.tr()
    for heading in  'component', 'unreleased', 'latest release':
        heading_row(tags.th(heading))
    for instance_name in sorted(instances):
        heading_row(tags.th(instance_name))
    table(tags.thead(heading_row))
    tbody = tags.tbody()
    for name, component in sorted(components.items()):
        row = tags.tr()
        extra_rows = []
        def td(*args, **kwargs):
            row(tags.td(*args, **kwargs))
        td(name)
        unreleased_count = len(component.unreleased_revisions)
        if unreleased_count:
            id_ = get_id()
            content = (
                tags.a(str(unreleased_count), href='#', class_='highlight'),)
            td(content, class_='version clickable', id=id_)
            extra_rows.append(
                tags.tr(
                    tags.td(
                        format_revlist(component.unreleased_revisions),
                        colspan=str(3 + len(instances))),
                    class_='hidden',
                    id="show-" + id_))
        else:
            td(str(unreleased_count), class_='version')
        td(component.last_release, class_='version')
        for instance_name, instance in sorted(instances.items()):
            ver = instance.get(name)
            if ver is None:
                td(u'\N{EM DASH}', class_='version')
            elif ver == component.last_release:
                td(ver, class_='version')
            else:
                td(tags.a(ver, href='#'), class_='version highlight')
        tbody(row, *extra_rows)
    table(tbody)
    html = tags.html(
        tags.head(
            tags.title("Deployment report"),
            tags.script(
                src='https://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js',
                type='text/javascript'),
            tags.script(
                src='https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.18/jquery-ui.min.js',
                type='text/javascript'),
            tags.script(CDATA(js), type='text/javascript'),
            tags.style(CDATA(css), type="text/css"),
            ),
        tags.body(
            tags.h1("Deployment report"),
            table,
            ),
        )
    html(xmlns="http://www.w3.org/1999/xhtml")
    return DOCTYPE + flatten(html)


LAVA_INSTANCES =  '/srv/lava/instances'


if __name__ == '__main__':
    components = create_components_from_branches()
    instances = load_instances()
    print make_html(components, instances)
