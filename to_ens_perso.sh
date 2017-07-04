#! /bin/bash

# Send the latest version of refs_mapping.xml.gz, ipr_shortnames.xml.gz
# and ipr_reviewed_human_match.xml.gz to ENS personnal page.

# Find latest version of InterPro files in directory "anatomizer_ipr_files".


lftp -u slegare perso.ens-lyon.fr \
     -e "cd anatomizer_ipr_files; \
         put anatomizer_ipr_files/refs_mapping-63.xml.gz; \
	 put anatomizer_ipr_files/ipr_shortnames-63.xml.gz; \
	 put anatomizer_ipr_files/ipr_reviewed_human_match-63.xml.gz; \
         quit"

