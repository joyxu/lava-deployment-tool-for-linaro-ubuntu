import sys

from lxml import etree

t = etree.parse(open(sys.argv[1]))

def x(t, e, **kw):
    return t.xpath(e, namespaces={'html': 'http://www.w3.org/1999/xhtml'}, **kw)


def col(t, n):
    return x(t, '//html:table[@class="main"]/html:tbody/html:tr[@class="component"]/html:td[position()=$index]', index=n)


def strip_to_basics(fname):
    t = etree.parse(open(fname))
    instances = x(t, '//html:table[@class="main"]//html:tr/html:th[@class="instance-name"]')

    for instance in reversed(instances):
        index = instance.getparent().index(instance)

        for td in col(t, index+1):
            td.getparent().remove(td)
        instance.getparent().remove(instance)

    for tr in x(t, '//html:table[@class="main"]/html:tbody/html:tr[contains(@class,"branch-diff")]'):
        tr.getparent().remove(tr)
    return t

_id = 0
def get_id():
    global _id
    _id += 1
    return 'id' + str(_id)

def process(base, fname):
    t = etree.parse(open(fname))

    instances = x(t, '//html:table[@class="main"]//html:tr/html:th[@class="instance-name"]')

    for instance in instances:
        index = instance.getparent().index(instance)
        rows = x(base, '//html:table[@class="main"]/html:tbody/html:tr[@class="component"]')
        for td, row in zip(col(t, index+1), rows):
            if 'clickable' in td.get('class'):
                extra_row = x(t, '//*[@id=$id]', id='show-'+td.get('id'))[0]
                id_ = get_id()
                extra_row.set('id', 'show-' + id_)
                td.set('id', id_)
                row_index = row.getparent().index(row)
                row.getparent().insert(row_index + 1, extra_row)
            row.append(td)
        x(base, '//html:table[@class="main"]/html:thead/html:tr')[0].append(instance)


t = strip_to_basics(sys.argv[1])
for fname in sys.argv[1:]:
    process(t, fname)

col_count = len(x(t, '//html:table[@class="main"]/thead/html:tr/html:th'))
for e in x(t, '//html:table[@class="main"]/html:tbody/html:tr[contains(@class, "hidden")]/html:td'):
    e.set('colspan', '12')

print etree.tostring(t)
