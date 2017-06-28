#! /usr/bin/python3

# Files to fetch if InterPro file is found to have a new version:
#   match_complete.xml.gz
#   interpro.xml.gz
#   uniprot-hproteome.tsv.gz
#   uniprot-hproteome.fasta.gz
#
# I get uniprot-hproteome.tsv.gz and uniprot-hproteome.fasta.gz
# sorted from A to Z to ease subsequent extraction of reviewed 
# human proteins with script ipr_reviewed_human_match.py
#
# The fasta file is actually only necessary to get the length 
# of the isoforms, which I was not able to retrieve otherwise.
# But in the end I also use the fasta file to get the ordered
# list of UniProt entries with isoforms.

import os
import sys
import re
import time
import urllib.request # Cannot use requests for FTP

import lxml.html
from lxml import etree

# Function to show download progression. 
# Found on stackoverflow from J.F. Sebastian.
def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


# Check what is the previous version of InterPro that was downloaded.
match_versions = []
for dlded_file in os.listdir('downloaded-files'):
    if 'match_complete' in dlded_file:
        dash = dlded_file.index('-')
        dot = dlded_file.index('.')
        version = int(dlded_file[dash+1:dot])
        match_versions.append(version)
if len(match_versions) > 0:
    sorted_versions = sorted(match_versions)
    prev_version = sorted_versions[-1]
else:
    prev_version = 0
    

# Check last version of InterPro online.
ipr_home = urllib.request.urlopen('https://www.ebi.ac.uk/interpro/')
content = ipr_home.read()
tree = lxml.etree.HTML(content)
release = tree.find(".//div[@class='release-box']")
latest_rel = release.find(".//span[@class='version_title_main']")
ipr_version = latest_rel.text
tokens = ipr_version.split()
last_version = int(float(tokens[1]))


# Check if the InterPro data must be updated.
if last_version > prev_version:
    download_needed = True
    today = time.strftime("%d%b%Y")
else:
    download_needed = False


# Download files if necessary.
if download_needed:
    # Download match_complete.xml.gz
    print('Downloading file match_complete-%i.xml.gz' % last_version)
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'match_complete.xml.gz', 
                               'downloaded-files/match_complete-%i.xml.gz'
                               % last_version, reporthook
    )    
    # Download interpro.xml.gz
    print('Downloading file interpro-%i.xml.gz' % last_version)
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'interpro.xml.gz', 
                               'downloaded-files/interpro-%i.xml.gz' 
                               % last_version, reporthook
    )
     Download uniprot-hproteome.tsv.gz
    print('Downloading file uniprot-hproteome-%i-%s.tsv.gz' % (last_version, today))
    print('This should take about a minute.')
    queryline = ('http://www.uniprot.org/uniprot/'
                 '?query=reviewed:yes+AND+organism:9606+AND+proteome:up000005640'
                 '&sort=id&desc=no&format=tab&compress=yes'
                 '&columns=id,genes(PREFERRED),genes(ALTERNATIVE),database(HGNC),'
                 'comment(ALTERNATIVE%20PRODUCTS)'
    )
    urllib.request.urlretrieve(queryline, 
                               'downloaded-files/'
                               'uniprot-hproteome-%i-%s.tsv.gz' 
                               % (last_version, today)
    )
    # Download uniprot-hproteome.fasta.gz
    print('Downloading file uniprot-hproteome-%i-%s.fasta.gz' % (last_version, today))
    print('This should take about a minute.')
    queryline = ('http://www.uniprot.org/uniprot/'
                 '?query=reviewed:yes+AND+organism:9606+AND+proteome:up000005640'
                 '&sort=id&desc=no&format=fasta&include=yes&compress=yes'
    )
    urllib.request.urlretrieve(queryline, 
                               'downloaded-files/'
                               'uniprot-hproteome-%i-%s.fasta.gz' 
                               % (last_version, today)
    )

