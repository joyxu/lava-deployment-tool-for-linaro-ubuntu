#!/usr/bin/python

import bzrlib.branch
import bzrlib.errors

from twisted.web.template import CDATA, flattenString, tags

import os


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
        self.tip_revid = None
        self.unreleased_revisions = None


def load_manifest(fname):
    d = {}
    from_line = None
    for line in open(fname):
        line = line.strip()
        if line.startswith('# from '):
            from_line = line[len('# from '):-1]
            if from_line.startswith('EGG'):
                from_line = None
        if line.startswith('#'):
            continue
        package, version = line.split('==')
        d[package.lower().strip()] = (version.strip(), from_line)
        from_line = None
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
            revno2release = {}
            release2revno = {}
            for tag, revid in branch_tags.iteritems():
                if tag.startswith('release-'):
                    try:
                        revno = branch.revision_id_to_dotted_revno(revid)
                    except bzrlib.errors.NoSuchRevision:
                        pass
                    else:
                        if len(revno) > 1:
                            continue
                        revno2release[revno[0]] = tag[len('release-'):]
                        release2revno[tag[len('release-'):]] = revno[0]
            if revno2release:
                component.released_revno = max(revno2release)
                component.last_release = revno2release[max(revno2release)]
            else:
                component.released_revno = None
            component.release2revno = release2revno
            component.revno2release = revno2release
            revno, revid = branch.last_revision_info()
            component.tip_revno = revno
            component.tip_revid = revid
            mainline_revs = []
            unreleased_revs = []
            while True:
                rev = branch.repository.get_revision(revid)
                if rev.message.strip() != 'post release bump':
                    if component.released_revno and revno > component.released_revno:
                        unreleased_revs.append((rev, revno))
                    mainline_revs.append((rev, revno))
                if not rev.parent_ids:
                    break
                revid = rev.parent_ids[0]
                revno -= 1
            component.unreleased_revisions = unreleased_revs
            component.mainline_revs = mainline_revs
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
.clickable {
  cursor: pointer;
}
.hidden {
  display: none;
}
table.main {
  border-collapse: collapse;
  width: 80ex;
}
table.inner {
  width: 100%;
}
table.inner > tbody > tr > td {
  width: 4ex;
}
table.inner > tbody > tr > td+td {
  width: auto;
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
      e.preventDefault();
      $("#show-" + $(this).attr("id")).toggle();
    });
});
'''

DOCTYPE = '''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
'''

def format_revlist(revlist, name=None):
    table = tags.table(class_='inner')
    if name:
        table(tags.thead(tags.tr(tags.th(name, colspan="2"))))
    revs = tags.tbody()
    table(revs)
    for rev, revno in revlist:
        r = tags.tr()
        r(tags.td(str(revno)))
        r(tags.td(rev.message.splitlines()[0][:100],
                  style="text-align: left"))
        revs(r)
    return table

_id = 0
def get_id():
    global _id
    _id += 1
    return 'id' + str(_id)

def make_html(components, instances):
    table = tags.table(class_='main')
    heading_row = tags.tr()
    for heading in  'component', 'tip revno', 'unreleased revisions', 'latest release':
        heading_row(tags.th(heading))
    for instance_name in sorted(instances):
        heading_row(tags.th(instance_name, class_="instance-name"))
    table(tags.thead(heading_row))
    tbody = tags.tbody()
    for name, component in sorted(components.items()):
        row = tags.tr(class_="component")
        revs_between_ids = {}
        extra_rows = []
        def td(*args, **kwargs):
            row(tags.td(*args, **kwargs))
        td(name)
        td(str(component.tip_revno), class_='version')
        unreleased_count = len(component.unreleased_revisions)
        if unreleased_count:
            id_ = get_id()
            td(
                tags.a(str(unreleased_count), href='#', class_='highlight'),
                class_='version clickable', id=id_)
            sub_name = 'revs between %s (r%s) and tip (r%s)' % (
                component.last_release, component.released_revno,
                component.tip_revno)
            extra_rows.append(
                tags.tr(
                    tags.td(
                        format_revlist(component.unreleased_revisions, name=sub_name),
                        colspan=str(4 + len(instances))),
                    class_='hidden',
                    id="show-" + id_))
        elif not component.last_release:
            td(u'\N{EM DASH}', class_='version')
        else:
            td(str(unreleased_count), class_='version')
        if component.last_release:
            td(component.last_release, class_='version')
        else:
            td(u'???', class_='version')
        for instance_name, instance in sorted(instances.items()):
            ver, location = instance.get(name, (None, None))
            if ver is None:
                td(u'\N{EM DASH}', class_='version')
            elif ver == component.last_release:
                td(ver, class_='version')
            elif ver in component.release2revno:
                revno_low = component.release2revno[ver]
                sub_name = 'revs between %s (r%s) and %s (r%s)' % (
                    ver, revno_low,
                    component.last_release, component.released_revno)
                revlist = []
                for rev, revno in component.mainline_revs:
                    if revno_low < revno < component.released_revno:
                        revlist.append((rev, revno))
                if revlist:
                    id_ = get_id()
                    revs_between_ids[revno_low] = id_
                    extra_rows.append(
                        tags.tr(
                            tags.td(
                                format_revlist(revlist, name=sub_name),
                                colspan=str(4 + len(instances))),
                            class_='hidden branch-diff',
                            id="show-" + id_))
                    td(
                        tags.a(ver, href='#', class_='highlight'),
                        class_='version clickable', id=id_)
                else:
                    td(tags.span(ver, class_='highlight'), class_='version')
            elif location:
                try:
                    branch = bzrlib.branch.Branch.open(location)
                except bzrlib.errors.NoSuchBranch:
                    td(tags.span(ver, class_='highlight'), class_='version')
                else:
                    branch.lock_read()
                    try:
                        # This utterly half-assed version of bzr missing
                        # doesn't take merges into account!
                        revno, revid = branch.last_revision_info()
                        ver = ver.split('dev')[0] + 'dev' + str(revno)
                        mainline_revids = dict(
                            (rev.revision_id, revno)
                            for rev, revno in component.mainline_revs)
                        in_branch_revs = []
                        while revid not in mainline_revids:
                            rev = branch.repository.get_revision(revid)
                            if rev.message != 'post release bump':
                                in_branch_revs.append((rev, revno))
                            revno -= 1
                            if not rev.parent_ids:
                                break
                            revid = rev.parent_ids[0]
                        tables = []
                        if in_branch_revs:
                            tables.append(
                                format_revlist(
                                    in_branch_revs,
                                    'in branch (with nick %s) but not tip' % branch.nick))
                        in_trunk_revs = []
                        lca_revno = revno
                        for rev, revno in component.mainline_revs:
                            if revno > lca_revno:
                                in_trunk_revs.append((rev, revno))
                        if in_trunk_revs:
                            tables.append(
                                format_revlist(
                                    in_trunk_revs,
                                    'in tip but not branch'))
                        if tables:
                            id_ = get_id()
                            td(
                                tags.a(ver, href='#', class_='highlight'),
                                class_='version clickable', id=id_)
                            extra_rows.append(
                                tags.tr(
                                    tags.td(
                                        tables,
                                        colspan=str(4 + len(instances))),
                                    class_='hidden branch-diff',
                                    id="show-" + id_))
                        else:
                            if branch.last_revision() == component.tip_revno:
                                td(ver, class_='highlight version')
                            else:
                                td(ver, class_='version')
                    finally:
                        branch.unlock()
            else:
                td(tags.span(ver, class_='highlight'), class_='version')
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
