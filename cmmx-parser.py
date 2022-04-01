from csv import DictWriter
from os import getcwd, listdir, walk
from os.path import join
from time import time
from datetime import datetime as dt
from xml.etree import ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed

def flatten_element(element:ET.Element,flat:dict,prefix:str='',num:int=0):
    """
    generic call continues recursively adding data to dictionary,
    while element has data that we care about.
    Parameters:
    element     --The element that we want to extract data from
    flat        --The dictionary for storing data for this file
    prefix      --The leading str that is combined with element tag to form key
    num         --A number that is incremented to ensure unique keys in some cases
    """
    def enumerate_this(tag_name:str)->bool:
        if tag_name in [
            'Step','TeachPoint','WorkpieceType',
            'Feature','Workpiece','FeatureData',
            'DataPoint','CoOrdinate',
            'Ends','Dimension','TypeAndWorkpiece',
            'SPCBatch','SPCRun','SPCValue'
        ]:
            return True
        return False

    stuff_i_dont_care_about = [
        'FilePassword','DimensionData','FeatureNotes','Mk3Import','CompatibilityLevel','CameraView','ApplicationExtensionData','RecoveryVector',
        'DisplayLayers','UserShifts','LeapFrog','ClickIndex','MovePlaneNormal','MoveDetails','ContactNumber','Purpose',
        'RefDirectionDefined','RefPositionDefined','OverTravel','Penetration','Plunge','PlungeLocked','Rise','RiseLocked','PreTravel',
        'MaxContactAngle','UserRequestsAClosedScan','ArcMovesUsed','Constructed','Notes','RunThisFeature','ClickPositionConstructionSelection',
        'PenatrateRelativeToPlaneCircleAndLineUnits','OriginalPenetrationCompensationPlane','UserEnteredValue','UserEnteredValueAngle',
        'ConePointsGoingTo','DisplayLineStyle','MoveListState','IgnoreUnmatchedCurvePoints','PlotPointViewDetails','TemplateLocked',
        'TransformIndex','TemplateNumPoints','Projection','ProjectionFeature','ExtentionFeature1','ExtentionFeature2','DisplayLayer','BoreBossSign',
        'ConstructionChoice','ConstructionType','ConstructionType2','ConstructionSwaped','Selected','Parameters','HeaderView','OutputOptions',
        'FeatureAndPointsOnIt','boolean','ClickableDimensionLines','ClickableTextArea','FeatureNumber','CuttingTool']
    tag = element.tag
    text = element.text
    if text is not None: text=text.rstrip()
    if tag in stuff_i_dont_care_about: return None
    if tag == 'Step':
        if element.attrib['Purpose']!='TakePoint': return None
    if enumerate_this(tag): 
        prefix += f'_{tag}{num}'
    elif prefix is not '': 
        prefix += '_'+tag
    else:
        prefix = tag
    if len(element.attrib):
        for a in element.attrib:
            key = f'{prefix}_{a}'
            if key in flat: raise# ensures we don't overwrite anything on accident
            if 'type' in key and '://www.' in key: key = '_'.join([k for k in key.split('_') if '://www.' not in k])+'_Type'
            flat[key] = element.attrib[a]
    if text != None and text != '':
        key = prefix
        if key in flat: raise# ensures we don't overwrite anything on accident
        if 'type' in key and '://www.' in key: key = '_'.join([k for k in key.split('_') if '://www.' not in k])+'_Type'
        flat[key] = text
    if len(list(element)):
        for idx,e in enumerate(element):
            flatten_element(e,flat,prefix,idx)

def flatten_cmmx_file(path:str)->dict:
    """
    takes path to cmmx file and returns a dictionary with all pruned data.
    """
    cmmx_xml = ET.parse(path).getroot()
    flat = {'filepath':path}
    for item in cmmx_xml:
        flatten_element(item, flat)
    return flat

if __name__=="__main__":
    all_runs = []
    cwd = getcwd()
    start=time()
    with ProcessPoolExecutor(9) as pool:
        for r,d,f in walk(cwd):
            cmmxfiles = [join(r,f) for f in listdir(r) if f.endswith('.cmmx')]
            futs = [pool.submit(flatten_cmmx_file, cmmxpath) for cmmxpath in cmmxfiles]
            for fut in as_completed(futs):
                res = None
                try:
                    res = fut.result()
                except: pass
                if res is not None:
                    all_runs.append(res)
    print(f'elapsed: {time()-start:.2f} sec')
    headings = {}
    for r in all_runs:
        for h in r:
            try:
                headings[h]+=1
            except KeyError:
                headings[h]=1
    with open(f'cmmx-file-summary_{dt.now().strftime("%Y%m%d")}.csv','w',newline='') as csvfile:
        writer = DictWriter(csvfile,headings,'')
        writer.writeheader()
        writer.writerows(all_runs)