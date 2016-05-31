import json
import os, re, sys
import shutil
import filecmp
import logging
import subprocess
from datetime import datetime


class PhotoOrganizer(object):
    """
    Class that encapsulates functionality of using Exiftool to get metadata of the images
    and copy/move it to file structure desired.
    """
    
    
    def __init__(self, options):
        """
        Constructor of the class
        """
        
        self.options = options
        self.paths = {}
        
        #Setting up logger.
        self.log = logging.getLogger('PhotoOrganizer')
        self.log.setLevel(logging.DEBUG)
        fileHandler = logging.FileHandler("PhotoOrganizer.log", mode='w', encoding='UTF-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileHandler.setFormatter(formatter)
        self.log.addHandler(fileHandler)
        self.log.info("Initializing PhotoOrganizer")
        
        
    def get_metadata_json(self):
        """
        Function to run Exiftool and returns JSON object describing meta values.
        """
        
        print('Running Exiftool to get metadata of images in Json format. This might take time...')
        self.log.info('Running Exiftool to get metadata of images in Json format')
        
        args = ['-j', '-a', '-G']
        
        if self.options.recursive:
            args += ['-r']
        
        args.append(self.options.source_dir)
        filename = self.options.meta_file
        
        exiftool = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'exiftool.exe')
        
        command = exiftool + ' ' + ' '.join(args) + ' >' + filename
        subprocess.call(command, shell=True)
        
        metadatajson = None
        
        try:
            metadatajson = json.load(open(filename, encoding='UTF-8', mode='r')) 
        except ValueError:
            print('No files to process')
            self.log.info('No files to process')
        finally:
            if not self.options.keep_meta:
                os.remove(filename)
        
        return metadatajson
     
    def get_paths(self, jsonfile):
        """
        Function to analyze metadata and resolving paths to member variable.
        """
        
        metadatafields = ['File:FileModifyDate', 'File:FileAccessDate', 'File:FileCreateDate',\
                          'EXIF:ModifyDate', 'EXIF:DateTimeOriginal', 'EXIF:CreateDate']
        for index, image in enumerate(jsonfile):
            sourcefilename = os.path.join(self.options.source_dir, image['SourceFile'])
            print("\rGetting target paths for files {}/{}".format(index + 1, len(jsonfile)), end='')
            self.log.info('Handling file {}'.format(sourcefilename))
            
            dates = []
            for metadata in image:
                if metadata in metadatafields:
                    dt = self.get_datetime(image[metadata])
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
        print("\nStarting to store results.")
        
        for index, path in enumerate(self.paths):
            sourcepath = path
            targetpath = self.paths[path]['targetpath']
            
            self.log.info('Handling {}'.format(path))
            print("\rStoring file {}/{}".format(index + 1, len(self.paths)), end='')
            
            fileindex = 1
            while True: 
                if os.path.isfile(targetpath) and filecmp.cmp(sourcepath, targetpath):
                    self.log.info('Identical file found {}'.format(targetpath))
                    break
                elif os.path.isfile(targetpath):
                    self.log.info('File with same name {}'.format(targetpath))
                    targetpath = self.get_next_filename(targetpath, fileindex)
                    fileindex += 1
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
    
    
    def get_next_filename(self, filename, fileindex):
        """
        Internal function to get next filename available.
        Uses pattern filename<_NUMBER>.extension
        """
        
        base, ext = os.path.splitext(filename)
        newfile = ""
        if fileindex == 1:
        #want to add _ after filename and therefore needs special handling for the first round
            newfile = base + '_1' + ext
        else:
            newfile = base.rsplit('_', 1)[0] + '_{}'.format(str(fileindex)) + ext

        return newfile                
                
            
    def get_datetime(self, datestr):
        """
        Function to get string representation of the date and returning it as 
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
    parser.add_argument('-m', '--meta-only', action='store_true', help='Runs metadata collection part only and never deletes the file.')
    parser.add_argument('--meta-file', type=str, help='Metadata filename', default='image_meta.json')
    parser.add_argument('--skip-meta', action='store_true', help='Gets previously generated metadata file. Must be found from \n\
    the location that is defined by --meta-file argument.')

    # parse command line arguments
    options = parser.parse_args()

    if options.meta_only:
    #Doesn't make sense to run metadata generation only and then delete the results.
        options.keep_meta = True


    ph = PhotoOrganizer(options)
    
    metadatajsonObject = None
    if not options.skip_meta:
        metadatajsonObject = ph.get_metadata_json()
    elif os.path.is_file(options.meta_file):
        metadatajsonObject=json.load(open(filename, encoding='UTF-8', mode='r'))
    
    if not options.meta_only:
        ph.get_paths(metadatajsonObject)
        ph.store_results()
    
    
if __name__ == '__main__':
    main()
