
import os, sys, inspect, time, re, inspect
from collections import defaultdict
from itertools import izip, chain

# ALL INITIAL FILES SHOULD START OUT WITH THE PROPER NAMING CONVENTION: There should be
# only one dot (preceeding the suffix) unless the file name contains a chomosome name then
# it should be name.chr1.tsv

#<name without .>.<tags possibly with . and joined by _><.tsv>

# everytime a task is performed on a file we add a tag like this:
# e.g. after task1:
#/path/file_name.task1.tsv
# e.g. after task2:
#/path/file_name.task2_task1.tsv
# note that we append new tags at the beginning at the tag string between the first and last .
# This is to allow globbing of all files sharing only some set of tags e.g. /path/file_name.task1.chr*.tsv

# fileRegex = r'(.*?/?)([^./]+\.?)([^/]*)(\.[^./]*)$'
# # >>> re.search(r'(.*?/?)([^./]+\.?)([^/]*)(\.[^./]*)$', '/path/name_chr22.tag3_tag23.4.tsv').groups()
# # ('/path/', 'name_chr22.', 'tag3_tag23.4', '.tsv')

#fileRegex = r'(.*?/?)([^./]+)(\.?[^/]*)(\.[^./]*)$'
fileRegex = r'(.*?/?)([^./]+\.)([^/]*?\.?)([^.]*)$'

def writeSentinel(outp):
    with open(outp, 'w') as f:
        pass

def floatToTag(f):
    s = "%.2f" % f
    return s.replace('.', '')

def pathToTag(p):
    return os.path.splitext(os.path.basename(p))[0]


def outFile(tag, suffix="", outdir=""):
    assert not re.match('\d', tag)
    tag = tag.replace('.', '')
    if outdir:
        if not outdir.endswith('/'):
            outdir += '/'
    else:
        outdir = r"\1"
    if not suffix:
        suffix = r"\4"
    if tag == '':
        return r"%s\2\3%s" % (outdir, suffix)
    else:
        return r"%s\2%s.\3%s" % (outdir, tag, suffix)


def outFileGlob(tagPrefix, suffix="", outdir=""):

    tagPrefix = tagPrefix.replace('.', '')
    if outdir:
        if not outdir.endswith('/'):
            outdir += '/'
    else:
        outdir = r"\1"
    if not suffix:
        suffix = r"\4"
    return r"%s\2%s*.\3%s" % (outdir, tagPrefix, suffix)


def collateByTag(tag):
    return r'.*(%s[^.]*).*' % tag


def getOutputFileName(inputFileName, tag, identifier, outdir="", suffix=""):
    if type(tag) in (list, tuple):
        tag = '.'.join([x.replace('.', '') for x in tag])
    tag = tag.replace('.', '')
    identifier = identifier.replace('.', '')
    return re.sub(fileRegex, outFileGlob(tag, outdir=outdir, suffix=suffix), inputFileName).replace('*', identifier)


class CollatedOutputFiles(object):

    def __init__(self, tag, suffix, outdir="", groupDepth=0):
        self.tag = tag
        self.outdir = outdir
        self.groupDepth = groupDepth
        if isinstance(suffix, list):
            self.suffix = suffix
        else:
            self.suffix = [suffix]

    def _flatten(self, lst):
        for elem in lst:
            if type(elem) in (tuple, list):
                for i in self._flatten(elem):
                    yield i
            else:
                yield elem

    def _longest_substr(self, data):
        substr = ''
        if len(data) > 1 and len(data[0]) > 0:
            for i in range(len(data[0])):
                for j in range(len(data[0])-i+1):
                    if j > len(substr) and self._is_substr(data[0][i:i+j], data):
                        substr = data[0][i:i+j]
        return substr

    def _is_substr(self, find, data):
        if len(data) < 1 and len(find) < 1:
            return False
        for i in range(len(data)):
            if find not in data[i]:
                return False
        return True

    def _summarizeValues(self, subvals, spacer):
        li = list()
        si = list()
        for v in subvals:
            try:
                li.append(int(v))
            except ValueError:
                si.append(v)
        li.sort()
        si.sort()
        toRemove = [y for x, y, z in izip(chain((None, None), li), chain((None,), li), li) if x == z-2 and y == z-1]

        substlst = list()
        for x in li:
            if x in set(toRemove):
                substlst.append('-')
            else:
                substlst.append(str(x))
        newValue = re.sub(r'(_-)+_', '-', spacer.join(substlst))
        #newValue = "-".join(map(str, [x for x in li if x not in set(toRemove)]))

        if li and si:
            newValue += spacer
        newValue += spacer.join(si)
        return newValue

    def _parseNameList(self, inp):

        def parseSuffixGroup(inp):
            original_inp_length = len(inp)

            tags = []
            names = set()
            suffixes = set()
            for match in (re.search(fileRegex, x) for x in sorted(inp)):
                path = match.group(1)
                n = match.group(2).replace('.', '')
                names.add(n)
                t = match.group(3)[0:-1]

                tags.append(t)

                suffixes.add(match.group(4))

            # summarize tags if possible
            d = dict()
            for t in tags:
                for k in t.split('.'):
                    if k not in d:
                        d[k] = 0
                    d[k] += 1

            commons = [k for k in d if not d[k] % (original_inp_length/len(suffixes))] # tags that every file has
            uniques = [k for k in d if d[k] == len(names) * len(suffixes)]  # tags that make files with a certain name+suffix unique        

            ## print len(names) * len(suffixes)
            ## print 'original_inp_length', original_inp_length
            ## print 'NAMES', names
            ## print 'UNIQUE', uniques
            ## print 'COMMONS', commons
            ## print len(d)
            ## for k, v in d.items():
            ##     print k, v


            if len(d) == len(commons + uniques):  # if there are only these two kinds
                commonPrefix = os.path.commonprefix(uniques)
                commonSuffix = os.path.commonprefix([u[::-1] for u in uniques])[::-1]
                regex = re.compile(r'%s(.*)%s' % (commonPrefix, commonSuffix))
                values = [regex.search(u).group(1) for u in uniques]

                spacer = self._longest_substr(values)
                spacer = '_'
                if spacer and not re.match(r'\d+', spacer):
                    subvalList = [v.split(spacer) for v in values]
                else:
                    subvalList = [values]

                sd = dict()
                for l in subvalList:
                    sd.setdefault(spacer.join(l[0:-1]), []).append(l[-1])

                newValueList = list()
                for k, v in sd.items():
                    newValueList.append(k + self._summarizeValues(v, spacer))
                dbspacer = spacer * 2
                newValue = dbspacer.join(newValueList)

                if len(newValue) > 30:
                    newValue = 'HASH%d' % hash(newValue)

                tags = [re.sub(r'%s([^.]*)%s' % (commonPrefix, commonSuffix), commonPrefix + newValue + commonSuffix, tags[0])]


            # summarize names if possible
            commonPrefix = os.path.commonprefix(names)
            commonSuffix = os.path.commonprefix([u[::-1] for u in names])[::-1]
            regex = re.compile(r'%s(.*)%s' % (commonPrefix, commonSuffix))
            try:
                values = [regex.search(u).group(1) for u in names]
            except AttributeError:
                values = []
            if len(values) == len(names):
                names = [commonPrefix + self._summarizeValues(values, '_') + commonSuffix]


            return (names, set(tags), suffixes)


        # devide into groups based on suffix:
        suffixGroups = defaultdict(list)
        for fileName, suffix in ((x, os.path.splitext(x)[1]) for x in inp):
            suffixGroups[suffix].append(fileName)
            
        # parse each group seperately and add results to sets
        names = set()
        tags = set()
        suffixes = set()
        for gr in suffixGroups.values():
            n, t, s = parseSuffixGroup(gr)
            names.update(n)
            tags.update(t)
            suffixes.update(s)

        # parse tag sets to make sure there are no redunancies:
        new_tags = set()
        for t in tags:
            if not any(t in x and t != x for x in tags):
                new_tags.add(t)
        tags = new_tags
            
        return (names, tags, suffixes)

    def _parse(self, lst, expandDepth):

        if not expandDepth:
            return self._parseNameList(list(self._flatten(lst)))
        else:
            expandDepth -= 1
            
        names, tags, suffixes = set(), set(), set()
        for l in lst:
            if type(l) in (tuple, list):
                n, t, s = self._parse(l, expandDepth)
            else:
                n, t, s = self._parseNameList([l])

            names.update(n)
            suffixes.update(s)            
            for y in t:
                if not any((y in x for x in tags)):
                    for x in tags:
                        if x in y:
                            tags.remove(x)
                            break                    
                    tags.add(y)

        return names, tags, suffixes                    
            
    def getOutputFile(self, inp):
        assert isinstance(inp, list) or isinstance(inp, tuple)

        names, tags, suffixes = self._parse(inp, self.groupDepth)

        if self.outdir:
            path = self.outdir
        else:
            lst = list(self._flatten(inp))
            # check that all dirnames are the same
            assert all(os.path.dirname(lst[0]) == os.path.dirname(l) for l in lst)
            path = os.path.dirname(lst[0])

        # remove empty strings:
        tags = [x for x in tags if x]

        # make list of output names
        if tags:
            outp = [os.path.join(path,  "_".join(list(names)) + ".%s." % self.tag + ".".join(sorted(set(tags))) + "." + suffix) for suffix in self.suffix]
        else:
            outp = [os.path.join(path,  "_".join(list(names)) + ".%s." % self.tag + suffix) for suffix in self.suffix]

        # turn into string if list has one filename
        if len(outp) == 1:
            outp = outp[0]

        assert outp not in inp
        return outp
