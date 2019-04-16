# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.
"""tf2onnx.optimizer module"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import copy

from .const_fold_optimizer import ConstFoldOptimizer
from .identity_optimizer import IdentityOptimizer
from .merge_duplicated_nodes_optimizer import MergeDuplicatedNodesOptimizer
from .transpose_optimizer import TransposeOptimizer
from .. import logging

# optimizer sequence need to be considered carefully
_optimizers = OrderedDict([
    ("reduce_transpose", TransposeOptimizer),
    ("fold_constants", ConstFoldOptimizer),
    # merge_duplication should be used after reduce_transpose
    # for reduce_transpose may have some trans nodes that can be merge
    ("merge_duplication", MergeDuplicatedNodesOptimizer),
    ("reduce_identity", IdentityOptimizer),
])


def _get_optimizers():
    return _optimizers


def optimize_graph(graph):
    """ Optimize graph, return optimized graph. No throw. """
    logger = logging.getLogger(__name__)
    logger.info("Optimizing ONNX model")

    before = graph.dump_node_statistics()
    opts = _get_optimizers()
    for name, factory in opts.items():
        try:
            logger.verbose("Apply %s", name)
            current = copy.deepcopy(graph)
            graph = factory().optimize(current)
        except Exception:  # pylint: disable=broad-except
            # if current optimizer fails, continue with other optimizers
            logger.warning("Failed to apply %s", name, exc_info=1)

    after = graph.dump_node_statistics()
    diff = copy.deepcopy(after)
    diff.subtract(before)
    diff = ["{} {} ({}->{})".format(k, str(v) if v < 0 else '+' + str(v), before.get(k, 0), after.get(k, 0))
            for k, v in diff.most_common() if v != 0]
    logger.info("After optimization: %s", ', '.join(diff) if diff else "no change")

    return graph
