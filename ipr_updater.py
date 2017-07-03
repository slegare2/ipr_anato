"""
Set of utils to download and update InterPro information 
for use with the Anatomizer.
"""

import os
import sys
import re
import math
import time
import csv
import shutil
import urllib.request # Cannot use requests for FTP

import lxml.html
from lxml import etree


# 1. Set of functions to fetch files from InterPro and UniProt.
#
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
# ---------------------------------------------------------------------------

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


def convert_size(size_bytes):
   """ 
   Convert file size from bytes to MB, GB, etc.
   taken on Stakoverflow by James Sapam.
   """
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


def local_version(directory, prefix, suffix):
    """ 
    Check the version of local file with given prefix and suffix.
    An example of prefix is 'match_complete' and suffix would be 'xml.gz'.
    """
    match_versions = []
    for dlded_file in os.listdir(directory):
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
        loc_version = sorted_versions[-1]
    else:
        loc_version = 0

    return loc_version


def online_version():
    """ Check last version of InterPro online. """
    ipr_home = urllib.request.urlopen('https://www.ebi.ac.uk/interpro/')
    content = ipr_home.read()
    tree = lxml.etree.HTML(content)
    release = tree.find(".//div[@class='release-box']")
    latest_rel = release.find(".//span[@class='version_title_main']")
    ipr_version = latest_rel.text
    tokens = ipr_version.split()
    onl_version = int(float(tokens[1]))

    return onl_version


def fetch_match(version):
    """ Download match_complete.xml.gz. """
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'match_complete.xml.gz', 
                               'downloaded-files/match_complete-%i.xml.gz'
                               % version, reporthook
    ) 
    print('')


def fetch_interpro(version):
    """ Download interpro.xml.gz. """
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'interpro.xml.gz', 
                               'downloaded-files/interpro-%i.xml.gz' 
                               % version, reporthook
    )
    print('')


def fetch_tsv(version, date):
    """ Download uniprot-hproteome.tsv.gz. """
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
                               % (version, date)
    )
    print('')


def fetch_fasta(version, date):
    """ Download uniprot-hproteome.fasta.gz. """
    print('This should take about a minute.')
    queryline = ('http://www.uniprot.org/uniprot/'
                 '?query=reviewed:yes+AND+organism:9606+AND+proteome:up000005640'
                 '&sort=id&desc=no&format=fasta&include=yes&compress=yes'
    )
    urllib.request.urlretrieve(queryline, 
                               'downloaded-files/'
                               'uniprot-hproteome-%i-%s.fasta.gz' 
                               % (version, date)
    )
    print('')

# ---------------------------------------------------------------------------


# 2. Extract HGNC mapping corresponding to InterPro version.
# ===========================================================================

# 3. Extract InterPro short names and parents.
#
# Short names are used as official name for domains
# and parents are used to merge domains that are banched.
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def update_shortname(version, human_only = False, exclude_family = False):
    """
    Write an xml file that contains the id, short name, name, 
    parent and type of each InterPro entry.
    """
    # Input files.
    infile = 'downloaded-files/interpro-%i.xml.gz' % ipr_version
    interpro_in = gzip.open(infile,'r').read()
    
    # Output files.
    if human_only and exclude_family:
        filename = 'ipr-tmp_shortnames-nofam-human-%i.xml.gz' % version
    if human_only and not exclude_family:
        filename = 'ipr-tmp_shortnames-human-%i.xml.gz' % version
    if not human_only and exclude_family:
        filename = 'ipr-tmp_shortnames-nofam-%i.xml.gz' % version
    if not human_only and not exclude_family:
        filename = 'ipr-tmp_shortnames-%i.xml.gz' % version
    short_out = gzip.open(filename, 'wt')
        
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
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
