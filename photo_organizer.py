import json
import os, re, sys, csv
import shutil
import filecmp
import logging
import subprocess
from datetime import datetime


class PhotoOrganizer(object):
    """
    Class encapsulating script functionality to use Exiftool to get metadata
    and copy/move it to file structure desired.
    """
    
    
    def __init__(self, options):
        """
        Constructor of the class
        """
        
        self.options = options
        self.metadatajson = None
        self.paths = {}
        self.log = logging.getLogger('PhotoOrganizer')
        self.log.setLevel(logging.DEBUG)
        fileHandler = logging.FileHandler("PhotoOrganizer.log", mode='w', encoding='UTF-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileHandler.setFormatter(formatter)
        self.log.addHandler(fileHandler)
        self.log.info("Initializing PhotoOrganizer")
        
        
    def get_metadata_json(self):
        """
        Function to run Exiftool and storing received metadata to member variable.
        """
        
        print('Running Exiftool to get metadata of images in Json format')
        self.log.info('Running Exiftool to get metadata of images in Json format')
        
        args = ['-j', '-a', '-G']
        
        if self.options.recursive:
            args += ['-r']
        
        args.append(self.options.source_dir)
        filename = 'metadata.json'
        
        exiftool = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'exiftool.exe')
        
        command = exiftool + ' ' + ' '.join(args) + ' >' + filename
        subprocess.call(command, shell=True)
        
        try:
            self.metadatajson = json.load(open(filename, encoding='UTF-8', mode='r')) 
        except ValueError:
            print('No files to process')
            self.log.info('No files to process')
            return False
        finally:
            if not self.options.keep_meta:
                os.remove(filename)
        
        return True
     
    def get_paths(self):
        """
        Function to analyze metadata and resolving paths to member variable.
        """
        
        metadatafields = ['File:FileModifyDate', 'File:FileAccessDate', 'File:FileCreateDate',\
                          'EXIF:ModifyDate', 'EXIF:DateTimeOriginal', 'EXIF:CreateDate']
        for index, image in enumerate(self.metadatajson):
            sourcefilename = os.path.join(self.options.source_dir, image['SourceFile'])
            print("\rHandling file {}/{}".format(index + 1, len(self.metadatajson)), end='')
            self.log.info('Handling file {}'.format(sourcefilename))
            
            dates = []
            for metadata in image:
                if metadata in metadatafields:
                    dt = self.__get_datetime(image[metadata])
                    self.log.info('Metadata: {} Datetime: {}'.format(metadata, dt))
                    if dt:
                        dates.append((dt, metadata))
                
            dates.sort()
            self.paths[sourcefilename] = {}
            if len(dates):
                dir_structure = dates[0][0].strftime(self.options.sort)
                self.paths[sourcefilename]['targetpath'] = os.path.join(self.options.target_dir, 
                                                        dir_structure, 
                                                        os.path.basename(sourcefilename))
            else:
                self.paths[sourcefilename]['targetpath'] = 'no-info'
                
            self.log.info('Target path: {}'.format(self.paths[sourcefilename]['targetpath']))
    
    def store_results(self):
        """
        Function to perform copy of move actions based on the get_path analysis.
        """
        
        self.log.info('Storing results...')
        
        for path in self.paths:
            sourcepath = path
            targetpath = self.paths[path]['targetpath']
            
            self.log.info('Handling {}'.format(path))
            
            while True: 
                if os.path.isfile(targetpath) and filecmp.cmp(sourcepath, targetpath):
                    self.log.info('Identical file found {}'.format(targetpath))
                    break
                elif os.path.isfile(targetpath):
                    self.log.info('File with same name {}'.format(targetpath))
                    targetpath = self.__get_next_filename(targetpath)
                else:
                    self.log.info('Copy or Move to {}'.format(targetpath))
                    self.__copy_or_move(sourcepath, targetpath)
                    break
  
    
    def __copy_or_move(self, source, target):
        """
        Internal function to perform copy or move based on the command line
        arguments. Supports also dry-run option which only writes information
        to the log file.
        """
        
        if self.options.dry_run:
            self.log.info('Dry-run copy or move')
        else:
            
            if not os.path.isdir(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            
            if self.options.copy:
                shutil.copy2(source, target)
            else:
                shutil.move(source, target)  
    
    
    def __get_next_filename(self, filename):
        """
        Internal function to get next filename available.
        Uses pattern filename<_NUMBER>.extension
        """
        
        base, ext = os.path.splitext(filename)
        if len(base.rsplit('_', 1)) == 1:
            number = 1
        else:
            number = int(rsplit('_', 1)[1]) + 1
        
        return base + '_' + str(number) + ext                
                
            
    def __get_datetime(self, datestr):
        """
        Internal function to get string representation of the date and returning it as 
        datetime object. 
        """
        
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
            if int(year) < 1970:
            #strptime cannot handle years earlier than 1970.
                return None
            return datetime.strptime(dateformatter, 
                                     '%Y %m %d %H %M %S %z')
            
        else:
            return None
                
                   

def main():
    import argparse

    # setup command line parsing
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Organizes files into folders by date using EXIF data')
    parser.add_argument('source_dir', type=str, help='source directory')
    parser.add_argument('target_dir', type=str, help='target directory')
    parser.add_argument('-r', '--recursive', action='store_true', help='Search source directory recursively')
    parser.add_argument('-k', '--keep-meta', action='store_true', help='Keeps metadata JSON after the run')
    parser.add_argument('-c', '--copy', action='store_true', help='copy files instead of move')
    parser.add_argument('--dry-run', action='store_true', help='Performs only analysis, not doing actual moving or copying')
    parser.add_argument('--sort', type=str, default='%Y\%m',
                        help="choose destination folder structure using datetime format \n\
    The default is '%%Y\%%m', which separates by year then month \n\
    with both the month number and name (e.g., 2012/02).")
    parser.add_argument('--csv', help='Creates CSV report and stores it to this filename')

    # parse command line arguments
    options = parser.parse_args()

    ph = PhotoOrganizer(options)
    if ph.get_metadata_json():
        ph.get_paths()
        ph.store_results()
    
    
if __name__ == '__main__':
    main()
