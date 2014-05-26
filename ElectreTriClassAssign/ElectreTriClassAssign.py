#!/usr/bin/env python

"""
ElectreTriClassAssign - computes assignments ("affectations") according to the
Electre TRI method.

This module (along with ElectreTriConcordance, ElectreTriDiscordances and
ElectreTriCredibility) is equal to ElectreTriExploitation module split into
four separate parts for user's convenience.

Usage:
    ElectreTriClassAssign.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
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
from copy import deepcopy
from itertools import chain
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


def assign_class(alternatives, categories_profiles, credibility, cut_threshold):

    def _get_profiles_ordering(last_found, profiles):
        """Gets the ordering of categories profiles."""
        for i in categories_profiles.values():
            if i.get('lower') == last_found:
                if i.get('upper') is None:
                    return
                profiles.append(i.get('upper'))
                last_found = profiles[-1]
                break
        _get_profiles_ordering(last_found, profiles)

    def _get_categories_ordering():
        categories_profiles_copy = deepcopy(categories_profiles)
        for profile in profiles:
            for category in categories_profiles_copy:
                if categories_profiles_copy[category].get('upper') == profile:
                    categories.append(category)
                    categories_profiles_copy.pop(category)
                    break
            for category in categories_profiles_copy:
                if categories_profiles_copy[category].get('lower') == profile:
                    if category != categories[-1]:
                        categories.append(category)
                        categories_profiles_copy.pop(category)
                    break

    def _get_relation(alternative, profile):
        c_ap = credibility[alternative][profile]
        c_pa = credibility[profile][alternative]
        if order == 'conjuctive':  # i.e. 'pessimistic'
            if c_ap >= cut_threshold and c_pa < cut_threshold:
                return 'pref'  # aPb
            elif c_ap >= cut_threshold and c_pa >= cut_threshold:
                return 'ind'  # indifference
        elif order == 'disjunctive':  # i.e. 'optimistic'
            if c_ap < cut_threshold and c_pa >= cut_threshold:
                return 'pref'  # bPa

    profiles = []
    _get_profiles_ordering(None, profiles)
    categories = []
    _get_categories_ordering()

    exploitation = OrderedDict.fromkeys(alternatives)
    for alternative in alternatives:
        order = 'conjuctive'  # (from 'best', i.e. b_n)
        for p in list(enumerate(profiles))[::-1]:
            relation = _get_relation(alternative, p[1])
            if relation == 'ind' or relation == 'pref':
                conjuctive = p[0] + 1
            else:
                conjuctive = 0
        order = 'disjunctive'  # (from 'worst', i.e. b_1)
        for p in enumerate(profiles):
            relation = _get_relation(alternative, p[1])
            if relation == 'pref':
                disjunctive = p[0]
            else:
                disjunctive = len(profiles)
        exploitation[alternative] = (categories[conjuctive], categories[disjunctive])
    return exploitation


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'categoriesProfiles.xml',
        'credibility.xml',
        'cut_threshold.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    cp_tree = trees['categoriesProfiles']
    categories = list(set(cp_tree.xpath('//categoriesProfiles//limits//categoryID/text()')))
    categories_profiles = px.getCategoriesProfiles(trees['categoriesProfiles'], categories)
    profiles_names = [p for p in cp_tree.xpath('//categoriesProfiles//alternativeID/text()')]
    credibility = getAlternativesComparisons(trees['credibility'], alternatives, profiles_names)
    cut_threshold = px.getParameterByName(trees['cut_threshold'], 'cut_threshold')
    check_cut_threshold(cut_threshold)

    ret = {
        'alternatives': alternatives,
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
        credibility = input_data['credibility']
        cut_threshold = input_data['cut_threshold']

        affectations = assign_class(alternatives, categories_profiles, credibility,
                                    cut_threshold)

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
