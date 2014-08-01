#!/usr/bin/env python

"""
ElectreTri-rCClassAssignments - computes class assignments according to the
Electre TRI-C method.

This method uses central reference actions (profiles) instead of boundary
actions known from Electre TRI.

Usage:
    ElectreTri-rCClassAssignments.py -i DIR -o DIR

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
    assignments_as_intervals_to_xmcda,
    create_messages_file,
    get_dirs,
    get_error_message,
    get_input_data,
    write_xmcda,
)

__version__ = '0.2.0'


def assign_class(alternatives, categories_rank, categories_profiles, outranking, credibility):
    # sort categories by their rank, but we want the worst one on the 'left'- hence 'reverse=True'
    categories = [i[0] for i in sorted(categories_rank.items(),
                                       key=lambda x: x[1], reverse=True)]
    # get a list of profiles sorted accordingly to the above
    profiles = [i[0] for i in sorted(categories_profiles.items(),
                                     key=lambda x: categories.index(x[1]))]
    assignments_descending = []; assignments_ascending = []
    for a in alternatives:
        # direction: rank n <--- rank 1 (from the most preferred to the least preferred)
        found_descending = False
        for p in profiles[len(profiles) - 2:: -1]:
            p_next = profiles[profiles.index(p) + 1]
            if outranking[a][p] == 'preference' and credibility[a][p_next] > credibility[p][a]:
                category = categories_profiles.get(p_next)
                assignments_descending.append((a, category))
                found_descending = True
                break
        if not found_descending:
            # formally, here we make comparison with the 'worst' profile,
            # but since that always returns True, we just assign to C_h+1
            # (similar situation below - 'if not found_ascending...')
            assignments_descending.append((a, categories[0]))
        # direction: rank n ---> rank 1 (from the least preferred to the most preferred)
        found_ascending = False
        for p in profiles[1:]:
            p_prev = profiles[profiles.index(p) - 1]
            if outranking[p][a] == 'preference' and credibility[p_prev][a] > credibility[a][p]:
                category = categories_profiles.get(p_prev)
                assignments_ascending.append((a, category))
                found_ascending = True
                break
        if not found_ascending:
            assignments_ascending.append((a, categories[-1]))
    assignments = {}
    for i in zip(assignments_descending, assignments_ascending):
        assignments[i[0][0]] = (i[0][1], i[1][1])
    return assignments


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('categories.xml', False),
            ('categories_profiles.xml', False),
            ('credibility.xml', False),
            ('outranking.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'categories_rank',
            'credibility',
            'outranking',
        ]
        d = get_input_data(input_dir, filenames, params, comparison_with='central_profiles')

        assignments = assign_class(d.alternatives, d.categories_rank, d.categories_profiles,
                                   d.outranking, d.credibility)

        # serialization etc.
        xmcda_intervals = assignments_as_intervals_to_xmcda(assignments)
        write_xmcda(xmcda_intervals, os.path.join(output_dir, 'assignments.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())
