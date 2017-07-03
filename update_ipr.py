#! /usr/bin/python3

# Update InterPro data.
# First fetch Interpro and UniProt files.
# Then process then to create files ipr_reviewed_human_match.xml.gz 
# ipr_shortnames-nofam.xml.gz and refs_mapping.xml.gz

from ipr_updater import *


# --------- Fetch files ----------
ipr_version = online_version()

today = time.strftime("%d%b%Y")

# Interpro
interpro_version = local_version('downloaded-files',
                                 'interpro-', 'xml.gz')
if interpro_version < ipr_version:
    print('Downloading file 1 of 4: interpro-%i.xml.gz'
          % ipr_version)
    fetch_interpro(ipr_version)
else:
    print('File 1 of 4, interpro-%i.xml.gz, already downloaded.\n' % ipr_version)


# Match
match_version = local_version('downloaded-files',
                              'match_complete-', 'xml.gz')
if match_version < ipr_version:
    print('Downloading file 2 of 4: match_complete-%i.xml.gz' % ipr_version)
    fetch_match(ipr_version)
else:
    print('File 2 of 4, match_complete-%i.xml.gz, already downloaded.' % ipr_version)
    file_byte = os.path.getsize('downloaded-files/match_complete-%i.xml.gz' % ipr_version)
    filesize = convert_size(file_byte)
    print("This file's size is %s. It should be at least 15 GB.\n" % filesize)


# TSV
tsv_version = local_version('downloaded-files',
                            'uniprot-hproteome-', 'tsv.gz')
if tsv_version < ipr_version:
    print('Downloading file 3 of 4: uniprot-hproteome-%i-%s.tsv.gz' % (ipr_version, today))
    fetch_tsv(ipr_version, today)
else:
    print('File 3 of 4, uniprot-hproteome-%i.tsv.gz, already downloaded.\n' % ipr_version)


# FASTA
fasta_version = local_version('downloaded-files',
                              'uniprot-hproteome-', 'fasta.gz')
if fasta_version < ipr_version:
    print('Downloading file 4 of 4: uniprot-hproteome-%i-%s.fasta.gz' % (ipr_version, today))
    fetch_fasta(ipr_version, today)
else:
    print('File 4 of 4, uniprot-hproteome-%i.fasta.gz, already downloaded.\n' % ipr_version)

# --------------------------------

print(' ---- Finished fetching files. Now writing custom files. ----\n')

# ====== Write custom files ======

# Mapping
mapping_version = local_version('./', 'refs_mapping-', '.xml.gz')
if mapping_version < ipr_version:
    #update_mapping(ipr_version)

# Short names
shortname_version = local_version('./', 'ipr_shortnames-', '.xml.gz')
if shortname_version < ipr_version:
    #update_shortname(ipr_version

# Matching
matching_version = local_version('./', 'ipr_reviewed_human_match-', '.xml.gz')
if matching_version < ipr_version:
    #update_match(ipr_version)


# ================================

print('Update of InterPro files to version %i completed.' % ipr_version)
