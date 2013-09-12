
import shutil, tempfile, os, sys, re, inspect, subprocess

import XGrid, SGE
#from bbfreeze import Freezer

class PipelineUtils(object):

    def __init__(self, mode, controlvariables):
        assert mode in ['', 'local', 'sge', 'xgrid']
        self.controlvariables = controlvariables
        self.callingFile = os.path.abspath(inspect.stack()[1][1])
        self.mode = mode
        self.extraDependencies = list()
        self.extraDirsAndFiles = list()
        self.hostname = '10.11.101.253'
        self.password = 'birc'

    def addDependencies(self, lst):
        self.extraDependencies.extend(lst)

    def addDirsAndFiles(self, lst):
        self.extraDirsAndFiles.extend(lst)

    def setGrid(self, hostname, password):
        self.hostname = hostname
        self.password = password

#     def freezePythonForDistribution(self):
# 
#         self.freezeDir = tempfile.mkdtemp(prefix="freeze_")
# 
#         f = Freezer(self.freezeDir) # setup dir
#         f.include_py = False
#         f.addScript(self.callingFile) # add script
#         f() # starts the freezing process
# 
#         # create symlink to .py name:
#         exeName = os.path.join(self.freezeDir, os.path.splitext(os.path.split(self.callingFile)[1])[0])
#         os.symlink(exeName, exeName+'.py')


    def distribute(self):
        """
        use like this:
        def task():
            if distribute(): return

            rest of function ...
        """
        if self.mode:

            callingFrame, callingFile, lineNr, callingFunction, lineSource, _ = inspect.stack()[1]

# # FIXME: Test this should allow that us to get calling frame from a loaded
# # module while knowing which script file to run in the distributed job:            
#             callingFile = self.callingFile

            argsInfo = inspect.getargvalues(callingFrame)
            inputFileNames = argsInfo.locals[argsInfo.args[0]]
            if not isinstance(inputFileNames, list):
                inputFileNames = [inputFileNames]
            outputFileNames = argsInfo.locals[argsInfo.args[1]]
            if not isinstance(outputFileNames, list):
                outputFileNames = [outputFileNames]
            outputDirs = list()
            for o in outputFileNames:
                if os.path.exists(o):
                    os.remove(o) # remove output file because Xgrid won't overwrite existing files passed along.
            extraArguments = []
            if argsInfo.args > 2:
                for i in range(2,len(argsInfo.args)):
                    extraArguments.append(argsInfo.locals[argsInfo.args[i]])

            extraArgumentTypes = list()
            for a in extraArguments:
                extraArgumentTypes.append(repr(type(a)).replace("<type '", ''). replace("'>", ''))
            extraArguments = ["%s:%s" % t for t in zip(extraArgumentTypes, map(str, extraArguments))]

            mapping = ','.join(['0'] * len(inputFileNames) + ['1'] * len(outputFileNames) + ['2'] * len(extraArguments))        
#            print map(type, [inputFileNames, outputFileNames, map(str, extraArguments)])
            allArguments = " ".join(inputFileNames + outputFileNames + map(str, extraArguments))
            cmd = "python %s --controlvariables %s '%s' %s %s" % (callingFile, self.controlvariables, callingFunction, mapping, allArguments) # function/task is quoted so it is not confused with a possible file with same name
            if self.mode == 'local':
                p = subprocess.Popen(cmd, env=os.environ, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                stdout, stderr = p.communicate()
                print >>sys.stdout, stdout
                print >>sys.stderr, stderr
            elif self.mode == 'sge':
                parallel_task = SGE.SGE(cmd)
                parallel_task.run()
            elif self.mode == 'xgrid':
#                dependencies = XGrid.Dependencies(cmd, frame=callingFrame, extraDependencies=self.extraDependencies, extraDirsAndFiles=self.extraDirsAndFiles)
                dependencies = XGrid.Dependencies(cmd, callingFile=callingFile, extraDependencies=self.extraDependencies, extraDirsAndFiles=self.extraDirsAndFiles)
                parallel_task = XGrid.XGrid(dependencies, hostname=self.hostname, password=self.password)
                print parallel_task
                parallel_task.run()
            else:
                assert 0, 'mode should be wither "local", "sge" or "xgrid"'
            return True
        else:
            return False

    def executeDistributedTask(self, args):
        task = args.pop(0)
        category_flags = map(int, args.pop(0).split(','))
        assert len(category_flags) == len(args)
        arguments = [[], [], []]
        for i, a in enumerate(args):
           arguments[category_flags[i]].append(a)
#        input_files, output_files, extra_arguments = arguments
        tmp = list()
        for a in arguments[2]:
            t, s = a.split(':')
            tmp.append(__builtins__[t](s))
        arguments[2] = tmp
        if not len(arguments[-1]):
            arguments.pop()
        if len(arguments[0]) == 1:
            arguments[0] = arguments[0][0] # to fit ruffus convention        
        if len(arguments[1]) == 1:
            arguments[1] = arguments[1][0] # to fit ruffus convention        
        if len(arguments) == 3:
            arguments = arguments[:2] + arguments[2] # to fit ruffus convention        
        inspect.stack()[1][0].f_globals[task](*arguments)
#        inspect.stack()[1][0].f_globals[task](input_files, output_files, extra_arguments)
        ## locals()[task](input_files, output_files, extra_arguments)


# def sysCall(cmd, outputdirs=[], stdOutFile=None, stdErrFile=None):
#     if runOnSGE:
#         parallel_task = SGE.SGE(cmd)
#         parallel_task.wait()
#     elif runOnXgrid:
#         dependencies = XGrid.Dependencies(cmd)
#         parallel_task = XGrid.XGrid(cmd, dependencies)
#         parallel_task.wait()
#     else:
#         p = subprocess.Popen(cmd, env=os.environ, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
#         stdout, stderr = p.communicate()
#         _writeOutput(stdout, stderr, stdOutFile, stdErrFile)
# 
# 
# def _writeOutput(sout, serr, outf, errf):
#     if outf is not None:
#         outf.write(sout)
#     else:
#         f, path = tempfile.mkstemp(suffix='.stdout.xgrid')
#         f.write(sout)
#         
#     if errf is not None:
#         errf.write(serr)
#     else:
#         f, path = tempfile.mkstemp(suffix='.stderr.xgrid')
#         f.write(serr)

