
# class Error(Exception):
#     """
#     Base class for exceptions in this module.
#     """
#     pass
# 
# class FormatError(Error):
#     """
#     Exception raised for errors in interaction with formatting.
# 
#     Attributes:
#         expression: input expression in which
#                     the error occurred
#         message:    explanation of the error
#     """
#     def __init__(self, expression, message):
#         self.message = expression
#         self.message = message
#         print self.expression, ": ", self.message
# 
# class InputError(Error):
#     """
#     Exception raised for errors in interaction with formatting.
# 
#     Attributes:
#         expression: input expression in which
#                     the error occurred
#         message:    explanation of the error
#     """
#     def __init__(self, expression, message):
#         self.message = expression
#         self.message = message
#         print self.expression, ": ", self.message
# 
# class SGEError(Error):
#     """
#     Exception raised for errors in interaction with SGE.
# 
#     Attributes:
#         expression: input expression in which
#                     the error occurred
#         message:    explanation of the error
#     """
#     def __init__(self, expression, message):
#         self.message = expression
#         self.message = message
#         print self.expression, ": ", self.message
# 
# class SGE(object):
# 
#     def __init__(self, cmd):
#         self.cmd = cmd
#         self.jobName = '_'  + ''.join([random.choice(string.letters + string.digits) for x in range(5)])
#         self.outErrDir = tempfile.mkdtemp(suffix="_sge_%s" % self.jobName)
#         self.outputBaseName = os.path.join(self.outErrDir, self.jobName)
# 
#     def run(self):
#         self._qsub(cmd)
#         self.wait()
# 
#     def wait(self, stdout=None, stderr=None):
#         while True:
#             nrJobs = self._qstat()
#             if nrJobs > 1:
#                 raise SGEError(self.jobName, "More than one job with same job name")
#             if nrJobs == 1:
#                 time.sleep(10)
#         os.unlink(self.tmpFileName)
#         self._redirectOutput(stdout, stderr)
#         shutil.rmtree(self.outErrDir)
# 
#     def _redirectOutput(self, stdout, stderr):
# 
#         stdoutFile = open(self.outputBaseName + ".stdout")
#         if stdout is None:
#             sys.stdout.write(stdoutFile.read())
#         else:
#             f = open(stdout, 'w')
#             f.write(stdoutFile.read())
#             f.close()    
#         stdoutFile.close()
# 
#         stderrFile = open(self.outputBaseName + ".stderr")
#         if stderr is None:
#             sys.stderr.write(stderrFile.read())
#         else:
#             f = open(stderr, 'w')
#             f.write(stderrFile.read())
#             f.close()    
#         stderrFile.close()
# 
#     def _qsub(self, cmd):
#         qsubString, self.tmpFileName = self._writeShellScript(cmd)
#         s = subprocess.Popen(qsubString, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         output, error = s.communicate()
# #         fp = os.popen(qsubString)
# #         output = ""
# #         for l in fp:
# #             output += l
# #         #output = fp.read()
# #         fp.close()
#         m = re.search(r'Your job (\d+)', output)
#         if m:
#             self.jobid = m.group(1)
#         else:
#             raise QsubError(output, "could not capture job id")
# 
# 
#     def _qstat(self):
#         s = subprocess.Popen("qstat", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         fp = os.popen("qstat")
#         jobNameRe = re.compile("\s+%s\s+" % self.jobName)
#         nrJobs = 0
#         for line in fp.readlines():
#             match = jobNameRe.search(line)
#             if match:
#                 nrJobs += 1
#         fp.close()
#         return nrJobs
#         
#     def _writeShellScript(self, cmd):
#         exePath = cmd.split(' ', 1)[0][0]
#         if exePath[0] == '~' or os.path.abspath(exePath) == exePath:
#             shellString = "#!/bin/sh\n#$ -N %s\n#$ -o %s\n#$ -cwd\n#$ -V\n%s ; /bin/echo $? > %s.retval\n" % (self.jobName, self.outputBaseName, cmd, self.outputBaseName)
#         else:
#             if len(cmd.split(' ', 1)) == 2:
#                 shellString = "#!/bin/sh\n#$ -N %s\n#$ -o %s\n#$ -cwd\n#$ -V\n`which %s` %s\n/bin/echo $? > %s.retval\n" % (self.jobName, self.outputBaseName, cmd.split(' ', 1)[0], cmd.split(' ', 1)[1], self.outputBaseName)
#             else:
#                 shellString = "#!/bin/sh\n#$ -N %s\n#$ -o %s\n#$ -cwd\n#$ -V\n`which %s`\n/bin/echo $? > %s.retval\n" % (self.jobName, self.outputBaseName, cmd, self.outputBaseName)
# 
#         tmpFile, tmpFileName = tempfile.mkstemp(suffix=".sge_%s" % self.jobName)
#         tmpFile.write(shellString)
#         tmpFile.close()
#         qsubString = "qsub %s %s" % (self.qsubArgs, tmpFileName)
#         return qsubString, tmpFileName
#                 
# #         chars = string.letters + string.digits
# #         tmpFileName = "/tmp/job_%s." % self.jobName
# #         for i in range(7):
# #             tmpFileName += random.choice(chars)        
# #         fp = open(tmpFileName, 'w')
# #         fp.write(shellString)
# #         fp.close()
# #         qsubString = "qsub %s %s" % (self.qsubArgs, tmpFileName)
# #         return qsubString, tmpFileName

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

class SGEError(Error):
    """
    Exception raised for errors in interaction with SGE.

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

class SGE(object):

    def __init__(self, cmd):
        self.cmd = cmd
        self.jobName
        self.qsub(cmd)
        self.wait

    def wait(self):
        while True:
            nrJobs = self._qstat()
            if nrJobs > 1:
                raise SGEError(self.jobName, "More than one job with same job name")
            if nrJobs == 1:
                time.sleep(10)

    def _qsub(self, cmd):
        qsubString, tmpFileName = self._writeShellScript(cmd)
        #fp = subprocess.Popen(qsubString, shell=True, stdout=subprocess.PIPE).stdout
        fp = os.popen(qsubString)
        output = ""
        for l in fp:
            output += l
        #output = fp.read()
        fp.close()
        m = re.search(r'Your job (\d+)', output)

    def _qstat(self):
        #fp = subprocess.Popen("qstat", shell=True, stdout=subprocess.PIPE).stdout
        fp = os.popen("qstat")
        jobNameRe = re.compile("\s+%s\s+" % self.jobName)
        nrJobs = 0
        for line in fp.readlines():
            match = jobNameRe.search(line)
            if match:
                nrJobs += 1
        fp.close()
        return nrJobs
        
    def _writeShellScript(self, cmd):
        exePath = cmd.split(' ', 1)[0][0]
        if exePath[0] == '~' or os.path.abspath(exePath) == exePath:
            shellString = "#!/bin/sh\n#$ -N %s\n#$ -o $JOB_NAME.$JOB_ID\n#$ -cwd\n#$ -V\n%s ; /bin/echo $? > $JOB_NAME.$JOB_ID.retval\n" % (self.jobName, cmd)
        else:
            if len(cmd.split(' ', 1)) == 2:
                shellString = "#!/bin/sh\n#$ -N %s\n#$ -o $JOB_NAME.$JOB_ID\n#$ -cwd\n#$ -V\n`which %s` %s\n/bin/echo $? > $JOB_NAME.$JOB_ID.retval\n" % (self.jobName, cmd.split(' ', 1)[0], cmd.split(' ', 1)[1])
            else:
                shellString = "#!/bin/sh\n#$ -N %s\n#$ -o $JOB_NAME.$JOB_ID\n#$ -cwd\n#$ -V\n`which %s`\n/bin/echo $? > $JOB_NAME.$JOB_ID.retval\n" % (self.jobName, cmd)
            #shellString = "#!/bin/sh\n#$ -N %s\n#$ -o $JOB_NAME.$JOB_ID\n#$ -cwd\n#$ -V\n`which %s` %s\n/bin/echo $? > $JOB_NAME.$JOB_ID.retval\n" % (self.jobName, cmd.split(' ', 1)[0], cmd.split(' ', 1)[1])
            
        chars = string.letters + string.digits
        tmpFileName = "/tmp/job_%s." % self.jobName
        for i in range(7):
            tmpFileName += random.choice(chars)        
        fp = open(tmpFileName, 'w')
        fp.write(shellString)
        fp.close()
        qsubString = "qsub %s %s" % (self.qsubArgs, tmpFileName)
        return qsubString, tmpFileName

# 
# class HTF(SGE):
# 
#     
