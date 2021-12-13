# Artifact File Creation & Tracking

This repository contains scripts to enable the automatic creation of artifact files, given a set of measurements from a cmm. The script reads csv files from a directory, and determines average values to write a valid artifact file. This artifact xml file is then stored in the repository for correct versioning, and to maintain a database of files from which the HP3DScanStudio software can load valid measurement files. The files here can be updated as needed, and changes can be pulled into new software builds. 

Users must have a valid python 3 installation to run this tool. Email marco.pantoja1@hp.com with any questions.
