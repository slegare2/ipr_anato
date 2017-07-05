# ipr_updater

The ipr_updater updates custom files built from the InterPro protein domain database
for use with the Anatomizer project.

It contains 4 files: ipr_updater.py, update_ipr.py, to_ens_perso.py and rm_ens_perso.py.


Module ipr_updater.py contains the functions required to fetch InterPro files and 
extract the desired information to custom files.

Script update_ipr.py runs the functions of ipr_updater.py in the proper order and output
various messages about update progress. It takes about 2 hours to complete and should be 
run at every new InterPro update (once every 2 months).

Script to_ens_perso.py sends the custom InterPro files online to be available for users 
of the Anatomizer. The files are sent to http://perso.ens-lyon.fr/sebastien.legare/anatomizer_ipr_files/
using lftp (password required).

Script rm_ens_perso.py removes given files from the perso.ens-lyon.fr page (password required)
in case something went wrong and thing must be cleaned.

