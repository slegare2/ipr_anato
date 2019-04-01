"""
Set of utils to download and update InterPro information 
for use with the Anatomizer.
"""


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


class IprUpdaterError(Exception):
    """Base class for exception."""


# 0. Initialize by writing output directories if they do not exist.
#............................................................................
def ipr_mkdir(dldir, wrtdir):
    """ 
    Create directory 'dldir,' to put fetched files
    and directory 'wrtdir' to write custom InterPro files.
    """
    os.makedirs(dldir, exist_ok=True)
    os.makedirs(wrtdir, exist_ok=True)
#............................................................................


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


def local_version(directory, prefix, suffix, avoid=None):
    """ 
    Check the version of local file with given prefix and suffix.
    An example of prefix is 'match_complete' and suffix would be 'xml.gz'.
    """
    match_versions = []
    for dlded_file in os.listdir(directory):
        if prefix in dlded_file and suffix in dlded_file:
            if not avoid or (avoid and avoid not in dlded_file):
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


def fetch_match(version, dldir):
    """ Download match_complete.xml.gz. """
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'match_complete.xml.gz', 
                               '%s/match_complete-%i.xml.gz'
                               % (dldir, version), reporthook
    ) 


def fetch_interpro(version, dldir):
    """ Download interpro.xml.gz. """
    urllib.request.urlretrieve('ftp://ftp.ebi.ac.uk/pub/databases/interpro/'
                               'interpro.xml.gz', 
                               '%s/interpro-%i.xml.gz' 
                               % (dldir, version), reporthook
    )


def fetch_tsv(version, dldir, date):
    """ Download uniprot-hproteome.tsv.gz. """
    queryline = ('http://www.uniprot.org/uniprot/'
                 '?query=reviewed:yes+AND+organism:9606+AND+proteome:up000005640'
                 '&sort=id&desc=no&format=tab&compress=yes'
                 '&columns=id,genes(PREFERRED),genes(ALTERNATIVE),database(HGNC),'
                 'comment(ALTERNATIVE%20PRODUCTS)'
    )
    urllib.request.urlretrieve(queryline, 
                               '%s/uniprot-hproteome-%i-%s.tsv.gz'
                               % (dldir, version, date)
    )


def fetch_fasta(version, dldir, date):
    """ Download uniprot-hproteome.fasta.gz. """
    queryline = ('http://www.uniprot.org/uniprot/'
                 '?query=reviewed:yes+AND+organism:9606+AND+proteome:up000005640'
                 '&sort=id&desc=no&format=fasta&include=yes&compress=yes'
    )
    urllib.request.urlretrieve(queryline, 
                               '%s/uniprot-hproteome-%i-%s.fasta.gz' 
                               % (dldir, version, date)
    )

# ---------------------------------------------------------------------------


# 2. Extract HGNC mapping corresponding to InterPro version.
# ===========================================================================
def check_dates(version, dldir):
    """
    Ensure that input fasta and tsv files are dated as expected.
    """
    dates = []
    for infile in os.listdir(dldir):
        if 'uniprot-hproteome-%i' % version in infile:
            dash = infile.rindex('-')
            dot = infile.index('.')
            date = infile[dash+1:dot]
            dates.append(date)
    dates_set = set(dates)
    if len(dates_set) == 1:
        date_ext = list(dates_set)[0]
    elif len(dates_set) > 1:
        raise IprUpdaterError('A unique date is expected for '
                              'uniprot-hproteome-%i fasta and tsv files.'
                              % version)
    return date_ext


def update_mapping(version, dldir, wrtdir):
    """
    Write an xml file that contains the UniProt id, HGNC symbol, HGNC id, 
    HGNC synonyms and isoforms for each reviewed human proteome UniProt entry.
    """
    date = check_dates(version, dldir)

    # Input files.
    tsvfile = gzip.open('%s/uniprot-hproteome-%i-%s.tsv.gz'
                        % (dldir, version, date), 'rt')
    fastafile = gzip.open('%s/uniprot-hproteome-%i-%s.fasta.gz'
                          % (dldir, version, date), 'rt')
    
    # Output file
    outfile = gzip.open('%s/refs-tmp_mapping-%i.xml.gz'
                        % (wrtdir, version), 'wt')

    # Running options message.
    print('Extracting information from %s/' % dldir)
    print('uniprot-hproteome-%i-%s.tsv.gz' % (version, date) )
    print('uniprot-hproteome-%i-%s.fasta.gz' % (version, date) )
    
    # Get the length of each isoform by counting the 
    # number of residues in fasta entry.
    isoform_lengths = {}
    first = True
    for line in fastafile:
        if '>sp' in line:
    
            if not first:
                isoform_lengths[isoform_id] = l
            first = False
    
            pipe = line.index('|')+1
            unpipe = line[pipe:].index('|') + pipe
            isoform_id = line[pipe:unpipe]            
            l = 0
        else:
            l += len(line) - 1
    # For the last entry
    isoform_lengths[isoform_id] = l
    
    outfile.write('<mapping>\n')
    
    reader = csv.reader(tsvfile, delimiter='\t')
    first = True
    for entry in reader:
        if not first: 
            uniprot_ac = entry[0]
            hgnc_symbol = entry[1]
            hgnc_synonyms = entry[2]
            hgnc_id = entry[3][:-1]
            alt_prods = entry[4]
    
            synonyms = hgnc_synonyms.split()
            
            # Process the "ALTERNATIVE PRODUCTS" part of entry.
            isoform_info = alt_prods.split(';')
            isoforms = []
            seq_types = []
            if len(isoform_info) > 1:
                for field in isoform_info:
                    if 'IsoId' in field:
                        equal_sign = field.index('=')
                        # Sometimes, there are other ids for a same isoform.
                        # I just take the first it these cases.
                        try:
                            coma = field.index(',')
                            isoform_id = field[equal_sign+1:coma]
                        except:
                            isoform_id = field[equal_sign+1:]
                        isoforms.append(isoform_id)
                    if 'Sequence' in field:
                        equal_sign = field.index('=')
                        seq_string = field[equal_sign+1:]
                        if seq_string == 'Displayed':
                            seq_types.append('canonical')
                        else:
                            seq_types.append('alternative')
            else: # Assume one single sequence with id UNIPAC-1.
                isoforms.append('%s-1' % uniprot_ac)
                seq_types.append('canonical')
    
            # Get the length of each isoform.
            lengths = []
            for isoform in isoforms:
                try:
                    l = isoform_lengths[isoform]
                except:
                    dash = isoform.index('-')
                    canon = isoform[:dash]
                    l = isoform_lengths[canon]
                lengths.append(l)
    
            # Write to file in xml style.
            outfile.write('<entry uniprot_ac="%s" hgnc_symbol="%s" hgnc_id="%s">\n' 
                          % (uniprot_ac, hgnc_symbol, hgnc_id) )
            for syn in synonyms:
                outfile.write('  <synonym>%s</synonym>\n' % syn)
            for i in range(len(isoforms)):
                outfile.write('  <isoform>\n')
                outfile.write('    <id>%s</id>\n' % isoforms[i])
                outfile.write('    <length>%s</length>\n' % lengths[i])
                outfile.write('    <type>%s</type>\n' % seq_types[i])
                outfile.write('  </isoform>\n')
            outfile.write('</entry>\n')
    
        first = False
    
    outfile.write('</mapping>\n')
    outfile.close()

    # Copy final output file if everything went well.
    shutil.copyfile('%s/refs-tmp_mapping-%i.xml.gz' % (wrtdir, version), 
                    '%s/refs_mapping-%i.xml.gz' % (wrtdir, version) )
    os.remove('%s/refs-tmp_mapping-%i.xml.gz' % (wrtdir, version) )
# ===========================================================================


# 3. Extract InterPro short names and parents.
#
# Short names are used as official name for domains
# and parents are used to merge domains that are banched.
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def update_shortname(version, dldir, wrtdir, 
                     human_only = False, exclude_family = False):
    """
    Write an xml file that contains the id, short name, name, 
    parent and type of each InterPro entry.
    """
    # Input files.
    infile = '%s/interpro-%i.xml.gz' % (dldir, version)
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
    short_out = gzip.open('%s/%s' % (wrtdir, filename), 'wt')
        
    # Running options message.
    print('Extracting information from %s/' % dldir)
    print('interpro-%i.xml.gz' % version)
    if human_only:
        print(' -- Keeping only features found in "Human".')
    if exclude_family:
        print(' -- Excluding entries of type "Family".')
    if not human_only and not exclude_family:
        print(' -- Keeping all entries.')
    
    
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
    short_out.close()

    # Copy final output file if everything went well.
    new_filename = '%s%s' % (filename[:3], filename[7:])
    shutil.copyfile('%s/%s' % (wrtdir, filename), 
                    '%s/%s' % (wrtdir, new_filename))
    os.remove('%s/%s' % (wrtdir, filename))
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# 4. Extract the reviewed human entries from the InterPro file 
# match_complete.xml.gz, which contains the InterPro domains of 
# all UniProt entries.
#
# File match_complete.xml.gz is very large (~15Go compressed) and we do not
# know the number of lines in advance. It presumably contains ~85 millon 
# entries (the number of protein sequences in TrEMBL).
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def update_match(version, dldir, wrtdir):
    """
    Write an xml file that contains the InterPro signatures of each 
    UniProt reviewed human proteome entry.
    """
    date = check_dates(version, dldir)

    # Input files.
    rev_human_proteome = gzip.open('%s/uniprot-hproteome-%i-%s.fasta.gz' 
                                   % (dldir, version, date),'r')
    complete_match_in = gzip.open('%s/match_complete-%i.xml.gz'
                                  % (dldir, version),'r')
    
    # Output files.
    matchrun_out = open('reviewed_human_match_run.out','w')
    proteome_list = open('%s/uniprot-entries-%i-%s.txt' 
                         % (wrtdir, version, date),'w')
    swiss_match_out = gzip.open('%s/ipr_reviewed_human_match-%i-copy.xml.gz'
                                % (wrtdir, version),'wt')
    
    # Running options message.
    print('Extracting information from %s/' % dldir)
    print('match_complete-%i.xml.gz' % version)
    print('uniprot-hproteome-%i-%s.fasta.gz' % (version, date) )
    print(' -- This can take several hours. Need to parse ~5 billion lines.')

    # Extract UniProt ACs from uniprot-human-proteome.fasta.gz.
    # ////////////
    n = 0
    reviewed_protlist = []
    for line in rev_human_proteome:
        stringline = line.decode("utf-8")
        if '>sp' in stringline:
            pipe = stringline.index('|')+1
            unpipe = stringline[pipe:].index('|') + pipe
            uniprot_ac = stringline[pipe:unpipe]
            reviewed_protlist.append(uniprot_ac)
    
    # Sort ACs so that they are in the same order as in match_complete.xml.gz.
    sorted_protlist = sorted(reviewed_protlist)
    
    # Print sorted list of ACs to file.
    for uniprot_ac in sorted_protlist:
            n += 1
            proteome_list.write('%5i %s\n' % (n, uniprot_ac) )
    proteome_list.close()
    print('Searching for %i reviewed entries in match_complete.xml.gz' % n)
    matchrun_out.write('Searching for %i reviewed entries in ' 
                       'match_complete.xml.gz\n' % n )
    # ////////////
    
    
    # Useful variables.
    n = 0
    pos = 0
    sublist_ind = 0
    sublist_size = 4
    writeit = False
    starttime = time.time()
    
    sublist = sorted_protlist[sublist_ind:sublist_ind + sublist_size]
    
    # Element Tree expects xml files to have a single root tag.
    swiss_match_out.write('<interpromatch>\n')
    
    # Loop over file match_complete.xml.gz.
    for line in complete_match_in:
        stringline = line.decode("utf-8") 
    
        # Find UniProt AC in match_complete.xml.gz lines.
        if '<protein id=' in stringline:
            quote = stringline.index('"')+1
            unquote = stringline[quote:].index('"') + quote
            uniprot_ac = stringline[quote:unquote]
    
            # Check if AC is in the UniProt reviewed human genome.
            # If so, start writing entry to output file.
            if uniprot_ac in sublist:
                n += 1
                acfound = 'Found reviewed UniProt Accession %i: %s %s'%(n,uniprot_ac,sublist)
                print(acfound)
                matchrun_out.write('%s\n' % (acfound) )
                writeit = True
    
                # Check if AC was the first element of sublist.
                # Otherwise, that means a reviewed entry is missing or 
                # incorrectly ordered in match_complete.xml.gz.
                ac_index = sublist.index(uniprot_ac)
                if ac_index != 0:
                    print('AC ', end='')
                    matchrun_out.write('AC ')
                    for i in range(ac_index):
                        print('%s' % sublist[i], end='')
                        matchrun_out.write('%s' % sublist[i] )
                    print(' were skipped. %s' % sublist)
                    matchrun_out.write('were skipped. %s\n' % sublist)
                
                # Update sublist.
                sublist_ind += 1 + ac_index
                sublist = sorted_protlist[sublist_ind:sublist_ind + sublist_size]
    
        if writeit:
            swiss_match_out.write('%s' %(stringline) )
    
        # Entry stops with the line containing string '</protein>'.
        if '</protein>' in stringline:
            writeit = False
    
        # Print progress.
        pos += 1
        if pos%10000000 == 0:
            t = time.time() - starttime
            progress = ('%iM lines parsed in %is, %i AC found. '
                        'Searching for %s' 
                        % (pos/1000000, t, n, ' '.join(sublist) )
            )
            print(progress)
            matchrun_out.write('%s\n' %(progress) )
    
    swiss_match_out.write('</interpromatch>\n')
    swiss_match_out.close()

    # Make a copy of the generated file, since it took so long.
    shutil.copyfile('%s/ipr_reviewed_human_match-%i-copy.xml.gz' % (wrtdir, version), 
                    '%s/ipr_reviewed_human_match-%i.xml.gz' % (wrtdir, version) )
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# 5. Extract canonical entries only from previously made file 
# ipr_reviewed_human_match.xml.gz.
#
# Canonical entries in file ipr_reviewed_human_match.xml.gz are simply the
# ones with no dash (-).
# ***************************************************************************

def extract_canon(version, wrtdir):
    """
    Write an xml file that contains the InterPro signatures of each 
    canonical UniProt reviewed human proteome entry.
    """
    # Input file.
    rev_human_match_in =  gzip.open('%s/ipr_reviewed_human_match-%i.xml.gz'
        % (wrtdir, version),'r')
    
    # Output file.
    canon_human_match_out =  gzip.open('%s/ipr_canonical_human_match-%i.xml.gz'
        % (wrtdir, version),'wt')

    # Running options message.
    print('Extracting information from %s/' % wrtdir)
    print('ipr_reviewed_human_match-%i.xml.gz' % version)

    writeit = False

    # Element Tree expects xml files to have a single root tag.
    canon_human_match_out.write('<interpromatch>\n')
    
    # Loop over file ipr_reviewed_human_match.xml.gz.
    for line in rev_human_match_in:
        stringline = line.decode("utf-8")
  
        # Find canonical UniProt AC in ipr_reviewed_human_match.xml.gz lines.
        if '<protein id=' in stringline:
            tokens = stringline.split()
            # If there is no dash, it means that entry is canonical,
            # write it to output file.
            if '-' not in tokens[1]:
                writeit = True

        if writeit:
            canon_human_match_out.write('%s' %(stringline) )

        # Entry stops with the line containing string '</protein>'.
        if '</protein>' in stringline:
            writeit = False

    canon_human_match_out.write('</interpromatch>\n')
    canon_human_match_out.close()
# ***************************************************************************
