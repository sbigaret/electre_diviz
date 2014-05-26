#!/usr/bin/env python

from collections import OrderedDict
import unittest

from networkx import DiGraph

from ElectreIsFindKernel.ElectreIsFindKernel import build_graph, find_kernel
from ElectreIVCredibility.ElectreIVCredibility import get_credibility as get_credibility_iv
from ElectreTriCClassAssign.ElectreTriCClassAssign import assign_class as assign_class_tri_c
from ElectreIsDiscordanceBinary.ElectreIsDiscordanceBinary import get_discordances, aggregate_discordances
from ElectreTriClassAssign.ElectreTriClassAssign import assign_class as assign_class_tri
from ElectreTriCredibility.ElectreTriCredibility import get_credibility as get_credibility_tri


class TestElectreIsFindKernel(unittest.TestCase):

    def get_sample_graphs(self):
        def _g6_add_weights(g6):
            edges = [(0, 4), (1, 2), (2, 3), (3, 1), (4, 0), (6, 2), (6, 4)]
            #weights = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
            weights = [0.7, 0.9, 0.7, 0.5, 0.9, 0.8, 0.5]
            for i, edge in enumerate(edges, 0):
                g6.edge[edge[0]][edge[1]]['weight'] = weights[i]
            return g6

        g1 = DiGraph([(0, 1), (1, 3), (3, 2), (6, 4), (6, 5)])
        g2 = DiGraph([(0, 3), (1, 4), (3, 1), (3, 2), (4, 2)])
        g2.add_node(5)
        g3 = DiGraph([(0, 1), (1, 2)])
        g4 = DiGraph([(0, 2), (0, 3), (1, 4), (3, 2), (3, 1), (4, 2)])
        g5 = DiGraph([(0, 2), (2, 3), (3, 0), (4, 1), (4, 2)])
        g6 = DiGraph([(0, 4), (1, 2), (2, 3), (3, 1), (4, 0), (6, 2), (6, 4)])
        g6.add_node(5)
        g6 = _g6_add_weights(g6)
        # with self loops and cycles
        uni = DiGraph([
            (0, 0), (0, 6),
            (1, 0), (1, 1), (1, 3), (1, 6), (1, 9),
            (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 9),
            (3, 0), (3, 3), (3, 6),
            (4, 0), (4, 1), (4, 3), (4, 4), (4, 6), (4, 7), (4, 9),
            (5, 0), (5, 1), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 9),
            (6, 0), (6, 3), (6, 6),
            (7, 0), (7, 1), (7, 3), (7, 6), (7, 7), (7, 9),
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9),
            (9, 0), (9, 1), (9, 3), (9, 6), (9, 9)
        ])
        # without self loop but with cycles
        uni2 = DiGraph([
            (0, 6),
            (1, 0), (1, 3), (1, 6), (1, 9),
            (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 9),
            (3, 0), (3, 6),
            (4, 0), (4, 1), (4, 3), (4, 6), (4, 7), (4, 9),
            (5, 0), (5, 1), (5, 3), (5, 4), (5, 6), (5, 7), (5, 9),
            (6, 0), (6, 3),
            (7, 0), (7, 1), (7, 3), (7, 6), (7, 9),
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 9),
            (9, 0), (9, 1), (9, 3), (9, 6)
        ])
        # without self loops and cycles
        uni3 = DiGraph([
            (1, 0), (1, 3), (1, 6),
            (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 9),
            (3, 0),
            (4, 0), (4, 1), (4, 3), (4, 6), (4, 7), (4, 9),
            (5, 0), (5, 1), (5, 3), (5, 4), (5, 6), (5, 7), (5, 9),
            (6, 0),
            (7, 0), (7, 1), (7, 3), (7, 6), (7, 9),
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 9),
            (9, 0), (9, 1), (9, 3), (9, 6)
        ])
        sample_graphs = {
            'g1': g1,
            'g2': g2,
            'g3': g3,
            'g4': g4,
            'g5': g5,
            'g6': g6,
            'uni': uni,
            'uni2': uni2,
            'uni3': uni3,
        }
        return sample_graphs

    def setUp(self):
        self.sample_graphs = self.get_sample_graphs()
        self.alternatives = ['APS', 'AWF', 'PW', 'PWT', 'SGGW', 'SGH', 'SGSP', 'UKSW', 'UW', 'WAT']
        self.cut_threshold = 1.0
        self.eliminate_cycles_method = 'aggregate'
        self.outranking = {
            'APS': {'APS': 1.0, 'AWF': 0.0, 'PW': 0.0, 'PWT': 0.0, 'SGGW': 0.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 0.0, 'UW': 0.0, 'WAT': 0.0},
            'AWF': {'APS': 1.0, 'AWF': 1.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 0.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 0.0, 'UW': 0.0, 'WAT': 1.0},
            'PW': {'APS': 1.0, 'AWF': 1.0, 'PW': 1.0, 'PWT': 1.0, 'SGGW': 1.0, 'SGH': 1.0, 'SGSP': 1.0, 'UKSW': 1.0, 'UW': 0.0, 'WAT': 1.0},
            'PWT': {'APS': 1.0, 'AWF': 0.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 0.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 0.0, 'UW': 0.0, 'WAT': 0.0},
            'SGGW': {'APS': 1.0, 'AWF': 1.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 1.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 1.0, 'UW': 0.0, 'WAT': 1.0},
            'SGH': {'APS': 1.0, 'AWF': 1.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 1.0, 'SGH': 1.0, 'SGSP': 1.0, 'UKSW': 1.0, 'UW': 0.0, 'WAT': 1.0},
            'SGSP': {'APS': 1.0, 'AWF': 0.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 0.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 0.0, 'UW': 0.0, 'WAT': 0.0},
            'UKSW': {'APS': 1.0, 'AWF': 1.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 0.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 1.0, 'UW': 0.0, 'WAT': 1.0},
            'UW': {'APS': 1.0, 'AWF': 1.0, 'PW': 1.0, 'PWT': 1.0, 'SGGW': 1.0, 'SGH': 1.0, 'SGSP': 1.0, 'UKSW': 1.0, 'UW': 1.0, 'WAT': 1.0},
            'WAT': {'APS': 1.0, 'AWF': 1.0, 'PW': 0.0, 'PWT': 1.0, 'SGGW': 0.0, 'SGH': 0.0, 'SGSP': 1.0, 'UKSW': 0.0, 'UW': 0.0, 'WAT': 1.0}
        }

    def test_build_graph(self):
        expected_graph = {0: 'APS', 1: 'AWF', 2: 'PW', 3: 'PWT', 4: 'SGGW', 5: 'SGH', 6: 'SGSP', 7: 'UKSW', 8: 'UW', 9: 'WAT'}
        expected_nodes = [(0, {}), (1, {}), (2, {}), (3, {}), (4, {}), (5, {}), (6, {}), (7, {}), (8, {}), (9, {})]
        expected_edges = [
            (0, 0, {'weight': 1.0}),
            (0, 6, {'weight': 1.0}),
            (1, 0, {'weight': 1.0}),
            (1, 1, {'weight': 1.0}),
            (1, 3, {'weight': 1.0}),
            (1, 6, {'weight': 1.0}),
            (1, 9, {'weight': 1.0}),
            (2, 0, {'weight': 1.0}),
            (2, 1, {'weight': 1.0}),
            (2, 2, {'weight': 1.0}),
            (2, 3, {'weight': 1.0}),
            (2, 4, {'weight': 1.0}),
            (2, 5, {'weight': 1.0}),
            (2, 6, {'weight': 1.0}),
            (2, 7, {'weight': 1.0}),
            (2, 9, {'weight': 1.0}),
            (3, 0, {'weight': 1.0}),
            (3, 3, {'weight': 1.0}),
            (3, 6, {'weight': 1.0}),
            (4, 0, {'weight': 1.0}),
            (4, 1, {'weight': 1.0}),
            (4, 3, {'weight': 1.0}),
            (4, 4, {'weight': 1.0}),
            (4, 6, {'weight': 1.0}),
            (4, 7, {'weight': 1.0}),
            (4, 9, {'weight': 1.0}),
            (5, 0, {'weight': 1.0}),
            (5, 1, {'weight': 1.0}),
            (5, 3, {'weight': 1.0}),
            (5, 4, {'weight': 1.0}),
            (5, 5, {'weight': 1.0}),
            (5, 6, {'weight': 1.0}),
            (5, 7, {'weight': 1.0}),
            (5, 9, {'weight': 1.0}),
            (6, 0, {'weight': 1.0}),
            (6, 3, {'weight': 1.0}),
            (6, 6, {'weight': 1.0}),
            (7, 0, {'weight': 1.0}),
            (7, 1, {'weight': 1.0}),
            (7, 3, {'weight': 1.0}),
            (7, 6, {'weight': 1.0}),
            (7, 7, {'weight': 1.0}),
            (7, 9, {'weight': 1.0}),
            (8, 0, {'weight': 1.0}),
            (8, 1, {'weight': 1.0}),
            (8, 2, {'weight': 1.0}),
            (8, 3, {'weight': 1.0}),
            (8, 4, {'weight': 1.0}),
            (8, 5, {'weight': 1.0}),
            (8, 6, {'weight': 1.0}),
            (8, 7, {'weight': 1.0}),
            (8, 8, {'weight': 1.0}),
            (8, 9, {'weight': 1.0}),
            (9, 0, {'weight': 1.0}),
            (9, 1, {'weight': 1.0}),
            (9, 3, {'weight': 1.0}),
            (9, 6, {'weight': 1.0}),
            (9, 9, {'weight': 1.0})
        ]
        graph = build_graph(self.alternatives, self.outranking, self.cut_threshold)
        self.assertEqual(graph.graph, expected_graph)
        self.assertEqual(graph.nodes(data=True), expected_nodes)
        self.assertEqual(graph.edges(data=True), expected_edges)

    def test_find_kernel_g1(self):
        expected = [0, 3, 6]
        found, _ = find_kernel(self.sample_graphs['g1'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_g2(self):
        expected = [0, 1, 2, 5]
        found, _ = find_kernel(self.sample_graphs['g2'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_g3(self):
        expected = [0, 2]
        found, _ = find_kernel(self.sample_graphs['g3'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_g4(self):
        expected = [0, 1]
        found, _ = find_kernel(self.sample_graphs['g4'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_g5(self):
        expected = [4]
        found, _ = find_kernel(self.sample_graphs['g5'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_g6_aggregate(self):
        expected = [5, 6]
        found, _ = find_kernel(self.sample_graphs['g6'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_g6_cut_weakest(self):
        expected = [1, 3, 5, 6, 0]
        found, _ = find_kernel(self.sample_graphs['g6'], eliminate_cycles_method='cut_weakest')
        self.assertEqual(expected, found)

    def test_find_kernel_uni(self):
        expected = [8]
        found, _ = find_kernel(self.sample_graphs['uni'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_uni2(self):
        expected = [8]
        found, _ = find_kernel(self.sample_graphs['uni2'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)

    def test_find_kernel_uni3(self):
        expected = [8]
        found, _ = find_kernel(self.sample_graphs['uni3'], eliminate_cycles_method='aggregate')
        self.assertEqual(expected, found)


class TestElectreIvCredibility(unittest.TestCase):

    def setUp(self):
        self.criteria = ['power', 'safety', 'cost']
        self.performances = {
            'aut': {'safety': 8.0, 'cost': 800.0, 'power': 74.0},
            'bel': {'safety': 0.0, 'cost': 200.0, 'power': 58.0},
            'fra': {'safety': 6.0, 'cost': 800.0, 'power': 98.0},
            'ger': {'safety': 7.0, 'cost': 400.0, 'power': 66.0},
            'ita': {'safety': 4.0, 'cost': 600.0, 'power': 90.0}
        }
        self.pref_directions = {'safety': 'max', 'cost': 'min', 'power': 'max'}
        self.thresholds = {
            'safety': {'indifference': 1.0, 'preference': 2.0, 'veto': 8.0},
            'cost': {'indifference': 100.0, 'preference': 200.0, 'veto': 600.0},
            'power': {'indifference': 4.0, 'preference': 12.0, 'veto': 28.0}
        }
        self.expected_result = {
            'aut': {'aut': 1.0, 'bel': 0.2, 'fra': 0.2, 'ger': 0.0, 'ita': 0.0},
            'bel': {'aut': 0.0, 'bel': 1.0, 'fra': 0.0, 'ger': 0.2, 'ita': 0.0},
            'fra': {'aut': 0.2, 'bel': 0.2, 'fra': 1.0, 'ger': 0.2, 'ita': 0.2},
            'ger': {'aut': 0.6, 'bel': 0.2, 'fra': 0.0, 'ger': 1.0, 'ita': 0.2},
            'ita': {'aut': 0.2, 'bel': 0.2, 'fra': 0.2, 'ger': 0.0, 'ita': 1.0},
        }

    def test_result(self):
        result = get_credibility_iv(self.performances, self.criteria, self.thresholds,
                                    self.pref_directions)
        self.assertEqual(result, self.expected_result)


class TestElectreTriCClassAssign(unittest.TestCase):

    def setUp(self):
        self.alternatives =  ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10', 'a11', 'a12', 'a13', 'a14', 'a15', 'a16', 'a17', 'a18', 'a19', 'a20', 'a21', 'a22', 'a23', 'a24', 'a25', 'a26', 'a27', 'a28', 'a29', 'a30', 'a31', 'a32', 'a33', 'a34', 'a35', 'a36', 'a37', 'a38', 'a39', 'a40']
        self.categories_profiles = OrderedDict([('b1', 'C1'), ('b2', 'C2'), ('b3', 'C3'), ('b4', 'C4')])
        self.categories_rank = {'C3': 2, 'C2': 3, 'C1': 4, 'C4': 1}
        self.credibility =  OrderedDict([
            ('a1', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a2', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 1.0), ('b4', 1.0)])),
            ('a3', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a4', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a5', OrderedDict([('b1', 0.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a6', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a7', OrderedDict([('b1', 0.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a8', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.769230769231), ('b4', 0.0)])),
            ('a9', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a10', OrderedDict([('b1', 0.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a11', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a12', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a13', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a14', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a15', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a16', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a17', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 1.0), ('b4', 0.0)])),
            ('a18', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a19', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.769230769231), ('b4', 0.0)])),
            ('a20', OrderedDict([('b1', 0.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a21', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a22', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a23', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a24', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a25', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a26', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a27', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a28', OrderedDict([('b1', 0.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a29', OrderedDict([('b1', 0.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a30', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a31', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 1.0), ('b4', 0.0)])),
            ('a32', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a33', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a34', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a35', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a36', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a37', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a38', OrderedDict([('b1', 1.0), ('b2', 0.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a39', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('a40', OrderedDict([('b1', 1.0), ('b2', 1.0), ('b3', 0.0), ('b4', 0.0)])),
            ('b1', OrderedDict([
                ('a1', 0.0), ('a2', 0.0), ('a3', 0.0), ('a4', 0.0), ('a5', 0.0),
                ('a6', 0.0), ('a7', 0.0), ('a8', 0.0), ('a9', 0.0), ('a10', 0.0),
                ('a11', 0.0), ('a12', 0.0), ('a13', 0.0), ('a14', 0.0), ('a15', 0.0),
                ('a16', 0.0), ('a17', 0.0), ('a18', 0.0), ('a19', 0.0), ('a20', 0.0),
                ('a21', 0.0), ('a22', 0.0), ('a23', 0.0), ('a24', 0.0), ('a25', 0.0),
                ('a26', 0.0), ('a27', 0.0), ('a28', 0.0), ('a29', 0.0), ('a30', 0.0),
                ('a31', 0.0), ('a32', 0.0), ('a33', 0.0), ('a34', 0.0), ('a35', 0.0),
                ('a36', 0.0), ('a37', 0.0), ('a38', 0.0), ('a39', 0.0), ('a40', 0.0)
            ])),
            ('b2', OrderedDict([
                ('a1', 0.0), ('a2', 0.0), ('a3', 0.0), ('a4', 0.0), ('a5', 0.0),
                ('a6', 0.0), ('a7', 0.0), ('a8', 0.0), ('a9', 0.0), ('a10', 0.0),
                ('a11', 0.0), ('a12', 0.0), ('a13', 0.0), ('a14', 0.0), ('a15', 0.0),
                ('a16', 0.0), ('a17', 0.0), ('a18', 0.0), ('a19', 0.0), ('a20', 0.0),
                ('a21', 0.0), ('a22', 0.0), ('a23', 0.0), ('a24', 0.0), ('a25', 0.0),
                ('a26', 0.0), ('a27', 0.0), ('a28', 0.0), ('a29', 0.0), ('a30', 0.0),
                ('a31', 0.0), ('a32', 0.0), ('a33', 0.0), ('a34', 0.0), ('a35', 0.0),
                ('a36', 0.0), ('a37', 0.0), ('a38', 0.0), ('a39', 0.0), ('a40', 0.0)
            ])),
            ('b3', OrderedDict([
                ('a1', 0.0), ('a2', 0.0), ('a3', 0.0), ('a4', 0.0), ('a5', 0.692307692308),
                ('a6', 0.0), ('a7', 0.0), ('a8', 0.0), ('a9', 0.692307692308), ('a10', 0.692307692308),
                ('a11', 0.0), ('a12', 0.0), ('a13', 0.0), ('a14', 0.0), ('a15', 0.0),
                ('a16', 0.0), ('a17', 0.0), ('a18', 0.0), ('a19', 0.0), ('a20', 0.0),
                ('a21', 0.0), ('a22', 0.0), ('a23', 0.0), ('a24', 0.0), ('a25', 0.0),
                ('a26', 0.0), ('a27', 0.0), ('a28', 0.692307692308), ('a29', 0.692307692308),('a30', 0.0),
                ('a31', 0.0), ('a32', 0.538461538462), ('a33', 0.0), ('a34', 0.0), ('a35', 0.0),
                ('a36', 0.0), ('a37', 1.0), ('a38', 0.0), ('a39', 0.0), ('a40', 0.0)
            ])),
            ('b4', OrderedDict([
                ('a1', 0.0), ('a2', 0.0), ('a3', 0.0), ('a4', 0.0), ('a5', 1.0),
                ('a6', 0.0), ('a7', 1.0), ('a8', 1.0), ('a9', 1.0), ('a10', 1.0),
                ('a11', 0.846153846154), ('a12', 0.846153846154), ('a13', 0.846153846154), ('a14', 0.0), ('a15', 0.0),
                ('a16', 0.0), ('a17', 0.846153846154), ('a18', 0.846153846154), ('a19', 0.846153846154), ('a20', 0.846153846154),
                ('a21', 0.846153846154), ('a22', 1.0), ('a23', 1.0), ('a24', 1.0), ('a25', 1.0),
                ('a26', 1.0), ('a27', 1.0), ('a28', 1.0), ('a29', 1.0), ('a30', 0.0),
                ('a31', 1.0), ('a32', 1.0), ('a33', 1.0), ('a34', 1.0), ('a35', 0.0),
                ('a36', 0.0), ('a37', 1.0), ('a38', 1.0), ('a39', 1.0), ('a40', 0.0)
            ]))
        ])
        self.cut_threshold = 0.7
        self.expected_result = OrderedDict([
            ('a1', ('C3', 'C4')),
            ('a2', ('C4', 'C4')),
            ('a3', ('C2', 'C4')),
            ('a4', ('C3', 'C4')),
            ('a5', ('C1', 'C3')),
            ('a6', ('C2', 'C4')),
            ('a7', ('C1', 'C3')),
            ('a8', ('C3', 'C4')),
            ('a9', ('C3', 'C3')),
            ('a10', ('C1', 'C3')),
            ('a11', ('C3', 'C3')),
            ('a12', ('C3', 'C3')),
            ('a13', ('C3', 'C3')),
            ('a14', ('C3', 'C4')),
            ('a15', ('C3', 'C4')),
            ('a16', ('C2', 'C4')),
            ('a17', ('C3', 'C4')),
            ('a18', ('C3', 'C3')),
            ('a19', ('C3', 'C4')),
            ('a20', ('C1', 'C3')),
            ('a21', ('C2', 'C3')),
            ('a22', ('C3', 'C3')),
            ('a23', ('C2', 'C3')),
            ('a24', ('C3', 'C3')),
            ('a25', ('C2', 'C3')),
            ('a26', ('C2', 'C3')),
            ('a27', ('C2', 'C3')),
            ('a28', ('C1', 'C3')),
            ('a29', ('C1', 'C3')),
            ('a30', ('C2', 'C4')),
            ('a31', ('C3', 'C4')),
            ('a32', ('C2', 'C3')),
            ('a33', ('C2', 'C3')),
            ('a34', ('C3', 'C3')),
            ('a35', ('C2', 'C4')),
            ('a36', ('C2', 'C4')),
            ('a37', ('C2', 'C2')),
            ('a38', ('C2', 'C3')),
            ('a39', ('C3', 'C3')),
            ('a40', ('C3', 'C4'))
        ])

    def test_result(self):
        result = assign_class_tri_c(self.alternatives, self.categories_profiles,
                                    self.categories_rank, self.credibility, self.cut_threshold)
        self.assertEqual(result, self.expected_result)


class TestElectreIsDiscordanceBinary(unittest.TestCase):

    def setUp(self):
        self.alternatives = ['ita', 'bel', 'ger', 'aut', 'fra']
        self.criteria = ['power', 'safety', 'cost']
        self.performances = {
            'aut': {'safety': 8.0, 'cost': 800.0, 'power': 74.0},
            'bel': {'safety': 0.0, 'cost': 200.0, 'power': 58.0},
            'fra': {'safety': 6.0, 'cost': 800.0, 'power': 98.0},
            'ger': {'safety': 7.0, 'cost': 400.0, 'power': 66.0},
            'ita': {'safety': 4.0, 'cost': 600.0, 'power': 90.0}
        }
        self.pref_directions = {'safety': 'max', 'cost': 'min', 'power': 'max'}
        self.thresholds = {
            'safety': {'indifference': 1.0, 'preference': 2.0, 'veto': 8.0},
            'cost': {'indifference': 100.0, 'preference': 200.0, 'veto': 600.0},
            'power': {'indifference': 4.0, 'preference': 12.0, 'veto': 28.0}
        }

        self.discordances = {
            'ger': {'ger': {'power': 0, 'cost': 0, 'safety': 0},
                    'fra': {'power': 1, 'cost': 0, 'safety': 0},
                    'aut': {'power': 0, 'cost': 0, 'safety': 0},
                    'bel': {'power': 0, 'cost': 0, 'safety': 0},
                    'ita': {'power': 0, 'cost': 0, 'safety': 0}},
            'fra': {'ger': {'power': 0, 'cost': 0, 'safety': 0},
                    'fra': {'power': 0, 'cost': 0, 'safety': 0},
                    'aut': {'power': 0, 'cost': 0, 'safety': 0},
                    'bel': {'power': 0, 'cost': 1, 'safety': 0},
                    'ita': {'power': 0, 'cost': 0, 'safety': 0}},
            'aut': {'ger': {'power': 0, 'cost': 0, 'safety': 0},
                    'fra': {'power': 0, 'cost': 0, 'safety': 0},
                    'aut': {'power': 0, 'cost': 0, 'safety': 0},
                    'bel': {'power': 0, 'cost': 1, 'safety': 0},
                    'ita': {'power': 0, 'cost': 0, 'safety': 0}},
            'bel': {'ger': {'power': 0, 'cost': 0, 'safety': 0},
                    'fra': {'power': 1, 'cost': 0, 'safety': 0},
                    'aut': {'power': 0, 'cost': 0, 'safety': 1},
                    'bel': {'power': 0, 'cost': 0, 'safety': 0},
                    'ita': {'power': 1, 'cost': 0, 'safety': 0}},
            'ita': {'ger': {'power': 0, 'cost': 0, 'safety': 0},
                    'fra': {'power': 0, 'cost': 0, 'safety': 0},
                    'aut': {'power': 0, 'cost': 0, 'safety': 0},
                    'bel': {'power': 0, 'cost': 0, 'safety': 0},
                    'ita': {'power': 0, 'cost': 0, 'safety': 0}}
        }
        self.aggregated_discordances = {
            'aut': {'aut': 0, 'bel': 1, 'fra': 0, 'ger': 0, 'ita': 0},
            'bel': {'aut': 1, 'bel': 0, 'fra': 1, 'ger': 0, 'ita': 1},
            'fra': {'aut': 0, 'bel': 1, 'fra': 0, 'ger': 0, 'ita': 0},
            'ger': {'aut': 0, 'bel': 0, 'fra': 1, 'ger': 0, 'ita': 0},
            'ita': {'aut': 0, 'bel': 0, 'fra': 0, 'ger': 0, 'ita': 0}
        }

    def test_get_discordances(self):
        result = get_discordances(self.alternatives, self.criteria,
                                  self.pref_directions, self.thresholds,
                                  self.performances)
        self.assertEqual(result, self.discordances)

    def test_aggregate_discordances(self):
        result = aggregate_discordances(self.discordances)
        self.assertEqual(result, self.aggregated_discordances)


class TestElectreTriClassAssign(unittest.TestCase):

    def setUp(self):
        self.alternatives = ['a01', 'a02', 'a03', 'a04', 'a05', 'a06']
        self.categories_profiles = {
            'Bad': {'upper': 'pBM'},
            'Good': {'lower': 'pMG'},
            'Medium': {'lower': 'pBM', 'upper': 'pMG'}
        }
        self.credibility = OrderedDict([
            ('a01', OrderedDict([('pMG', 0.7), ('pBM', 0.976)])),
            ('a02', OrderedDict([('pMG', 0.0), ('pBM', 0.7549)])),
            ('a03', OrderedDict([('pMG', 0.654), ('pBM', 1.0)])),
            ('a04', OrderedDict([('pMG', 0.0), ('pBM', 0.6453)])),
            ('a05', OrderedDict([('pMG', 0.6181), ('pBM', 0.9766)])),
            ('a06', OrderedDict([('pMG', 0.0), ('pBM', 0.8809)])),
            ('pMG', OrderedDict([('a01', 0.7219), ('a02', 1.0), ('a03', 0.7891), ('a04', 0.829), ('a05', 1.0), ('a06', 0.874)])),
            ('pBM', OrderedDict([('a01', 0.0), ('a02', 0.476), ('a03', 0.0), ('a04', 0.49), ('a05', 0.0), ('a06', 0.356)])),
        ])
        self.cut_threshold = 0.7
        self.expected_result = OrderedDict([
            ('a01', ('Medium', 'Good')),
            ('a02', ('Medium', 'Medium')),
            ('a03', ('Medium', 'Medium')),
            ('a04', ('Bad', 'Medium')),
            ('a05', ('Medium', 'Medium')),
            ('a06', ('Medium', 'Medium'))
        ])

    def test_result(self):
        result = assign_class_tri(self.alternatives, self.categories_profiles,
                                  self.credibility, self.cut_threshold)
        self.assertEqual(result, self.expected_result)


class TestElectreTriCredibility(unittest.TestCase):

    def setUp(self):
        self.alternatives = ['a01', 'a02', 'a03', 'a04', 'a05', 'a06']
        self.categories_profiles = ['pMG', 'pBM']
        self.concordance = OrderedDict([
            ('a01', OrderedDict([('pMG', 0.7), ('pBM', 0.976)])),
            ('a02', OrderedDict([('pMG', 0.3144), ('pBM', 0.7549)])),
            ('a03', OrderedDict([('pMG', 0.654), ('pBM', 1.0)])),
            ('a04', OrderedDict([('pMG', 0.5928), ('pBM', 0.6453)])),
            ('a05', OrderedDict([('pMG', 0.6181), ('pBM', 0.9766)])),
            ('a06', OrderedDict([('pMG', 0.3504), ('pBM', 0.8809)])),
            ('pMG', OrderedDict([('a01', 0.7219), ('a02', 1.0), ('a03', 0.7891), ('a04', 0.829), ('a05', 1.0), ('a06', 0.874)])),
            ('pBM', OrderedDict([('a01', 0.3546), ('a02', 0.476), ('a03', 0.0846), ('a04', 0.49), ('a05', 0.24), ('a06', 0.356)]))
        ])
        self.discordances = OrderedDict([
            ('a01', OrderedDict([
                ('pMG', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('pBM', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('a02', OrderedDict([
                ('pMG', OrderedDict([('c01', 1.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('pBM', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('a03', OrderedDict([
                ('pMG', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('pBM', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('a04', OrderedDict([
                ('pMG', OrderedDict([('c01', 1.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('pBM', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('a05', OrderedDict([
                ('pMG', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('pBM', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('a06', OrderedDict([
                ('pMG', OrderedDict([('c01', 1.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('pBM', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('pMG', OrderedDict([
                ('a01', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a02', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a03', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a04', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a05', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a06', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ])),
            ('pBM', OrderedDict([
                ('a01', OrderedDict([('c01', 1.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a02', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a03', OrderedDict([('c01', 1.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a04', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a05', OrderedDict([('c01', 1.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)])),
                ('a06', OrderedDict([('c01', 0.0), ('c02', 0.0), ('c03', 0.0), ('c04', 0.0), ('c05', 0.0)]))
            ]))
        ])

        self.expected_result = OrderedDict([
            ('a01', OrderedDict([('pMG', 0.7), ('pBM', 0.976)])),
            ('a02', OrderedDict([('pMG', 0), ('pBM', 0.7549)])),
            ('a03', OrderedDict([('pMG', 0.654), ('pBM', 1.0)])),
            ('a04', OrderedDict([('pMG', 0), ('pBM', 0.6453)])),
            ('a05', OrderedDict([('pMG', 0.6181), ('pBM', 0.9766)])),
            ('a06', OrderedDict([('pMG', 0), ('pBM', 0.8809)])),
            ('pMG', OrderedDict([('a01', 0.7219), ('a02', 1.0), ('a03', 0.7891), ('a04', 0.829), ('a05', 1.0), ('a06', 0.874)])),
            ('pBM', OrderedDict([('a01', 0), ('a02', 0.476), ('a03', 0), ('a04', 0.49), ('a05', 0), ('a06', 0.356)]))
        ])

    def test_result(self):
        result = get_credibility_tri(self.concordance, self.discordances,
                                     self.alternatives, self.categories_profiles)
        self.assertEqual(result, self.expected_result)


if __name__ == '__main__':
    unittest.main()
