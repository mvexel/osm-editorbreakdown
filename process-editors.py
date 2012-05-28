import os
import csv
# on python 2, you need bz2file from PyPi because the native bz2 library does 
# not support multi-stream bz2 files. As of python 3.3a2, multi-stream support
# is available in the native bz2 library
# http://python.readthedocs.org/en/latest/library/bz2.html
import bz2file
import sys
import re
try:
    from lxml.etree import cElementTree as ElementTree
except ImportError:
    import cElementTree as ElementTree

# License
# =======
# Copyright (c) 2012 Martijn van Exel
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Changelog
# 0.1 initial release
#
# configuration
# =============
# locations of the input file and the output files on your filesystem.
# existing output files will be overwritten!
#
# the editors.csv file is a text file with one entry per line.
# this file can be created from a changesets file using:
# bzcat /osm/planet/changesets/changesets-latest.osm.bz2 | grep -Po '\<tag k=\"created_by\" v=\"\K.*?(?=")' > editors.csv
infile = '/osm/planet/changesets/changesets-latest.osm.bz2'
outdir = '/osm/out/'

# list of common editors, for these, a breakdown by version will be output in a separate CSV file, and they will be counted separately in the totals CSV.
common_editors = ['Potlatch', 'Potlatch 2', 'Merkaartor', 'Mapzen', 'OpenMaps', 'wheelmap', 'OsmAnd', 'iLOE', 'Vespucci', 'ArcGIS']

# NO NEED TO CHANGE ANYTHING BEYOND THIS POINT
# ============================================

__version__ = 0.1

class NestedDict(dict):
    def __getitem__(self,key):
        if key in self: 
            return self.get(key)
        return self.setdefault(key, NestedDict())

class Results:
    def __init__(self):
        self.editors = NestedDict()
    def add(self,editor,version, user, empty):
        e = 0
        if empty: e = 1
        if editor in self.editors:
            if version in self.editors[editor]:
                self.editors[editor][version][0] += 1
                self.editors[editor][version][1] += e
                if user not in self.editors[editor][version][2]:
                    self.editors[editor][version][2].append(user)
            else:
                self.editors[editor][version] = [1, e, [user]]
        else:
            self.editors[editor] = {}
cscnt = 0
r = Results()
osmxml = bz2file.BZ2File(infile)
context = ElementTree.iterparse(osmxml, events = ('start','end'))
context = iter(context)
event, root = context.next()
changesetStarted = False
for event, elem in context:
    if elem.tag == 'changeset' and event == 'start':
        changesetStarted = True
        cscnt += 1
        if not cscnt % 10000:
            print '\r' + str(cscnt) + '...',
            sys.stdout.flush()
#        if cscnt == 1000000: break
        user = elem.attrib.get('user')
        editor = ''
        version = 'n/a'
        haseditor = False
        empty = False
        user = elem.attrib.get('user')
        if elem.attrib.get('min_lon'):
            minlon = float(elem.attrib.get('min_lon'))
            minlat = float(elem.attrib.get('min_lat'))
            maxlon = float(elem.attrib.get('max_lon'))
            maxlat = float(elem.attrib.get('max_lat'))
            if maxlon - minlon == 0 and maxlat - minlat == 0: 
                empty = True
        else:
            empty = False
    if elem.tag == 'changeset' and event == 'end':
        changesetStarted = False
        if haseditor: r.add(editor,version,user,empty)
    if changesetStarted:
        if elem.tag == 'tag':
            if elem.attrib.get('k') == 'created_by' and len(elem.attrib.get('v')) > 0:
                haseditor = True
                e = elem.attrib.get('v')
                if e.find('JOSM') > -1:
                    editor = 'JOSM'
                    ro = re.search('\d{4}',e)
                    if ro: version = ro.group(0)
                for k in common_editors:
                    if e.find(k) == 0: 
                        editor = e[:len(k)]
                        version = e[len(k):].strip()
                if editor == '': 
                    editor = 'Other'
                    version = e.encode('utf-8')
    elem.clear()

#print r.editors
csvtotals = csv.writer(open(os.path.join(outdir,'totals.csv'),'wb'))
csvtotals.writerow(('version','changesets','unique users','empty changesets'))
for editor,versions in r.editors.iteritems():
    csvout = csv.writer(open(os.path.join(outdir,editor+'.csv'),'wb'))
    csvout.writerow(('version','changesets','unique users','empty changesets'))
    total = 0
    totalcount = 0
    totalusers = 0
    totalempties = 0
    for k,v in versions.iteritems():
        countforversion = v[0]
        empties = v[1]
        usersforversion = len(v[2])
        csvout.writerow((k, countforversion, usersforversion))
        totalcount += countforversion
        totalempties += empties
        totalusers += usersforversion
    csvtotals.writerow((editor,totalcount, totalusers, totalempties))
print 'Done! %i changesets processed' % (cscnt)
