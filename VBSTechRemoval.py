import os
import fnmatch
import sys
import re
import VBSTechRemovalCore


#Gets arguments passed to the scripts
def get_main_arg ():
    if len(sys.argv) < 4:
        print("""Usage: 
python VBSTechRemoval.py <path to project dir> <technology name> <0 or 1> -d

Example:
python VBSTechRemoval.py C:\YourProjectSources\lib _SOME_TECH 1
        
See https://github.com/VHonzik/VBSTechRemoval/blob/master/README.md for more information.

vaclav.honzik@bisimulations.com 2014
                """)
        sys.exit()
    else:
        path = sys.argv[1]
        techname = sys.argv[2]
        trueorfalse = sys.argv[3]
        alwaysTrue = True
        if(trueorfalse=='0'):
            alwaysTrue = False
        elif(trueorfalse=='1'):
            alwaysTrue = True
        else:
            print('Third paramater must be either 1 or 0.')
            sys.exit()
        if(len(sys.argv) > 4):
            debugfile = sys.argv[4]
        else:
            debugfile = ''
    return [path,techname,alwaysTrue,debugfile]

#List all C++ files (.cpp or .hpp or .h or .hlsl) from path or fail if no present
def get_files(path):
    cfiles = []
    cfilesregex = re.compile('^.*\.(?:[ch](pp)?$)|(?:hlsl$)')
    for root, subFolders, files in os.walk(path,followlinks=True):
         for filename in files:
            if(cfilesregex.search(filename)!=None) : cfiles.append(os.path.join(root,filename))
            
    if len(cfiles)<1:
        print('No C++ files found. Are you sure you are in good directory? ('+path+')')
        sys.exit()
    cfiles.sort()
    return cfiles 


#Process a single file
def process_file(pathandfile,technologyName,alwaysTrue,log):    
    with open(pathandfile, 'r') as f:
        code = f.readlines()
        # use core tech remover class
        remover = VBSTechRemovalCore.TechRemover(code, technologyName, alwaysTrue, log)
        remover.process()
        if(remover.anyChange):
            if(not log is None): log.write('Writting changes to the file.')
            with open(pathandfile,'w') as f:                         
                for cline in remover.code:
                    f.write(cline)


#Main function calling process_file on every C++ file
def main():
    args = get_main_arg()
    path = args[0]
    technologyName = args[1]
    alwaysTrue = args[2]
    debugfile = args[3]
    
    
    if(debugfile=='-d'):         
        os.system('cls')
        with open('VBSTechRemovalDebug.log','w') as log:
            files = get_files(path)
            os.system('cls')
            for idx,f in enumerate(files):
                print('Processing file %d out of %d: %s' % (idx+1,len(files),f))
                log.write('Processing file: %s\n' % (f))
                process_file(f,technologyName,alwaysTrue,log)

            print('Success: Processing finished')
    
    else:
        os.system('cls')
        print('Retrieving file list from %s' % path)
        files = get_files(path)
        
        os.system('cls')
        print('Starting the processing. %d' % len(files))
        for idx,f in enumerate(files):
            print('Processing file %d out of %d: %s' % (idx+1,len(files),f))
            process_file(f,technologyName,alwaysTrue,None)

        print('Success: Processing finished')

if __name__ == '__main__':            
    main()
