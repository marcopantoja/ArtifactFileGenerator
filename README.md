# Artifact File Creation & Tracking

This repository contains scripts to enable the automatic creation of artifact files, given a set of measurements from a cmm. The script reads csv files from a directory, and determines average values to write a valid artifact file. This artifact xml file is then stored in the repository for correct versioning, and to maintain a database of files from which the HP3DScanStudio software can load valid measurement files. The files here can be updated as needed, and changes can be pulled into new software builds. 


# Requirements:
Users must have a valid python 3 installation to run this tool. Email marco.pantoja1@hp.com with any questions.

Creating Artifact Files:
1. Users should copy data into cmm-csv-files or point script to base data directory using the command line arguments

2. The folder names that contain "reports" & cmmx files will be used to name the artifacts, so name them accordingly

3. The named artifact folder should contain the last cmmx files from cmm inspections, and a folder called "Reports"

4. The reports folder contained in the artifact folder should have all of the cmm output csv files with relevent sphere measurements.

5. Run the make_artifacts.bat and see the newly minted files under the 'Artifact-XML' directory.

# Additional Notes:

1. The data from all csv files will be extracted and summarized in a {artifactFolderName}_summary.csv file, where users can view all of the data that is averaged into the artifact file.

2. Then the script will average the values to reduce the data to a form that can be exported in a {artifactFolderName}.artifact file

3. If a file for an artifact has been generated previously, the file will be updated with a new revision, and the changelog will 
have a new revision listed. The description is taken from the artifactFolderName. This name can be descriptive and underscore separated.
The first part should always be P### and anything following will be parsed for description strings. 

Otherwise, if it's the first time generating an artifact file, the changelogs will be identical besides the dates. 
You should create new P### folders each time new measurements are run, unless you want to combine the values with a previous
set of csv files. In that case, delete the summary.csv that was created, and add additional data csv files to this reports folder. 
Then, when you re-run the batch file you will see the artifact files updated. 