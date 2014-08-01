#!/usr/bin/env python

"""
ElectreTriClassAssignments - computes assignments according to the Electre TRI
method. It generates separate outputs for the conjuctive ('pessimistic') and
disjunctive ('optimistic') assignments.

Usage:
    ElectreTriClassAssignments.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory.
    -o DIR     Specify output directory.
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import traceback

from docopt import docopt

from common import (
    assignments_to_xmcda,
    create_messages_file,
    get_dirs,
    get_error_message,
    get_input_data,
    write_xmcda,
    Vividict,
)

__version__ = '0.2.0'


def assign_class(alternatives, categories_rank, categories_profiles, outranking):
    # sort categories by their rank, but we want the worst one on the 'left' - hence 'reverse=True'
    categories = [i[0] for i in sorted(categories_rank.items(), key=lambda x: x[1], reverse=True)]
    exploitation = Vividict()
    for alternative in alternatives:
        # conjuctive ('pessimistic' - from 'best' to 'worst')
        conjuctive_idx = 0
        for profile_idx, profile in list(enumerate(categories_profiles))[::-1]:  # .reverse()
            relation = outranking[alternative][profile]
            if relation in ('indifference', 'preference'):
                conjuctive_idx = profile_idx + 1
                break
            else:
                continue
        # disjunctive ('optimistic' - from 'worst' to 'best')
        disjunctive_idx = len(categories_profiles)
        for profile_idx, profile in enumerate(categories_profiles):
            relation = outranking[alternative][profile]
            if relation == 'none':  # 'reversed' preference, i.e. profile is preferred over alternative
                disjunctive_idx = profile_idx
                break
            else:
                continue
        exploitation[alternative] = (categories[conjuctive_idx], categories[disjunctive_idx])
    return exploitation


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('categories.xml', False),
            ('categories_profiles.xml', False),
            ('outranking.xml', False),
        ]
        params = [
            'alternatives',
            'categories_rank',
            'categories_profiles',
            'outranking',
        ]
        d = get_input_data(input_dir, filenames, params, comparison_with='boundary_profiles')

        assignments = assign_class(d.alternatives, d.categories_rank, d.categories_profiles,
                                   d.outranking)

        # uncomment this if you want output combined as a single file
        # xmcda_intervals = assignments_as_intervals_to_xmcda(assignments)
        # write_xmcda(xmcda_intervals, os.path.join(output_dir, 'assignments_intervals.xml'))
        assignments_conjuctive = {i[0]: i[1][0] for i in assignments.iteritems()}
        xmcda_conjuctive = assignments_to_xmcda(assignments_conjuctive)
        write_xmcda(xmcda_conjuctive, os.path.join(output_dir, 'assignments_conjuctive.xml'))
        assignments_disjunctive = {i[0]: i[1][1] for i in assignments.iteritems()}
        xmcda_disjunctive = assignments_to_xmcda(assignments_disjunctive)
        write_xmcda(xmcda_disjunctive, os.path.join(output_dir, 'assignments_disjunctive.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())
