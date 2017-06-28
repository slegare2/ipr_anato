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


def reporthook(blocknum, blocksize, totalsize):
    """
    Function to show download progression. 
    Found on stackoverflow from J.F. Sebastian.
    """
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

def check_version(prefix, suffix):
    """ 
    Check the version of file with given prefix and suffix.
    An example of prefix is 'match_complete' and suffix
    would be 'xml.gz'.
    """
    match_versions = []
    for dlded_file in os.listdir('downloaded-files'):
        if prefix in dlded_file and suffix in dlded_file:
            # Find version as first series of int characters.
            start = 0
            for i in range(len(dlded_file)):
                try:
                    x = int(dlded_file[i])
                    start = i-1
                except:
                    pass

                if start > 0:
                    try:
                        x = int(dlded_file[i])
                    except:
                        end = i
                        break

            version = int(dlded_file[start:end])
            match_versions.append(version)
    if len(match_versions) > 0:
        sorted_versions = sorted(match_versions)
        version = sorted_versions[-1]
    else:
        version = 0

    return version


# Check last version of InterPro online.
ipr_home = urllib.request.urlopen('https://www.ebi.ac.uk/interpro/')
content = ipr_home.read()
tree = lxml.etree.HTML(content)
release = tree.find(".//div[@class='release-box']")
latest_rel = release.find(".//span[@class='version_title_main']")
ipr_version = latest_rel.text
tokens = ipr_version.split()
last_version = int(float(tokens[1]))

today = time.strftime("%d%b%Y")


# Download match_complete.xml.gz if needed.
prev_version = check_version('match_complete-', 'xml.gz')
if last_version > prev_version:
    print('Downloading file match_complete-%i.xml.gz' % last_version)
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'match_complete.xml.gz', 
                               'downloaded-files/match_complete-%i.xml.gz'
                               % last_version, reporthook
    ) 

# Download interpro.xml.gz if needed.
prev_version = check_version('interpro-', 'xml.gz')
if last_version > prev_version:
    print('Downloading file interpro-%i.xml.gz' % last_version)
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'interpro.xml.gz', 
                               'downloaded-files/interpro-%i.xml.gz' 
                               % last_version, reporthook
    )

# Download uniprot-hproteome.tsv.gz if needed.
prev_version = check_version('uniprot-hproteome-', 'tsv.gz')
if last_version > prev_version:
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

# Download uniprot-hproteome.fasta.gz if needed.
prev_version = check_version('uniprot-hproteome-', 'fasta.gz')
if last_version > prev_version:
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

