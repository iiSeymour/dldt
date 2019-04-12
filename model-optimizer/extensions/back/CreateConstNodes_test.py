"""
 Copyright (c) 2018-2019 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
import unittest
import numpy as np
from extensions.back.CreateConstNodes import CreateConstNodesReplacement
from mo.utils.unittest.graph import build_graph_with_attrs, compare_graphs


class CreateConstNodesReplacementTest(unittest.TestCase):
    nodes = [
        ('data_node', {'kind': 'data', 'shape': None, 'value': None}),
        ('next_node', {'kind': 'op'}),
    ]
    edges = [
        ('data_node', 'next_node')
    ]

    new_nodes = [
        ('const', {'kind': 'op', 'op': 'Const'}),
        ('const_data', {'kind': 'data'})
    ]
    new_edges = [
        ('const', 'data_node'),
        ('const_data', 'const')
    ]

    def test_one_node(self):
        """We should add Const node and data node."""
        shape = np.array([2, 3, 4])
        data = np.zeros(shape)
        graph = build_graph_with_attrs(
            nodes_with_attrs=self.nodes,
            edges_with_attrs=self.edges,
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data})]
        )
        graph_ref = build_graph_with_attrs(
            nodes_with_attrs=self.nodes + self.new_nodes,
            edges_with_attrs=self.edges + self.new_edges,
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data}),
                                     ('const_data', {'shape': shape, 'value': data})]
        )
        tested_pattern = CreateConstNodesReplacement()
        tested_pattern.find_and_replace_pattern(graph)
        (flag, resp) = compare_graphs(graph, graph_ref, last_node='next_node')
        self.assertTrue(flag, resp)

    def test_one_bin_node(self):
        """Nothing should happen."""
        shape = np.array([2, 3, 4])
        data = np.zeros(shape)
        graph = build_graph_with_attrs(
            nodes_with_attrs=self.nodes,
            edges_with_attrs=self.edges,
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data})],
            update_edge_attrs={('data_node', 'next_node', 0): {'bin': 0}},
        )
        tested_pattern = CreateConstNodesReplacement()
        tested_pattern.find_and_replace_pattern(graph)
        (flag, resp) = compare_graphs(graph, graph, last_node='next_node')
        self.assertTrue(flag, resp)

    def test_force_precision_parameter(self):
        precision = 'FP16'
        shape = np.array([2, 3, 4])
        data = np.zeros(shape)
        graph = build_graph_with_attrs(
            nodes_with_attrs=self.nodes,
            edges_with_attrs=self.edges,
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data, 'force_precision': precision})]
        )
        graph_ref = build_graph_with_attrs(
            nodes_with_attrs=self.nodes + self.new_nodes,
            edges_with_attrs=self.edges + self.new_edges,
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data}),
                                     ('const_data', {'shape': shape, 'value': data, 'force_precision': precision}),
                                     ('const', {'force_precision': precision})]
        )
        tested_pattern = CreateConstNodesReplacement()
        tested_pattern.find_and_replace_pattern(graph)
        (flag, resp) = compare_graphs(graph, graph_ref, last_node='next_node')
        self.assertTrue(flag, resp)

        #check that force precision was added to data and Const nodes
        force_precision_const_node = graph.nodes['data_node_const']['force_precision']
        force_precision_new_data = graph.nodes['data_node_copy_']['force_precision']
        self.assertEqual(force_precision_const_node, precision)
        self.assertEqual(force_precision_new_data, precision)

    def test_two_nodes_with_bin(self):
        """Test case for data node with 2 consumers with bin edge attr.
        Nothing should happened."""
        shape = np.array([2, 3, 4])
        data = np.zeros(shape)
        graph = build_graph_with_attrs(
            nodes_with_attrs=self.nodes + [('next_node_2', {'kind': 'op'})],
            edges_with_attrs=self.edges + [('data_node', 'next_node_2')],
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data})],
            update_edge_attrs={('data_node', 'next_node', 0): {'bin': 0}, ('data_node', 'next_node_2', 0): {'bin': 0}},
        )
        tested_pattern = CreateConstNodesReplacement()
        tested_pattern.find_and_replace_pattern(graph)
        (flag, resp) = compare_graphs(graph, graph, last_node='next_node')
        self.assertTrue(flag, resp)

    def test_two_nodes_one_bin(self):
        """Test case for two output nodes, one with 'bin' parameter, other without."""
        shape = np.array([2, 3, 4])
        data = np.zeros(shape)
        graph = build_graph_with_attrs(
            nodes_with_attrs=self.nodes + [('next_node_2', {'kind': 'op'})],
            edges_with_attrs=self.edges + [('data_node', 'next_node_2')],
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data})],
            update_edge_attrs={('data_node', 'next_node', 0): {'bin': 0}},
        )
        graph_ref = build_graph_with_attrs(
            nodes_with_attrs=self.nodes + self.new_nodes + [('next_node_2', {'kind': 'op'})],
            edges_with_attrs=self.edges + self.new_edges + [('data_node', 'next_node_2')],
            update_nodes_attributes=[('data_node', {'shape': shape, 'value': data}),
                                     ('const_data', {'shape': shape, 'value': data})]
        )
        tested_pattern = CreateConstNodesReplacement()
        tested_pattern.find_and_replace_pattern(graph)
        (flag, resp) = compare_graphs(graph, graph_ref, last_node='next_node')
        self.assertTrue(flag, resp)

