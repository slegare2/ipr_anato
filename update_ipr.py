#! /usr/bin/python3

# Update InterPro data.
# First fetch Interpro and UniProt files.
# Then process then to create files ipr_reviewed_human_match.xml.gz 
# ipr_shortnames-nofam.xml.gz and refs_mapping.xml.gz

from ipr_updater import *


# --------- Fetch files ----------
ipr_version = online_version()

today = time.strftime("%d%b%Y")

match_version = local_version('match_complete-', 'xml.gz')
if match_version < ipr_version:
    fetch_match(ipr_version)

interpro_version = local_version('interpro-', 'xml.gz')
if interpro_version < ipr_version:
    fetch_interpro(ipr_version)

tsv_version = local_version('uniprot-hproteome-', 'tsv.gz')
if tsv_version < ipr_version:
    fetch_tsv(ipr_version, today)

fasta_version = local_version('uniprot-hproteome-', 'fasta.gz')
if fasta_version < ipr_version:
    fetch_fasta(ipr_version, today)
# --------------------------------


