#! /usr/bin/python3

# Update InterPro data.
# First fetch Interpro and UniProt files.
# Then process then to create files ipr_reviewed_human_match.xml.gz 
# ipr_shortnames-nofam.xml.gz and refs_mapping.xml.gz


import os
import sys
import re
import math
import time
import gzip
import csv
import shutil
import urllib.request # "import requests" does not work for FTP
import lxml.html
from lxml import etree

import ipr_updater as ipru


# Create necessary directories if they do not exist
downldir = 'downloaded_files' # Directory to put downloaded files.
writedir = 'anatomizer_ipr_files' # Directory to write custom files.
ipru.ipr_mkdir(downldir, writedir)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# --------- Fetch files ----------
ipr_version = ipru.online_version()

today = time.strftime("%d%b%Y")

# Interpro
interpro_version = ipru.local_version(downldir,
                                      'interpro-', 'xml.gz')
if interpro_version < ipr_version:
    print('Downloading file 1 of 4: interpro-%i.xml.gz to dir %s.'
          % (ipr_version, downldir) )
    ipru.fetch_interpro(ipr_version, downldir)
    print('')
else:
    print('File 1 of 4, interpro-%i.xml.gz, already in %s.\n'
          % (ipr_version, downldir) )


# Match
match_version = ipru.local_version(downldir,
                                   'match_complete-', 'xml.gz')
if match_version < ipr_version:
    print('Downloading file 2 of 4: match_complete-%i.xml.gz' % ipr_version)
    ipru.fetch_match(ipr_version, downldir)
    print('')
else:
    print('File 2 of 4, match_complete-%i.xml.gz, already downloaded.'
          % ipr_version)
    file_byte = os.path.getsize('%s/match_complete-%i.xml.gz'
                                % (downldir, ipr_version) )
    filesize = ipru.convert_size(file_byte)
    print("This file's size is %s. It should be at least 15 GB.\n"
          % filesize)


# TSV
tsv_version = ipru.local_version(downldir,
                                 'uniprot-hproteome-', 'tsv.gz')
if tsv_version < ipr_version:
    print('Downloading file 3 of 4: uniprot-hproteome-%i-%s.tsv.gz'
          % (ipr_version, today))
    print('This should take about a minute.')
    ipru.fetch_tsv(ipr_version, downldir, today)
    print('')
else:
    print('File 3 of 4, uniprot-hproteome-%i.tsv.gz, already downloaded.\n'
          % ipr_version)


# FASTA
fasta_version = ipru.local_version(downldir,
                                   'uniprot-hproteome-', 'fasta.gz')
if fasta_version < ipr_version:
    print('Downloading file 4 of 4: uniprot-hproteome-%i-%s.fasta.gz'
          % (ipr_version, today))
    print('This should take about a minute.')
    ipru.fetch_fasta(ipr_version, downldir, today)
    print('')
else:
    print('File 4 of 4, uniprot-hproteome-%i.fasta.gz, already downloaded.\n'
          % ipr_version)

# --------------------------------


print(' ---- Finished fetching files. Now writing custom files. ----\n')


# ====== Write custom files ======

# Mapping
mapping_version = ipru.local_version(writedir, 
                                     'refs_mapping-', '.xml.gz')
if mapping_version < ipr_version:
    print('Writing file 1 of 3: refs_mapping-%i.xml.gz'
          % ipr_version)
    ipru.update_mapping(ipr_version, downldir, writedir)
    print('')
else:
    print('File 1 of 3, refs_mapping-%i.xml.gz, already present.\n'
          % ipr_version)

# Short names
shortname_version = ipru.local_version(writedir, 
                                       'ipr_shortnames-', '.xml.gz')
if shortname_version < ipr_version:
    print('Writing file 2 of 3: ipr_shortnames-%i.xml.gz'
          % ipr_version)
    ipru.update_shortname(ipr_version, downldir, writedir)
    print('')
else:
    print('File 2 of 3, ipr_shortnames-%i.xml.gz, already present.\n'
          % ipr_version)

# Matching
matching_version = ipru.local_version(writedir, 
                                      'ipr_reviewed_human_match-', '.xml.gz')
if matching_version < ipr_version:
    print('Writing file 3 of 3: ipr_reviewed_human_match-%i.xml.gz'
          % ipr_version)
    ipru.update_match(ipr_version, downldir, writedir)
    print('')
else:
    print('File 3 of 3, ipr_reviewed_human_match-%i.xml.gz, already present.\n'
          % ipr_version)

# ================================

print('Update of InterPro files to version %i completed.' % ipr_version)

