#!/usr/bin/env python

__author__ = "justin kuczynski"
__copyright__ = "Copyright 2009, the PyCogent Project"
__credits__ = ["Rob Knight", "justin kuczynski"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "justin kuczynski"
__email__ = "justinak@gmail.com"
__status__ = "Prototype"


"""Contains tests for beta_metrics  functions."""
import os.path
import numpy
from cogent.util.unit_test import TestCase, main
from cogent.maths.unifrac.fast_unifrac import fast_unifrac
from qiime.parse import make_envs_dict
from qiime.beta_metrics import _reorder_unifrac_res, dist_unweighted_unifrac
from cogent.parse.tree import DndParser
from cogent.core.tree import PhyloNode

class FunctionTests(TestCase):
    def setUp(self):
        self.l19_data = numpy.array([
            [7,1,0,0,0,0,0,0,0],
            [4,2,0,0,0,1,0,0,0],
            [2,4,0,0,0,1,0,0,0],
            [1,7,0,0,0,0,0,0,0],
            [0,8,0,0,0,0,0,0,0],
            [0,7,1,0,0,0,0,0,0],
            [0,4,2,0,0,0,2,0,0],
            [0,2,4,0,0,0,1,0,0],
            [0,1,7,0,0,0,0,0,0],
            [0,0,8,0,0,0,0,0,0],
            [0,0,7,1,0,0,0,0,0],
            [0,0,4,2,0,0,0,3,0],
            [0,0,2,4,0,0,0,1,0],
            [0,0,1,7,0,0,0,0,0],
            [0,0,0,8,0,0,0,0,0],
            [0,0,0,7,1,0,0,0,0],
            [0,0,0,4,2,0,0,0,4],
            [0,0,0,2,4,0,0,0,1],
            [0,0,0,1,7,0,0,0,0]
            ])
        self.l19_sample_names = ['sam1', 'sam2', 'sam3', 'sam4', 'sam5','sam6',\
        'sam7', 'sam8', 'sam9', 'sam_middle', 'sam11', 'sam12', 'sam13', \
        'sam14', 'sam15', 'sam16', 'sam17', 'sam18', 'sam19']
        self.l19_taxon_names =  ['tax1', 'tax2', 'tax3', 'tax4', 'endbigtaxon',\
        'tax6', 'tax7', 'tax8', 'tax9']
        self.l19_treestr = '((((tax7:0.1,tax3:0.2):.98,tax8:.3, tax4:.3):.4, '+\
            '((tax1:0.3, tax6:.09):0.43,tax2:0.4):0.5):.2,'+\
            '(tax9:0.3, endbigtaxon:.08));'

    
    def test_reorder_unifrac_res(self):
        """ reorder should correctly reorder a misordered 3x3 matrix"""
        mtx = numpy.array([ [1,2,3],
                            [4,5,6],
                            [7,8,9]], 'float')
        unifrac_mtx = numpy.array([ [1,3,2],
                                    [7,9,8],
                                    [4,6,5]], 'float')
        sample_names = ['yo', "it's", "samples"]
        unifrac_sample_names = ['yo', "samples", "it's"]
        reordered_mtx = _reorder_unifrac_res([unifrac_mtx,unifrac_sample_names],
            sample_names)
        self.assertFloatEqual(reordered_mtx, mtx)
    
    def test_dist_unweighted_unifrac(self):
        """ exercise the unweighted unifrac metric"""
        tree = DndParser(self.l19_treestr, PhyloNode)
        res = dist_unweighted_unifrac(self.l19_data, self.l19_taxon_names, tree)
        envs = make_envs_dict(self.l19_data, self.l19_sample_names,
            self.l19_taxon_names)
        unifrac_mat, unifrac_names = \
            fast_unifrac(tree, envs, modes=['distance_matrix'])['distance_matrix']
        self.assertFloatEqual(res, _reorder_unifrac_res([unifrac_mat,
            unifrac_names], self.l19_sample_names))

#run tests if called from command line
if __name__ == '__main__':
    main()
