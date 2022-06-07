from concurrent.futures import ThreadPoolExecutor, as_completed
from json import loads
from os import getenv, walk, system
from os.path import abspath, basename, dirname, getmtime, isdir, isfile, join
from sys import argv
from time import time
from subprocess import CREATE_BREAKAWAY_FROM_JOB, Popen, CREATE_NO_WINDOW

import boto3 as b3


def find_key_file(key_path='key_info.txt'):
    """
    search user's account for key if it's not in current directory.
    """
    if isfile(key_path):
        return abspath(key_path)
    else:
        possible_keys = {}
        user = getenv('userprofile')
        for r, d, f in walk(user):
            for item in f:
                if item == 'key_info.txt':
                    possible_keys[getmtime(join(r, item))] = join(r, item)
        if possible_keys:
            lastKey = possible_keys[sorted(possible_keys)[-1]]
            print('using key login info from: ' + lastKey)
            return lastKey
    raise FileNotFoundError(
        'Could not locate a valid AWS key file in user profile: ' + user)


def is_accepted_file(filename: str):
    """
    checks if file has an extension in ignore list / prohibited file
    """
    # Prohibit uploading user credential keys to S3 storage
    if (filename.endswith('key_info.txt')
        # Block file extensions as listed in Ignore on line 60
            or '.' + filename.split('.')[-1] in vars['IgnoreEXT']):
        return False
    return True


def already_on_S3(AWSname: str):
    """
    True if file with given name exists already in AWSBucket.
    Always false if overwrite is true.
    """
    if not vars['Overwrite']:  # Check if file exists if we aren't overwriting
        response = s3_client.list_objects_v2(
            Bucket=vars['AWSBucket'],
            Prefix=AWSname
        )
        try:
            if len(response['Contents']):
                return True  # The key is already valid in AWS S3
        except KeyError:
            pass  # The key was not valid in AWS S3
    return False  # We're overwriting file / it doesn't exist yet


def should_upload_file(filename: str, AWSname: str):
    if is_accepted_file(filename) and not already_on_S3(AWSname):
        print('uploading file: ' + filename)
        return True
    return False


def get_aws_key(root_dir_remove: str, current_root: str, item: str):
    """
    checks if the possible key contains upload dir, and
    removes it. maintains directory structure when uploading.
    """
    if current_root.startswith(root_dir_remove):
        return join(
            current_root[len(root_dir_remove) + 1:], item).replace('\\', '/')
    return join(current_root, item).replace('\\', '/')


vars = {
    # Overwrite if file with same name exists on AWS-S3?
    'Overwrite': True,
    # Ignore files with these extensions by default. Remove if needed
    'IgnoreEXT': ['.py', '.bat', '.exe'],
    # Path of file to upload, or directory to upload all files recursively
    'Upload': dirname(abspath(argv[0])),
    # Path to the BlackSea key data file
    'AWSKey': find_key_file(),
    # Location in bucket to store all data uploads
    'AWSPrefix': 'shared/ArtifactFileData',
    # S3 Bucket name
    'AWSBucket': 'gbd-3dp-data-lake-stage-data-science',
    # Can be path. Script will keep running until this file/folder is no
    # longer modified
    'SYNC': None,
}  # Set current state:
for name in vars:
    if name in argv:
        arg_val = argv[argv.index(name) + 1]
        if name == 'Overwrite':
            vars[name] = True
            continue
        if name == 'IgnoreEXT':
            [vars[name].append(item) for item in arg_val.split(';')]
            continue
        if name == 'SYNC':
            vars[name] = abspath(arg_val)
        vars[name] = arg_val
if vars['SYNC']:
    SYNC_LAST_MOD = getmtime(vars['SYNC'])
# Extract AWS auth info from blacksea key file:
if isfile(vars['AWSKey']):
    with open(vars['AWSKey'], 'r') as keyfile:
        jsonkey = loads(keyfile.read())
    key = jsonkey['key_info'][-1]
    s3_client = b3.client('s3',
                          aws_access_key_id=key['access_key_id'],
                          aws_secret_access_key=key['secret_key'])
# Upload file or directory:
if isfile(vars['Upload']):
    s3_client.upload_file(
        vars['Upload'],
        vars['AWSBucket'],
        f'{vars["AWSPrefix"]}/{basename(vars["Upload"])}')
elif isdir(vars['Upload']):
    # Recursively upload files 40 at a time asyncronously when they have
    # accepted ext and are not on S3 already:
    with ThreadPoolExecutor(max_workers=40) as uploadPool:
        for r, d, f in walk(vars['Upload']):
            futs = {uploadPool.submit(
                s3_client.upload_file,
                Filename=join(r, item),  # File to upload (local path)
                Bucket=vars['AWSBucket'],  # Bucket name on AWS S3
                # Key for retriving from bucket
                Key=f'{vars["AWSPrefix"]}/{get_aws_key(vars["Upload"],r,item)}'
            ): join(r, item)
                for item in f if should_upload_file(item, f'{vars["AWSPrefix"]}/{get_aws_key(vars["Upload"],r,item)}')}
        print('finishing uploads', end='...')
        for fut in as_completed(futs):
            if not (fut.result() and fut.exception()):
                print(futs[fut] + ' uploaded successfully!')
        print('All uploads complete!')
if vars['SYNC']:
    print('waiting for file-changes to continue synchronizing files...')
    start_wait = time()  # Wait a min or for any changes to be made
    while time() - start_wait < 60 or getmtime(vars['SYNC']) == SYNC_LAST_MOD:
        pass
    if getmtime(vars['SYNC']) != SYNC_LAST_MOD:
        if len(vars['IgnoreEXT']) > 3:
            IGNORE = ';'.join(vars['IgnoreEXT'][3:])
        else:
            IGNORE = ''
        Popen(  # Run again with the exact same state as now
            ['python', argv[0],
             'AWSKey', vars['AWSKey'],
             'AWSPrefix', vars['AWSPrefix'],
             'SYNC', vars['SYNC'],
             'Upload', vars['Upload'],
             'IgnoreExt', IGNORE],
            creationflags=CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB
        )
    system('exit')