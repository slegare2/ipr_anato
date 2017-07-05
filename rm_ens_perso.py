#! /usr/bin/python3

# Send the latest version of refs_mapping.xml.gz, ipr_shortnames.xml.gz
# and ipr_reviewed_human_match.xml.gz to ENS personnal page using lftp.

import os


ftpdir = 'anatomizer_ipr_files'


# List of files to remove on remote site perso.ens-lyon.fr
rmfile_list = ['refs_mapping-63.xml.gz', 'ipr_shortnames-63.xml.gz', 'ipr_reviewed_human_match-63.xml.gz']


if len(rmfile_list) > 0:

    # Build lftp command line.
    cmd_string = "lftp -u slegare perso.ens-lyon.fr -e 'cd %s;" % ftpdir

    for rmfile in rmfile_list:
        cmd_string = cmd_string + " rm %s;" % rmfile

    cmd_string = cmd_string + " quit'"


    # Run lftp
    os.system(cmd_string)

