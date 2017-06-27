#! /usr/bin/python3

# Files to fetch if InterPro file is found to have a new version:
#   match_complete.xml.gz
#   interpro.xml.gz
#   uniprot-human-proteome.fasta.gz
#   hgncsymbol-uniprot.list

import sys
import urllib.request


# Nice function to show download progression. 
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
prev_version = 63

# Check last version of InterPro online.
last_version = 64

## Download match_complete.xml.gz
#print('Downloading')
#urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
#                           'match_complete.xml.gz', 
#                           'downloaded-files/match_complete-%i.xml.gz'
#                           % last_version, reporthook
#)
#
# Download interpro.xml.gz
urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                           'interpro.xml.gz', 
                           'downloaded-files/interpro-%i.xml.gz' 
                           % last_version, reporthook
)




