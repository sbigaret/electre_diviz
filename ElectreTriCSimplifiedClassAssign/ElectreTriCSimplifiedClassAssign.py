#!/usr/bin/env python

"""
ElectreTriCSimplifiedClassAssign - computes assignments according to the
simplified version of the Electre TRI-C method.

All the inputs and options are the same as in ElectreTriCClassAssign - the only
difference is in the assignment procedure (conditions are simplified).

Usage:
    ElectreTriCSimplifiedClassAssign.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   categories.xml
                   categoriesProfiles.xml
                   credibility.xml
                   cut_threshold.xml
    -o DIR     Specify output directory.
    --version  Show version.
    -h --help  Show this screen.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import os
import sys
import traceback

from docopt import docopt
from lxml import etree
import PyXMCDA as px

from common import (
    affectations_to_xmcda,
    check_cut_threshold,
    create_messages_file,
    get_categories_profiles_central,
    get_dirs,
    get_error_message,
    get_trees,
    getAlternativesComparisons,
    unreverseAltComparisons,
    write_xmcda,
)

__version__ = '0.1.0'


def assign_class(alternatives, categories_profiles, categories_rank, credibility, cut_threshold):
    uc = unreverseAltComparisons(credibility, alternatives, categories_profiles)
    credibility_ap, credibility_pa = uc

    # rank == 1 is the preferred category, hence 'reverse=True' below
    categories = OrderedDict(sorted(categories_rank.items(), key=lambda t: t[1], reverse=True))
    profiles_categories = {v: k for k, v in categories_profiles.items()}
    profiles = [profiles_categories[key] for key in categories.keys()]
    ass_des = []; ass_asc = []
    for a in alternatives:
        # direction: rank n <--- rank 1 (from the most preferred to the least preferred)
        found_desc = False
        for p in profiles[len(profiles) - 2:: -1]:
            p_next = profiles[profiles.index(p) + 1]
            if ((credibility_ap[a][p] >= cut_threshold and credibility_pa[a][p] < cut_threshold) and
                    (credibility_ap[a][p_next] > credibility_pa[a][p])):
                category = categories_profiles.get(p_next)
                ass_des.append((a, category))
                found_desc = True
                break
        if not found_desc:
            # formally, here we make comparison with the 'worst' profile,
            # but since that always returns True, we just assign to C_h+1
            # (similar situation below - 'if not found_asc...')
            ass_des.append((a, categories.keys()[0]))
        # direction: rank n ---> rank 1 (from the least preferred to the most preferred profile)
        found_asc = False
        for p in profiles[1:]:
            p_prev = profiles[profiles.index(p) - 1]
            if ((credibility_pa[a][p] >= cut_threshold and credibility_ap[a][p] < cut_threshold) and
                    (credibility_pa[a][p_prev] > credibility_ap[a][p])):
                category = categories_profiles.get(p_prev)
                ass_asc.append((a, category))
                found_asc = True
                break
        if not found_asc:
            ass_asc.append((a, categories.keys()[-1]))
    affectations = OrderedDict()
    for i in zip(ass_des, ass_asc):
        affectations[i[0][0]] = (i[0][1], i[1][1])  # (descending, ascending)
    return affectations


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'categories.xml',
        'categoriesProfiles.xml',
        'credibility.xml',
        'cut_threshold.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    categories = px.getCategoriesID(trees['categories'])
    categories_rank = px.getCategoriesRank(trees['categories'], categories)
    categories_profiles = get_categories_profiles_central(trees['categoriesProfiles'])
    credibility = getAlternativesComparisons(trees['credibility'], alternatives,
                                             categories_profiles)
    cut_threshold = px.getParameterByName(trees['cut_threshold'], 'cut_threshold')
    check_cut_threshold(cut_threshold)

    ret = {
        'alternatives': alternatives,
        'categories_rank': categories_rank,
        'categories_profiles': categories_profiles,
        'credibility': credibility,
        'cut_threshold': cut_threshold,
    }
    return ret


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        alternatives = input_data['alternatives']
        categories_profiles = input_data['categories_profiles']
        categories_rank = input_data['categories_rank']
        credibility = input_data['credibility']
        cut_threshold = input_data['cut_threshold']

        affectations =  assign_class(alternatives, categories_profiles,
                                     categories_rank, credibility, cut_threshold)

        affectations_xmcda = affectations_to_xmcda(affectations)
        write_xmcda(affectations_xmcda, os.path.join(output_dir, 'affectations.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())
