#!/usr/bin/env python

"""
ElectreTriClassAssignments - computes assignments according to the Electre TRI
method. It generates separate outputs for the conjuctive ('pessimistic') and
disjunctive ('optimistic') assignments.

Usage:
    ElectreTriClassAssignments.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   classes.xml
                   classes_profiles.xml
                   outranking.xml
    -o DIR     Specify output directory. Files generated as output:
                   assignments_conjuctive.xml
                   assignments_disjunctive.xml
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

from common import assignments_to_xmcda, create_messages_file, get_dirs, \
    get_error_message, get_input_data, get_relation_type, write_xmcda, Vividict

__version__ = '0.2.0'


def assign_class(alternatives, categories_rank, categories_profiles,
                 outranking):
    # sort categories by their rank, but we want the worst one on the 'left'
    # - hence 'reverse=True'
    categories = [i[0] for i in sorted(categories_rank.items(),
                                       key=lambda x: x[1], reverse=True)]
    exploitation = Vividict()
    for alternative in alternatives:
        # conjuctive ('pessimistic' - from 'best' to 'worst')
        conjuctive_idx = 0
        for profile_idx, profile in list(enumerate(categories_profiles))[::-1]:
            relation = get_relation_type(alternative, profile, outranking)
            if relation in ('indifference', 'preference'):
                conjuctive_idx = profile_idx + 1
                break
            else:
                continue
        # disjunctive ('optimistic' - from 'worst' to 'best')
        disjunctive_idx = len(categories_profiles)
        for profile_idx, profile in enumerate(categories_profiles):
            relation = get_relation_type(profile, alternative, outranking)
            if relation == 'preference':
                disjunctive_idx = profile_idx
                break
            else:
                continue
        exploitation[alternative] = (categories[conjuctive_idx],
                                     categories[disjunctive_idx])
    return exploitation


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('classes.xml', False),
            ('classes_profiles.xml', False),
            ('outranking.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'categories_rank',
            'outranking',
        ]
        d = get_input_data(input_dir, filenames, params,
                           comparison_with='boundary_profiles')

        assignments = assign_class(d.alternatives, d.categories_rank,
                                   d.categories_profiles, d.outranking)

        # uncomment this if you want output combined as a single file (and
        # remember to import assignments_as_intervals_to_xmcda):
        # xmcda_intervals = assignments_as_intervals_to_xmcda(assignments)
        # write_xmcda(xmcda_intervals,
        #             os.path.join(output_dir, 'assignments_intervals.xml'))
        assignments_con = {i[0]: i[1][0] for i in assignments.iteritems()}
        xmcda_con = assignments_to_xmcda(assignments_con)
        write_xmcda(xmcda_con, os.path.join(output_dir,
                                            'assignments_conjuctive.xml'))
        assignments_dis = {i[0]: i[1][1] for i in assignments.iteritems()}
        xmcda_dis = assignments_to_xmcda(assignments_dis)
        write_xmcda(xmcda_dis, os.path.join(output_dir,
                                            'assignments_disjunctive.xml'))
        create_messages_file(None, ('Everything OK.',), output_dir)
        return 0
    except Exception, err:
        err_msg = get_error_message(err)
        log_msg = traceback.format_exc()
        print(log_msg.strip())
        create_messages_file((err_msg, ), (log_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())
