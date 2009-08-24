#!/usr/bin/env python

__author__ = "Rob Knight"
__copyright__ = "Copyright 2009, the PyCogent Project" #consider project name
__credits__ = ["Rob Knight","Greg Caporaso", "Kyle Bittinger"] #remember to add yourself if you make changes
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Rob Knight"
__email__ = "rob@spot.colorado.edu"
__status__ = "Prototype"

"""Contains code for picking representative set of seqs, several techniques.

This module has the responsibility for taking a set of OTU assignments and
a sequence file, and returning a set of sequences (one per OTU) labeled
with the OTU id (the original seq id and read id, and the count of identical
and/or prefix sequences, are stored as a comment in the fasta header).

This is heavily based on pick_otus.py.
"""

from optparse import OptionParser
from qiime.util import FunctionWithParams
from qiime.parse import fields_to_dict
from random import choice
from numpy import argmax
from cogent.util.misc import InverseDictMulti #inverts dict
from cogent.parse.fasta import MinimalFastaParser

label_to_name = lambda x: x.split()[0]

def first(items):
    """Returns first item from a list, used to fake random for testing."""
    return items[0]

def adapt_choice_f(choice_f):
    """Returns choice f that ignores second parameter so can use same API."""
    result = lambda ids, seqs='ignored': choice_f(ids)
    return result

first_id = adapt_choice_f(first)
random_id = adapt_choice_f(choice)

def longest_id(ids, seqs):
    """Chooses the longest seq from all seqs, uses first if ties."""
    lengths = map(len, [seqs.get(id_, '') for id_ in ids])
    return ids[argmax(lengths)]

def unique_id_map(seqs):
    """Returns map of seqs:unique representatives.
    
    Result is {orig_id:unique_rep_id}.
    """
    groups = InverseDictMulti(seqs)
    result = {}
    for v in groups.values():
        for i in v:
            result[i] = v[0]
    return result

#TODO: add unique including prefix matches, should keep longest that is
#free of low qual scores? and even truncate reads where the qual starts
#getting bad if can otherwise be rescued?

def make_most_abundant(seqs):
    """Makes function that chooses the most abundant seq from group"""
    seq_to_group = unique_id_map(seqs)
    groups = InverseDictMulti(seq_to_group)
    def most_abundant(ids, seqs='ignored'):
        """Returns most abundant seq from ids"""
        id_groups = [len(groups[seq_to_group[i]]) for i in ids]
        return ids[argmax(id_groups)]
    return most_abundant


class RepSetPicker(FunctionWithParams):
    """A RepSetPicker picks a representative set from a set of OTUs.

    This is an abstract class: subclasses should implement the __call__
    method.
    """
    
    Name = 'RepSetPicker'

    def __init__(self, params):
        """Return new RepSetPicker object with specified params.
        
        Note: expect params to contain both generic and per-method  params, 
        so leaving it as a dict rather than setting
        attributes. Some standard entries in params are:

        Algorithm: algorithm used (e.g. random, longest)
        Application: 3rd-party application used, if any
        """
        self.Params = params

    def __call__ (self, seq_path, otu_path, result_path=None, log_path=None):
        """Returns dict mapping {otu_id: seq} for each otu.
        
        Parameters:
        seq_path: path to file of sequences
        otu_path: path to file of otu assignments
        result_path: path to file of results. If specified, should
        dump the result to the desired path instead of returning it.
        log_path: path to log, which should include dump of params.
        """
        raise NotImplementedError, "RepSetPicker is an abstract class"


class GenericRepSetPicker(RepSetPicker):
    
    Name = 'GenericRepSetPicker'
    
    def __init__(self, params):
        """Return new RepSetPicker object with specified params.

        The GenericRepSetPicker allows any function such that
        f(list_of_ids, dict_of_id_to_seq) -> result. Remember
        to update the Algorithm and 
        
        params contains both generic and per-method (e.g. for
        cdhit application controller) params.
        
        Some generic entries in params are:
    
        Algorithm: algorithm used
        Application: 3rd-party application used
        """
        _params = {'Application':'None',
         'Algorithm':'random: "random choice from each OTU"',
         'ChoiceF':random_id,
         'ChoiceFRequiresSeqs':False
         }
        _params.update(params)
        RepSetPicker.__init__(self, _params)
    
    def __call__ (self, seq_path, otu_path, result_path=None, log_path=None):
        """Returns dict mapping {otu_id:[seq_ids]} for each otu.
        
        Parameters:
        seq_path: path to file of sequences
        otu_path: path to file of OTUs
        result_path: path to file of results. If specified,
        dumps the result to the desired path instead of returning it.
        log_path: path to log, which includes dump of params.
        """
        # Load the seq path. We may want to change that in the future 
        # to avoid the overhead of loading large sequence collections
        # during this step.
        seq_f = open(seq_path, 'U')
        seqs = dict(MinimalFastaParser(seq_f,label_to_name=label_to_name))
        seq_f.close()

        #Load the otu file
        otu_f = open(otu_path, 'U')
        otus = fields_to_dict(otu_f)
        otu_f.close()

        if self.Params['ChoiceFRequiresSeqs']:
            choice_f = self.Params['ChoiceF'](seqs)
        else:
            choice_f = self.Params['ChoiceF']

        #actually pick the set
        result = {}
        for set_id, ids in otus.items():
            result[set_id] = choice_f(ids, seqs)

        if result_path:
            # if the user provided a result_path, write the 
            # results to file with one tab-separated line per 
            # cluster
            of = open(result_path,'w')
            for cluster,id_ in sorted(result.items()):
                of.write('>%s %s\n%s\n' % (cluster, id_, seqs[id_]))
            of.close()
            result = None
            log_str = 'Result path: %s' % result_path
        else:
            # if the user did not provide a result_path, store
                # the result in a dict of {otu_id: rep_id},
            log_str = 'Result path: None, returned as dict.'
 
        if log_path:
            # if the user provided a log file path, log the run
            log_file = open(log_path,'w')
            log_file.write(str(self))
            log_file.write('\n')
            log_file.write('%s\n' % log_str)
    
        # return the result (note this is None if the data was
        # written to file)
        return result


def parse_command_line_parameters():
    """ Parses command line arguments """
    usage =\
     'usage: %prog [options]'
    version = 'Version: %prog ' +  __version__
    parser = OptionParser(usage=usage, version=version)

    parser.add_option('-m','--rep_set_picking_method',action='store',\
          type='string',dest='rep_set_picking_method',
          help='Method for picking'+\
          ' representative sets [default: %default]')
          
    parser.add_option('-o','--result_fp',action='store',\
          type='string',dest='result_fp',help='Path to store '+\
          'result file [default: <input_sequences_filepath>.otu]')
          
    parser.add_option('-l','--log_fp',action='store',\
          type='string',dest='log_fp',help='Path to store '+\
          'log file [default: No log file created.]')
          
    parser.add_option('-f','--fasta_file',action='store',\
          type='string',dest='fasta_fp',help='Path to read '+\
          'fasta file [required]')

    parser.add_option('-O','--otu_file',action='store',\
          type='string',dest='otu_fp',help='Path to read '+\
          'otu file [required]')
           
    parser.set_defaults(rep_set_picking_method='most_abundant')

    opts,args = parser.parse_args()

    return opts, args

rep_set_picking_methods = {
    'most_abundant':GenericRepSetPicker(params={'Algorithm':
            'most_abundant: picks most abundant sequence in OTU',
            'ChoiceF':make_most_abundant, 'ChoiceFRequiresSeqs':True}),
    'first':GenericRepSetPicker(params={'Algorithm':
            'first: picks first seq in output from each OTU',
            'ChoiceF':first_id}),
    'random':GenericRepSetPicker(params={'Algorithm':
            'random:picks seq at random from each OTU',
            'ChoiceF':random_id}),
    'longest':GenericRepSetPicker(params={'Algorithm':
            'longest:picks longest seq from each OTU',
            'ChoiceF':longest_id}),
}

if __name__ == "__main__":
    opts,args = parse_command_line_parameters()
    #verbose = opts.verbose
 
    rep_set_picker =\
     rep_set_picking_methods[opts.rep_set_picking_method]
     
    input_seqs_filepath = opts.fasta_fp

    input_otu_filepath = opts.otu_fp
   
    result_path = opts.result_fp or\
     '%s.otu' % input_seqs_filepath
     
    log_path = opts.log_fp
    
    rep_set_picker(input_seqs_filepath, input_otu_filepath,
     result_path=result_path,log_path=log_path)
    
    
