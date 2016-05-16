import subprocess
import sysconfig
import shutil
import json
import os
import re
from datetime import datetime

exiftool = os.path.join('C:\skriptit', 'exiftool.exe')


class PhotoOrganizer(object):
    
    def __init__(self, options):
        self.options = options
        self.metadatajson = None
        self.paths = {}
        
        
    def get_metadata_json(self):
        args = ['-j', '-a', '-G']
        
        if self.options.recursive:
            args += ['-r']
        
        args.append(self.options.src_dir)
        filename = 'metadata.json'
        
        command = exiftool + ' ' + ' '.join(args) + ' >' + filename
        subprocess.call(command, shell=True)
        
        self.metadatajson = json.load(open(filename, 'r')) 
     
    def get_paths(self):
        
        metadatafields = ['File:FileModifyDate', 'File:FileAccessDate', 'File:FileCreateDate',\
                          'EXIF:ModifyDate', 'EXIF:DateTimeOriginal', 'EXIF:CreateDate']
        for image in self.metadatajson:
            sourcefilename = os.path.join(self.options.src_dir, image['SourceFile'])
            print("Handling file\n" + sourcefilename)
            
            dates = []
            for metadata in image:
                if metadata in metadatafields:
                    dt = self.get_datetime(image[metadata])
                    if dt:
                        dates.append((dt, metadata))
                
            dates.sort()
            self.paths[sourcefilename] = {}
            if len(dates):
                dir_structure = dates[0][0].strftime(self.options.sort)
                self.paths['targetpath'] = os.path.join(self.options.dest_dir, 
                                                        dir_structure, 
                                                        os.path.basename(sourcefilename))
            else:
                self.paths['targetpath'] = 'no-info'
                
            
    def get_datetime(self, datestr):
        mo = re.search('(\d+):(\d+):(\d+) (\d+):(\d+):(\d+)(.*)', datestr)
        if mo:
            year = mo.group(1)
            month = mo.group(2)
            day = mo.group(3)
            hour = mo.group(4)
            minute = mo.group(5)
            second = mo.group(6)
            offset = mo.group(7)
            
            if offset:
                offset = offset.replace(':', '')
            else:
                offset = '+0000'
            
            dateformatter = '{0} {1} {2} {3} {4} {5} {6}'.format(year, month, 
                                                                 day, hour, 
                                                                 minute, second, 
                                                                 offset)
            return datetime.strptime(dateformatter, 
                                     '%Y %m %d %H %M %S %z')
            
        else:
            return None
                
                   

def main():
    import argparse

    # setup command line parsing
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Organizes files (primarily photos and videos) into folders by date\nusing EXIF and other metadata')
    parser.add_argument('src_dir', type=str, help='source directory')
    parser.add_argument('dest_dir', type=str, help='destination directory')
    parser.add_argument('-r', '--recursive', action='store_true', help='search src_dir recursively')
    parser.add_argument('-c', '--copy', action='store_true', help='copy files instead of move')
    parser.add_argument('--sort', type=str, default='%Y\%m',
                        help="choose destination folder structure using datetime format \n\
    https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior. \n\
    Use forward slashes / to indicate subdirectory(ies) (independent of your OS convention). \n\
    The default is '%%Y/%%m-%%b', which separates by year then month \n\
    with both the month number and name (e.g., 2012/02-Feb).")

    # parse command line arguments
    options = parser.parse_args()

    ph = PhotoOrganizer(options)
    ph.get_metadata_json()
    ph.get_paths()
    
    
if __name__ == '__main__':
    main()
