osm-editorbreakdown
===================

python script to parse editor information out of changesets-latest.osm.bz

running
=======

* download changesets-latest.osm.bz2 from the planet website
* extract the editors to a file using

    bzcat changesets-latest.osm.bz2 | grep -Po '\<tag k=\"created_by\" v=\"\K.*?(?=")' > editors.csv

* open process-editors.py
* change the `infile` and `outdir` variables to appropriate values
* save and exit
* call the script:

    python process-editors.py [-q]

