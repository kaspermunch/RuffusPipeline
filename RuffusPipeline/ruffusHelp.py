

##### parallel computations:

# one to one
@transform(PREVIOUSTASK, regex(fileRegex), outFile("tag%d" % TAG, outdir=RESULTDIR, suffix=SUFFIX), TAG)

# several to one (with all but one input being identical extras accross runs)
@transform(inputFiles, regex(fileRegex), add_inputs(["extra_file1", "extra_file2"]), outFile("tag"))

# several to one
@collate([PREVIOUSTASK1, PREVIOUSTASK2], regex(collateByTag('groupingtag')), CollatedOutputFiles("tag", "suffix"))

# several to several (using suffixes)
@collate([PREVIOUSTASK_1, PREVIOUSTASK_2], regex(collateByTag('groupingtag')), CollatedOutputFiles("tag", ["suffix1", "suffix2"]))

# one to several: (using suffixes)
@transform(inputFiles, regex(fileRegex), [outFile("tag", suffix="suffix1"), outFile("tag", suffix="suffix2")])

# one to unknown number
@split(PREVIOUSTASK, regex(fileRegex), outFileGlob("tag", outdir=RESULTDIR, suffix=SUFFIX))

# one (with an additional identical file for each task) to unknown number
@split(PREVIOUSTASK, regex(fileRegex), add_inputs("additional_file"), outFileGlob("tag", outdir=RESULTDIR, suffix=SUFFIX))

# several to glob
# One way to do this might be to make a CollatedGlob much like CollatedOutputFiles that
# merges inputfile names and tags and adds a * in the appropriate place. This should also
# work for just one input file so the functionaliry from outFileGlob is retained.



##### single computations (merges):

# many to one (uses a regex with one group matching everything)
@collate([PREVIOUSTASK], regex('.*(pickle).*'), CollatedOutputFiles("tag", ["suffix"]))
@collate([PREVIOUSTASK1, PREVIOUSTASK2], regex('.*(pickle).*'), CollatedOutputFiles("tag", "suffix"))

# many to several (uses a regex with one group matching everything)
@collate([PREVIOUSTASK], regex('.*(pickle).*'), CollatedOutputFiles("tag", ["suffix1", "suffix2"]))
@collate([PREVIOUSTASK1, PREVIOUSTASK2], regex('.*(pickle).*'), CollatedOutputFiles("tag", ["suffix1", "suffix2"]))


# FIXME: We should have a scheme using sentinel files in output so we can check if we have
# all the output files needed otherwise just specified as a glob outFileGlob could return
# a sentinel too like this [fileBaseName.sentinel, fileBaseName.*.suffix]. Then we could
# have a function getSentinelFile() that worked like get getOutputFile() to retrieve the
# sentinel file to write at the end of the task
