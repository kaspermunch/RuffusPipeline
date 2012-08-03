
import XGridInterface
import SnakeFoodWrap
import sys, os, re, inspect, subprocess, tempfile, shutil, time, stat

def _lsGlob(expr):
    """
    calls ls for a shell realistic glob:
    """
    if os.path.isdir(expr):
        return [expr]        
    if expr.startswith('-'): # <- to make sure this is not an option
        return [expr]
    p = subprocess.Popen("ls -d %s" % expr, env=os.environ, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    lst = []
    tmpLst = p.communicate()[0].split("\n")
    for g in tmpLst:
        if not g or g == '.' or g == '..':
            continue
        if expr[0] == '~':
            g = g.replace(os.path.expanduser('~'), '~')
        lst.append(g)
    return lst

class Error(Exception):
    """
    Base class for exceptions in this module.
    """
    pass

class FormatError(Error):
    """
    Exception raised for errors in interaction with formatting.

    Attributes:
        expression: input expression in which
                    the error occurred
        message:    explanation of the error
    """
    def __init__(self, expression, message):
        self.message = expression
        self.message = message
        print self.expression, ": ", self.message

class InputError(Error):
    """
    Exception raised for errors in interaction with input.

    Attributes:
        expression: input expression in which
                    the error occurred
        message:    explanation of the error
    """
    def __init__(self, expression, message):
        self.message = expression
        self.message = message
        print self.expression, ": ", self.message

class XgridError(Error):
    """
    Exception raised for errors in interaction with Xgrid.

    Attributes:
        expression: input expression in which
                    the error occurred
        message:    explanation of the error
    """
    def __init__(self, expression, message):
        self.message = expression
        self.message = message
        print self.expression, ": ", self.message

class DependencyError(Error):
    """
    Exception raised for errors in interaction with Xgrid.

    Attributes:
        expression: input expression in which
                    the error occurred
        message:    explanation of the error
    """
    def __init__(self, expression, message):
        self.message = expression
        self.message = message
        print self.expression, ": ", self.message

class XGrid(object):

    def __init__(self, arg, hostname='', password=''):
        
        if isinstance(arg, str):
            self.cmd, self.indir, dependencies = arg, '', None
        elif isinstance(arg, Dependencies):
            dependencies = arg
            self.cmd, self.indir = self.createIndir(dependencies)            
        else:
            raise InputError(arg, "argument not of appropriate type")

        self.artFileName = None
        if dependencies.pythonExtensionModules:
            self.generateARTscript(dependencies.pythonExtensionModules)

            # add (or change to) a direct link to the correct interpreter
            l = self.cmd.split() # THIS IS THE NEW APPROACH
            if l[0].endswith('python'):
                l.pop(0)
            self.cmd = " ".join([sys.executable] + l)

        conn = XGridInterface.Connection(hostname=hostname, password=password)
        cont = XGridInterface.Controller(conn)
        self.grid = cont.grid(0)

    def __str__(self):
        return '\n'.join([self.cmd, self.indir, self.artFileName])

    def run(self, stdout=None, stderr=None):

        self.job = self.grid.submit(cmd=self.cmd, indir=self.indir, art=self.artFileName, silent=True)
                
        if stdout is None:
            stdoutFile, stdoutFileName = tempfile.mkstemp(suffix=".stdout.xgrid")
        else:
            stdoutFileName = stdout

        if stderr is None:
            stderrFile, stderrFileName = tempfile.mkstemp(suffix=".stderr.xgrid")
        else:
            stderrFileName = stderr

        outdir = tempfile.mkdtemp(prefix='xgrid_')

        self.job.results(block=1, outdir=outdir, stdout=stdoutFileName, stderr=stderrFileName, silent=True)

        for f in self.fileList(outdir):
            if f.endswith('.pyc'):
                os.remove(f)

        for f in os.listdir(outdir):
            tmpPath = os.path.join(outdir, f)
            origPath = self.straightenPath(f)
            if os.path.isdir(tmpPath):
                if self.fileList(tmpPath):
                    os.system("cp -r %s/* %s/." % (tmpPath, origPath))
            else:
                os.system("cp %s %s" % (tmpPath, origPath))

        shutil.rmtree(outdir)

        if self.artFileName:
            os.remove(self.artFileName)
            self.artFileName = None
        
        if stdout is None:
            stdoutFile = open(stdoutFileName)
            sys.stdout.write(stdoutFile.read())
            stdoutFile.close()
            os.remove(stdoutFileName)

        if stderr is None:
            stderrFile = open(stderrFileName)
            sys.stderr.write(stderrFile.read())
            stderrFile.close()
            os.remove(stderrFileName)

#        self.job.delete(silent=True)
        self.job.delete(silent=False)

        self.cmd = None
        self.indir = None
        self.job = None
        self.grid = None

    def fileList(self, dirName):
        outputList = []
        for root, dirs, files in os.walk(dirName):
            for f1 in files:
                outputList.append('/'.join([root, f1]))
        return outputList


    def dirList(self, dirName):
        outputList = []
        for root, dirs, files in os.walk(dirName):
            outputList.append(root)
            for d in dirs:
                outputList.append('/'.join([root, d]))
        return outputList


#     def dirList(self, dirName):
#         outputList = []
#         for root, dirs, files in os.walk(dirName):
#             outputList.append(root)
#             for d in dirs:
#                 outputList.append('/'.join([root, d]))
#             for f1 in files:
#                 outputList.append('/'.join([root, f1]))
#         return outputList


    def flattenPath(self, p):
        return '_' + p.replace('/', '_-_')

        
    def straightenPath(self, p):
        if p.find('_-_') > 0:
            return p.replace('_-_', '/')[1:]
        else:
            return p

    def generateARTscript(self, moduleList):
        artFile, self.artFileName = tempfile.mkstemp(suffix=".art.xgrid")
        f = open(self.artFileName, 'w')
        ## scriptTemplate = "#! /usr/bin/env python\nimport sys\ntry:\n%s\nexcept:\n\tsys.stdout.write('0')\nelse:\n\tsys.stdout.write('1')\n"
        ## print >>f, scriptTemplate % '\n'.join(("\timport %s" % x) for x in [os.path.basename(p) for p in moduleList])

        # THIS IS THE NEW APPROACH
        scriptTemplate = """#! /usr/bin/env python
import os, sys, subprocess
requiredPythonVersion = '%s'
if os.path.exists(requiredPythonVersion) and subprocess.Popen(requiredPythonVersion + ' --version', shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[1].strip() == '%s':
    sys.stdout.write('1')
else:
    sys.stdout.write('0')
"""
        pythonVersion = subprocess.Popen(sys.executable + ' --version', shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[1].strip()
        print >>f, scriptTemplate % (sys.executable, pythonVersion)

        f.close()
        os.chmod(self.artFileName, stat.S_IRWXU | stat.S_IXGRP | stat.S_IRGRP | stat.S_IXOTH | stat.S_IROTH)

    def createIndir(self, dep):

        indir = tempfile.mkdtemp(prefix="xgrid_")

        for g in dep.dirsandfiles + dep.extraDirsAndFiles:
            for f in _lsGlob(g):
                flattenedName = self.flattenPath(os.path.abspath(f))
                indirPath = os.path.join(indir,flattenedName)
                if not os.path.exists(indirPath):
                    ## os.system("pax -rwl %s %s" % (flattenedName, indir))

                    #os.system("cp -r %s %s" % (f, indirPath))
                    if os.path.isdir(f):
                        os.makedirs(indirPath)
                    else:
                        os.system("cp %s %s" % (f, indirPath))

                    dep.cmd = dep.cmd.replace(f, flattenedName)            
                    # add dummy file to otherwise empty dirs:
                    if os.path.isdir(indirPath) and not os.listdir(indirPath):
                        with open(os.path.join(indirPath, 'dummy'), 'w') as dummy:
                            print >>dummy, "This is a dummy file to make xgrid copy an othewise empty dir."
        for f in dep.dirsandfilesfromfiles:
            if not os.path.exists(os.path.join(indir,f)):
                os.system("pax -rwl %s %s" % (f, indir))
                                            
        for p in dep.dependencies + dep.extraDependencies + dep.pythonExtensionModules:
            os.system("cp -r %s %s" % (p, indir))        

        return dep.cmd, indir

#         indir = tempfile.mkdtemp(prefix="xgrid_")
# 
#         for g in dep.dirsandfiles + dep.extraDirsAndFiles:
#             for f in _lsGlob(g):
#                 if f.startswith('../') or f.startswith('/') or f.startswith('~'):
#                     # files/dirs with absolute paths or paths above cwd:
#                     flattenedName = "_" + os.path.abspath(f).replace("/", "_-_")
#                     indirPath = os.path.join(indir,flattenedName)
#                     if not os.path.exists(indirPath):
#                         os.system("cp -r %s %s" % (f, indirPath))
#                         dep.cmd = dep.cmd.replace(f, flattenedName)            
#                 else:
#                     # all other paths:
#                     indirPath = os.path.join(indir,f)
#                     if not os.path.exists(indirPath):
#                         os.system("pax -rwl %s %s" % (f, indir))
# 
#                 # add dummy file to otherwise empty dirs:
#                 if os.path.isdir(indirPath) and not os.listdir(indirPath):
#                     with open(os.path.join(indir,f, 'dummy'), 'w') as dummy:
#                         print >>dummy, "This is a dummy file to make xgrid copy an othewise empty dir."
#                                 
#         for p in dep.dependencies + dep.extraDependencies:
#             os.system("cp -r %s %s" % (p, indir))        
# 
#         return dep.cmd, indir

#         indir = tempfile.mkdtemp(prefix="xgrid_")
# 
#         for g in dep.dirsandfiles:
#             for f in _lsGlob(g):
#                 if re.search('\.\.', f) or f.startswith('/') or f.startswith('~'):
#                     if os.path.isdir(f):
#                         print "We only handle dirs in or below current working dir"
#                         sys.exit()
#                     else:
#                         localName = "_" + f.replace("/", "_")
#                         os.system("ln %s %s" % (f, os.path.join(indir, localName)))
#                         dep.cmd = dep.cmd.replace(f, localName)
#                 else:
#                     if not os.path.exists(os.path.join(indir,f)):
#                         os.system("pax -rwl %s %s" % (f, indir))
#                         #os.system("cp -R %s %s" % (f, p))
#                         if os.path.isdir(os.path.join(indir,f)) and not os.listdir(os.path.join(indir,f)):
#                             with open(os.path.join(indir,f, 'dummy'), 'w') as dummy:
#                                 print >>dummy, "This is a dummy file to make xgrid copy an othewise empty dir."
#                                 
# 
#         for f in dep.extraDirsAndFiles:
#             os.system("pax -rwl %s %s" % (f, indir))
#             #os.system("cp -R %s %s" % (f, p))
# 
#         for p in dep.dependencies:
#             #os.system("pax -rwl %s %s" % (p, indir))
#             os.system("cp -r %s %s" % (p, indir))        
# 
#         for f in dep.extraDependencies:
#             #os.system("pax -rwl %s %s" % (p, indir))
#             os.system("cp -r %s %s" % (p, indir))        
# 
#         return dep.cmd, indir


        
class Dependencies(object):

#    def __init__(self, cmd, frame=None, testFile=None, extraDependencies=[], extraDirsAndFiles=[]):
    def __init__(self, cmd, callingFile=None, testFile=None, extraDependencies=[], extraDirsAndFiles=[]):

        self.callingFile = callingFile
        self.testFile = testFile
        self.dependencies = list()
        self.dirsandfiles = list()
        self.pythonExtensionModules = list()
        self.dirsandfilesfromfiles = list()
        self.extraDependencies = extraDependencies
        self.extraDirsAndFiles = extraDirsAndFiles
        
        cmd, dependencies, dirsandfiles, dirsandfilesfromfiles = self._getCmdDependencies(cmd)
        self.cmd = cmd
        self.dependencies.extend(dependencies)
        self.dirsandfiles.extend(dirsandfiles)
        self.dirsandfilesfromfiles.extend(dirsandfilesfromfiles)

        if callingFile:
            # find non standard libraries used in script:
            for modulePath, moduleName in SnakeFoodWrap.gendeps(callingFile):

                if not moduleName:
                    continue
                modulePath = os.path.join(modulePath, moduleName)

                if not re.search(r'/Library/Frameworks', modulePath) or re.search(r'site-packages', modulePath):                        

                    while os.path.exists(os.path.join(os.path.dirname(modulePath), "__init__.py")):
                        modulePath = os.path.dirname(modulePath)

                    # make a special list for compiled extension modules:
                    if os.path.isdir(modulePath):
                        pythonExtension = False
                        for root, dirs, files in os.walk(modulePath):
                            for f1 in files:
                                if f1.endswith('.so'):
                                    pythonExtension = True
                                    self.pythonExtensionModules.append(modulePath)
                                    break
                            if pythonExtension:
                                break
                        if pythonExtension:
                            continue
                    # FIXME: this should be a set so we don't get replicates...
                    self.dependencies.append(modulePath.replace('.pyc', '.py'))



#        if frame:
#             for name, var in frame.f_globals.items():
#                 if name.startswith('__') and name.endswith('__'):
#                     continue
# 
#                 modulePath = None
#                 if inspect.ismodule(var) and hasattr(var, "__file__"):
#                     modulePath = var.__file__
#                 else:
#                     mod = inspect.getmodule(var)
#                     if mod and hasattr(mod, "__file__"):
#                         modulePath = mod.__file__
# 
#                 if modulePath:
#                     if not re.search(r'/Library/Frameworks', modulePath) or re.search(r'site-packages', modulePath):                        
# 
#                         while os.path.exists(os.path.join(os.path.dirname(modulePath), "__init__.py")):
#                             modulePath = os.path.dirname(modulePath)
# 
#                         # make a special list for compiled extension modules:
#                         if os.path.isdir(modulePath):
#                             pythonExtension = False
#                             for root, dirs, files in os.walk(modulePath):
#                                 for f1 in files:
#                                     if f1.endswith('.so'):
#                                         pythonExtension = True
#                                         self.pythonExtensionModules.append(os.path.basename(modulePath))
#                                         break
#                                 if pythonExtension:
#                                     break
#                             if pythonExtension:
#                                 continue
# 
#                         self.dependencies.append(modulePath.replace('.pyc', '.py'))






#             # find commands called from function:
#             source = inspect.getsource(frame)
#             commandList = list()
#             for x in re.finditer(r'(system|popen|Popen)\(\s*[\'\"](.*?)[\'\"]\s*\)', source):
#                 cmd = x.group(2)
#                 # evaluate command string if necessary:
#                 if re.search(r'[\'\"].*[\'\"]\s*%\s*\S+', cmd):
#                     interpolCmd = cmd
#                     loc = frame.f_locals
#                     for var, val in loc.items():
#                         print var, val
#                         interpolCmd = re.sub(r'\b%s\b' % var, str(val), interpolCmd)
#                         print interpolCmd
#                     try:
#                         cmd = eval(interpolCmd)
#                     except NameError:
#                         pass
#                 else:
#                     commandList.append(cmd)
#                 dependencies, dirsandfiles = self._getCmdDependencies(cmd)
#                 self.dependencies.extend(dependencies)
#                 self.dirsandfiles.extend(dirsandfiles)

        self.pythonExtensionModules = list(set(self.pythonExtensionModules))
        self.dependencies = list(set(self.dependencies))
        self.dirsandfiles = list(set(self.dirsandfiles))


    def _getCmdDependencies(self, cmd):

        standardToolList = ["perl", "python", "sh", "bash", "cat", "echo", "sed", "grep", "head"]

        # list of globs to copy to root of bundle:
        dependencyFileGlobs = []
        # executables:
        subcmds = cmd.split("|")
        for j, s in enumerate(subcmds):
            lst = s.split()
            exe = lst[0]
            if exe in standardToolList:
                continue
            lst[0] = os.path.join(".", os.path.basename(exe))
            subcmds[j] = " ".join(lst)
            eLst = _lsGlob(exe)
            if not eLst or not os.path.exists(eLst[0]) or os.path.isdir(eLst[0]) :
                p = subprocess.Popen("which %s" % exe, env=os.environ, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                path = p.communicate()[0].strip()
                if not path:
                    raise DependencyError(exe, "could not locate binary")
                    sys.exit()
            else:
                path = exe
            dependencyFileGlobs.append(path)
        cmd = " | ".join(subcmds)
        
        # list of globs to copy to the same relative path in bundle:
        dirAndFileGlobs = []
        dirAndFileGlobsFromListFiles = []
        # get other files from command line (not the very first word that is the executable):
        for word in re.split(r'[=\s]+', cmd)[1:]:            
            if os.path.exists(word) or re.search(r'\*', word):
                if word.endswith(".filelist"):
                    f = open(word)
                    dirAndFileGlobsFromListFiles.extend(f.read().strip().split("\n"))
                    f.close()
                dirAndFileGlobs.append(word)
            else:
                # see it it could be an output file we need to create a dir for. The rule
                # is: if any top part of the path in the command line exists and is a dir
                # the full dir path is created in the bundle.
                path = os.path.split(word)[0]
                d = path
                while d:
                    if os.path.exists(d) and os.path.isdir(d):
                        dirAndFileGlobs.append(path)
                        break
                    else:
                        d = os.path.split(d)[0]
 
#                 path = os.path.split(word)[0]
#                 d = path
#                 while d:
#                     if os.path.exists(d) and os.path.isdir(d):
#                         cmd = re.sub('([=\s]+)%s(\s+|$)' % re.escape(word), r'\1%s\2' % ('_' + word.replace('/', '_-_')), cmd)
#                         break
#                     else:
#                         d = os.path.split(d)[0]

        return cmd, dependencyFileGlobs, dirAndFileGlobs, dirAndFileGlobsFromListFiles




    #### KM #############################################################################



if __name__ == "__main__":
    cmd = "./testscript.py -a 'c[1]' input.txt ./one/two/three/output.txt"
#    cmd = "tablemod.py -a 'c[1]' ../ancestral_recomb/input.txt ./one/two/three/output.txt"
    dependencies = Dependencies(cmd=cmd)#, outputDir='/Users/kasper/projects/ancestral_recomb/one/two/three')
    p = XGrid(dependencies)
    


# FIXME: It seems that xgrid won't overwrite files and when i attempt to will make a
# dummmy directory to open the file in instead. When trying to open the file here it is
# not taken into account that the dir substructure in indir does not exist in the dummy
# dir:
# 
# e.g.
# if a file output.txt already exists as
# ./one/two/three/output.txt
# xgrid will try to open it like this
# Users/kasper/projects/ancestral_recomb/./one/two/three/output.txt
# and will fail because one/two/three dirs do not exist.
# It seems the only solution is to
# 
# one thing we could do is to flatten all file names e.g. from ./one/two/three/output.txt to ___one___two___three___output.txt
# and then once copied back write them to the appropriate dirs in
# 
# # in outline like this:
# outdir = tempfile.mkdtemp()
# self.job.results(block=1, outdir=outdir, stdout=stdoutFileName, stderr=stderrFileName)
# for flattenedPath in os.listdir(outdir):
#     path = getPathAndBaseName(flattenedPath)
#     os.system(cp flattenedPath, path)
# shutil.rmtree(outdir)



# but this creates a problem with list files but I guess we can make them special and create real paths for those....



# Dependencies:
# _getCmdDependencies: generates dependencies
# 
# createIndir should be a Xgrid method and so should flattenPath and straightenPath


