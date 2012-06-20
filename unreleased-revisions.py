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
.version {
  text-align: center;
}
.highlight {
  font-weight: bold;
}
.hidden {
  display: none;
}
'''

js = '''
$(document).ready(function () {
  $("a.highlight").click(
    function (e) {
      $(this).closest("td").find(".hidden").toggle();
      console.log($(this).closest("td").find(".hidden"));
    });
});
'''

DOCTYPE = '''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
'''

def make_html(components, instances):
    table = tags.table()
    heading_row = tags.tr()
    for heading in  'component', 'unreleased', 'latest release':
        heading_row(tags.th(heading))
    for instance_name in sorted(instances):
        heading_row(tags.th(instance_name))
    table(heading_row)
    for name, component in sorted(components.items()):
        row = tags.tr()
        def td(*args, **kwargs):
            row(tags.td(*args, **kwargs))
        td(name)
        unreleased_count = len(component.unreleased_revisions)
        if unreleased_count:
            content = (
                tags.a(str(unreleased_count), href='#', class_='highlight'),
                tags.span(tags.br(), "xxx", class_='hidden'))
            td(content, class_='version')
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
##        for rev, revno in component.unreleased_revisions:
##            print ' ', revno[0], rev.message.splitlines()[0][:100]
        table(row)
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
            tags.style(css, type="text/css"),
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
