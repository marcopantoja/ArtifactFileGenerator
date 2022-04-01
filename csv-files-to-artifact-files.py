from csv import DictWriter
from datetime import datetime as dt
from math import sqrt
from os import getcwd, listdir, makedirs, walk
from os.path import basename, isdir, join
from statistics import mean, stdev
from sys import argv
from xml.etree import ElementTree as ET

from genericpath import isfile

# check args
if len(argv)>0:
    if '--help' in argv:
        print('''
        This script is meant for finding csv file(s) contained in a folder
        with cmmx file(s). The measurements are averaged across runs to 
        make one artifact file per directory. The artifact will be given a name
        that matches the directory name where data is stored.
        
        Output:
        The artifact files will be stored in the cmmx folder for each artifact,
        unless a common folder is specified at runtime. 
        
        Options:
        
        --folder    narrow search for files by providing a path to
                    a folder
        --output    path to directory where all artifact files should 
                    be saved to.''')
    if '--folder' in argv:
        cwd = argv[argv.index('--folder')+1]
        if not isdir(cwd):raise Exception('invalid folder argument!')
    else:
        cwd = getcwd()
    if '--output' in argv:
        outputDir = argv[argv.index('--output')+1]
    else:
        outputDir = 'Artifact-XML'

def flatten_cmm_csv(filepath:str):
    flat = {'file':filepath}
    with open(filepath, 'r') as csvfile:
        data = [r.strip('ï»¿\n').replace('Â','').split(',') for r in csvfile]
    after_notes = False
    for item in data:
        if item[0] == 'Notes':
            after_notes = True
            continue
        if not after_notes and item[1] != '' and item[0] not in flat: 
            if item[0]=='Temperature':
                flat[f'{item[0]}_{item[1][-2:]}'] = item[1][:-2]
            else:
                flat[item[0]] = item[1]
        elif after_notes:
            m_type = item[2].replace(' ','').lower()
            measures = {'nominal':3,'actual':6,'error':9}
            for val_type in measures:
                if 'positioncartesian' in m_type or 'trueposition' in m_type:
                    for id,direc in enumerate(['x','y','z']):
                        flat[f'{item[1]}_{val_type}_{direc}'] = item[measures[val_type]+id]
                elif 'diameter' in m_type:
                    flat[f'{m_type}_{item[1]}_{val_type}'] = item[measures[val_type]]
                elif 'pointpointdistance' in m_type:
                    flat[f'{m_type}_{item[1]}_{val_type}'] = item[measures[val_type]]
    return flat

def output_compiled_csv(data:list,filepath:str):
    fields = {}
    for d in data:
        for i in d:
            try: fields[i] += 1
            except KeyError: fields[i] = 1
    with open(filepath,'w',newline='') as csvout:
        writer = DictWriter(csvout,data[0],extrasaction='raise')
        writer.writeheader()
        writer.writerows(data)
    return True

def average_data(data:list):
    averages = {}
    for data in all_data:
        for d in data:
            if d.lower().startswith('pos ') and 'actual' in d:
                label = f'{d[4:6]}_{d[-1]}'
                try: averages[label].append(float(data[d]))
                except KeyError: averages[label] = [float(data[d])]
            elif d.startswith('diameter') and 'actual' in d:
                label = 'S'+d.split('_')[1][1:]
                try: averages[label].append(float(data[d]))
                except KeyError: averages[label] = [float(data[d])]
            elif d.startswith('pointpointdistance') and 'actual' in d:
                label = d.split('_')[1]
                try: averages[f'{label[0:2]}-{label[-1]}'].append(float(data[d]))
                except KeyError: averages[f'{label[0:2]}-{label[-1]}'] = [float(data[d])]
            elif 'temperature' in d.lower():
                try: averages[d[:-3]+'degC'].append(float(data[d]))
                except KeyError: averages[d[:-3]+'degC'] = [float(data[d])]
    for a in averages:
        if a.startswith('L') and '-' in a:
            A_B = a[1:].split('-'); A = 'S'+A_B[0]+'_'; B = 'S'+A_B[-1]+'_'
            if A+'x' in averages and B+'x' in averages:
                for idx,_ in enumerate(averages[a]):
                    averages[a][idx] = sqrt(sum([(averages[A+'x'][idx]-averages[B+'x'][idx])**2,(averages[A+'y'][idx]-averages[B+'y'][idx])**2,(averages[A+'z'][idx]-averages[B+'z'][idx])**2]))
    return {a:(mean(averages[a]),stdev(averages[a]),len(averages[a])) for a in averages if len(averages[a])}

def ordered_dist_measures_from(avg:dict,keystrt='L',sep='-'):
    """
    takes list of average values and returns only lengths ordered by spheres.
    """
    lengths = {l:avg[l] for l in avg if l.startswith(keystrt) and sep in l}
    ordered = {}
    while len(lengths):
        A_B = [(int(l[1:].split('-')[0]),int(l[1:].split('-')[-1])) for l in lengths]
        Amin = min([a[0] for a in A_B])
        bsort = sorted([b[-1] for b in A_B if b[0]==Amin])
        for i in bsort:
            ordered[f'{keystrt}{Amin}{sep}{i}'] = lengths[f'{keystrt}{Amin}{sep}{i}']
            lengths.pop(f'{keystrt}{Amin}{sep}{i}')
    return ordered

for r,d,f in walk(cwd):
    d = [i.lower() for i in d]
    cmmx = [i.lower() for i in f if i.endswith('.cmmx')]
    if 'reports' in d and len(cmmx):
        artifact = basename(r).split('_')
        reports = join(r,'reports')
        csvs = [join(reports,f) for f in listdir(reports) if f.endswith('.csv')]
        artifact_summary = join(reports,'_'.join(artifact)+'_summary.csv')
        if not len(csvs): continue# no csv files found
        elif isfile(artifact_summary): continue
        print('Compiling: ',r)
        all_data = []
        for csv in csvs:
            all_data.append(flatten_cmm_csv(csv))
        output_compiled_csv(all_data, artifact_summary)
        # all_data averaged
        averages = average_data(all_data)
        # make artifact file
        artifact_name = artifact[0]+f'_SDME-Avg.artifact'
        if outputDir is not None and isdir(outputDir):
            artifact_path = join(outputDir,artifact_name)
        elif outputDir is not None:
            try:
                makedirs(outputDir)
                artifact_path = join(outputDir,artifact_name)
            except:pass
        else:
            artifact_path = join(r,artifact_name)
        chg_log = ''
        if isfile(artifact_path):
            try:
                chg_log = ET.parse(artifact_path).getroot().find('changelog')
                chg_log[-1].tail = '\n'+'\t'*2
                rev_num = max([int(r.attrib['value']) for r in chg_log.findall('revision')])+1
                if len(artifact)>1:
                    description = ', '.join(artifact[1:])
                else:
                    description = 'Re-measured, descriptors N/A'
                ET.SubElement(chg_log, 'revision', {
                    'value':str(rev_num),
                    'date':dt.now().strftime("%Y-%m-%d"),
                    'description':description
                }).tail='\n\t'
                chg_log = ET.tostring(chg_log).decode()[:-2]
            except:pass
        else:
            rev_num = 0
        if chg_log =='': chg_log = '<changelog>\n\t\t'+\
            f'<revision value="0" date="{dt.now().strftime("%Y-%m-%d")}" '+\
            f'description="Initial python generated file, from {len(csvs)} csv cmm measurement files." />\n\t</changelog>'
        spheres = sorted([int(s[1:]) for s in averages if '_' not in s and '-' not in s and s[1:].isnumeric()])
        try:
            inspector = all_data[0]['Inspector']
        except:
            inspector = ''
        with open(artifact_path,'w') as artifactFile:
            sphere_info = ''
            for i in spheres:
                sphere_info+=f'''\n\t\t<sphere name="S{i}" x="{averages[f"S{i}_x"][0]:.4f}" y="{averages[f"S{i}_y"][0]:.4f}" z="{averages[f"S{i}_z"][0]:.4f}" diameter="{averages[f"S{i}"][0]:.4f}" count="{averages[f"S{i}"][2]}" stdev_mm="{averages[f"S{i}"][1]:.6f}" CTE_m_m_K="8.6E-06"/>'''
            distance_info = ''
            for dist in ordered_dist_measures_from(averages):
                distance_info+=f'''\n\t\t<sphereCenterDistance name="{dist}" sphereA="S{dist[1]}" sphereB="S{dist[-1]}" distance="{averages[dist][0]:.4f}" count="{averages[dist][2]}" stdev_mm="{averages[dist][1]:.6f}" CTE_m_m_K="1.2E-06"/>'''
            contents = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'+\
                f'<artifact type="{artifact[0]}" name="{artifact[0]} SDME Avg" date="{dt.now().strftime("%Y-%m-%d")}" revision="{rev_num}">'+\
                    '\n\t'+chg_log+\
                    '\n\t<alignmentGuide icr="None" rotX="0" rotY="0" rotZ="0" angleTolerance="60" />'+\
                    '\n\t<scanGuide dynamicRange="DRP2" />\n\t<pointFilter maxNormalAngleError="20" outlierRemoval="0.3" />'+\
                    f'\n\t<metrologyInfo date="{all_data[0]["Inspection Time"][:4]}-{all_data[0]["Inspection Time"][4:6]}'+\
                        f'-{all_data[0]["Inspection Time"][6:8]}" lab="SDME" tool="Axiom" metrologist="{inspector}" '+\
                        f'temperatureDegC="{averages["TemperaturedegC"][0]:.1f}" comment="31 touch pts, 10 deg below equator; Average of '+\
                        f'South and East Orientations; n={averages["TemperaturedegC"][-1]} (2 orientations x 6 reps/orientation x 3 sessions); '+\
                        'Ball Plate coord system defined by Datum A: best fit plane through spheres, Datum B: line through sphere centers 1 '+\
                        'and 2 projected onto Datum A, Origin at S0. Ball Plate placed directly on CMM table. Assumed Titanium Ti-6Al-4V spheres."/>'+\
                    f'\n\t<spheres>{sphere_info}\n\t</spheres>'+\
                    f'\n\t<distanceMeasures>{distance_info}\n\t</distanceMeasures>\n</artifact>'
            artifactFile.write(contents)
