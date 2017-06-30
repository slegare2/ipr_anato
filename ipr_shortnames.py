#! /usr/bin/python3

# Extract essential data from InterPro entries and show hierarchy tree.

import re
import gzip
import xml.etree.ElementTree as etree
from anytree import Node, RenderTree

human_only = False
exclude_family = True

# Choose which version of InterPro to use (must have been downloaded first
# using fetch_files.py)
ipr_version = 63
print('Extracting short names from InterPro version %i.' % ipr_version)

# Output files.
if human_only and exclude_family:
    short_out = gzip.open('ipr_shortnames-nofam-human-%i.xml.gz' % ipr_version, 'wt')
if human_only and not exclude_family:
    short_out = gzip.open('ipr_shortnames-human-%i.xml.gz' % ipr_version, 'wt')
if not human_only and exclude_family:
    short_out = gzip.open('ipr_shortnames-nofam-%i.xml.gz' % ipr_version, 'wt')
if not human_only and not exclude_family:
    short_out = gzip.open('ipr_shortnames-%i.xml.gz' % ipr_version, 'wt')

# Input files.
infile = 'downloaded-files/interpro-%i.xml.gz' % ipr_version
interpro_in = gzip.open(infile,'r').read()


# Running options message.
print('Extracting information from file %s.' % infile)
if human_only:
    print('Keeping only features found in "Human".')
if exclude_family:
    print('Excluding entries of type "Family".')
if not human_only and not exclude_family:
    print('Keeping all entries.')


interpro_root = etree.fromstring(interpro_in)

short_out.write('<interprodb>\n')

entries = interpro_root.findall("interpro")
for entry in entries:

    # Find if entry is found in Human.
    in_human = False
    taxons = entry.findall('taxonomy_distribution/taxon_data')
    for taxon in taxons:
        taxon_name = taxon.get('name')
        if taxon_name == 'Human':
            in_human = True
            break

    # Find if entre=y is of type Family.
    feature_type = entry.get('type')


    if not human_only or (human_only and in_human):
        if not exclude_family or (exclude_family and feature_type != 'Family'):

            ipr = entry.get('id')
            shortname = entry.get('short_name')
            feature_type = entry.get('type')
            nameline = entry.find('name')
            name = nameline.text

            parentline = entry.find('parent_list/rel_ref')
            try:
                parent = parentline.get('ipr_ref')
            except:
                parent = None

            # Escape special characters that are sometimes found in InterPro domain names (",&)
            if '"' in name:
                name = re.sub(r'"','&quot;',name)
            if '&' in name:
                name = re.sub(r'&','&amp;',name)

            short_out.write('<interpro id="%s" short_name="%s" name="%s" parent="%s" type="%s"/>\n' 
                            % (ipr, shortname, name, parent, feature_type) )


short_out.write('</interprodb>\n')

