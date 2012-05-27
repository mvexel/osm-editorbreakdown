import re
import os
import sys
import csv
from progress_bar import ProgressBar

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
infile = '/osm/out/editors.csv'
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
    def add(self,editor,version):
        if editor in self.editors:
            if version in self.editors[editor]:
                self.editors[editor][version] += 1
            else:
                self.editors[editor][version] = 1
        else:
            self.editors[editor] = {}

r = Results()
editors = open(infile,'r')
lc = 0
lines = int(os.popen('wc -l %s' % (infile)).read().split(' ')[0])
pb = ProgressBar(lines)

for line in editors:
    lc += 1
    if not '-q' in sys.argv and not lc % 10000:
        pb.update_time(lines - (lines - lc))
        print "{0}\r".format(pb),
#    if not lc % 10000 : continue
#    if lc == 10000: break
    if 'JOSM' in line:
        ro = re.search('\d{4}', line)
        if ro:
            version = ro.group(0)
        else:
            version = None
        r.add('JOSM',version)
        continue
    for k in common_editors:
        if line.find(k) == 0:
            r.add(line[:len(k)],line[len(k):].strip())
            break
    else:
        r.add('Others',line.strip())

print 'done.'

csvtotals = csv.writer(open(os.path.join(outdir,'totals.csv'),'wb'))
for editor,versions in r.editors.iteritems():
    csvout = csv.writer(open(os.path.join(outdir,editor+'.csv'),'wb'))
    total = 0
    for k,v in versions.iteritems():
        csvout.writerow((k,v))
        total += int(v)
    csvtotals.writerow((editor,total))