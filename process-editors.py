import re
import os
import csv

# the editors.csv file is a text file with one entry per line.
# this file can be created from a changesets file using:
# bzcat /osm/planet/changesets/changesets-latest.osm.bz2 | grep -Po '\<tag k=\"created_by\" v=\"\K.*?(?=")' > editors.csv

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

common_editors = ['JOSM', 'Potlatch', 'Potlatch 2', 'Merkaartor', 'Mapzen', 'OpenMaps', 'wheelmap', 'OsmAnd', 'iLOE', 'Vespucci', 'ArcGIS']

infile = '/osm/out/editors.csv'
outdir = '/osm/out/'

editors = open(infile,'r')

lc = 0

for line in editors:
    lc += 1
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

print '-' * 80

csvtotals = csv.writer(open(os.path.join(outdir,'totals.csv'),'wb'))
for editor,versions in r.editors.iteritems():
    csvout = csv.writer(open(os.path.join(outdir,editor+'.csv'),'wb'))
    total = 0
    for k,v in versions.iteritems():
        csvout.writerow((k,v))
        total += int(v)
    csvtotals.writerow((editor,total))

