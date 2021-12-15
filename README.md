# Artifact File Creation & Tracking

This repository contains scripts to enable the automatic creation of artifact files, given a set of measurements from a cmm. The script reads csv files from a directory, and determines average values to write a valid artifact file. This artifact xml file is then stored in the repository for correct versioning, and to maintain a database of files from which the HP3DScanStudio software can load valid measurement files. The files here can be updated as needed, and changes can be pulled into new software builds. 


Requirements:
--numpy (pip install numpy) if you don't have it already
Users must have a valid python 3 installation to run this tool. Email marco.pantoja1@hp.com with any questions.

Creating Artifact Files:
1. Users should copy data into cmm-csv-files

2. The folder names will be used to name the artifacts, so name them accordingly

3. The named artifact folder should contain the last cmmx files from cmm inspections, and a folder called "Reports"

4. The reports folder contained in the artifact folder should have all of the cmm output csv files with relevent sphere measurements.

5. Run the make_artifacts.bat and see the newly minted files under the 'Artifact-XML' directory.

The data from all csv files will be extracted and summarized in a *_summary.csv file, where users can view all of the data going into the artifact file.
Then the script will average the values to reduce the data to a form that can be exported in a *.artifact file