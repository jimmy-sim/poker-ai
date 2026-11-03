"""Slow own scalar CFR+ control for IEEE operation-contraction diagnosis only."""

import ctypes
import ctypes.util
from typing import Any

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.tree import Policy


class ScalarCFRPlus:
    def __init__(
        self,
        tree: MatrixTree,
        *,
        fused_values: bool,
        fused_regrets: bool,
        fused_averages: bool,
    ) -> None:
        library = ctypes.util.find_library("m") or "/usr/lib/libSystem.B.dylib"
        self.library: Any = ctypes.CDLL(library)
        self.fma: Any = self.library.fma
        self.fma.argtypes = [ctypes.c_double] * 3
        self.fma.restype = ctypes.c_double
        self.tree = tree
        self.arithmetic = fused_values, fused_regrets, fused_averages
        self.regrets = [np.zeros(len(menu)) for menu in tree.actions]
        self.averages = [row.copy() for row in self.regrets]
        self.iteration = 0

    @staticmethod
    def normalized(rows: list[FloatArray]) -> Policy:
        result = []
        for row in rows:
            # np.float64 scalar addition keeps operation order on Python 3.12 too.
            total = sum(row)
            result.append(
                tuple(float(x / total) for x in row)
                if total > 0
                else (1 / len(row),) * len(row)
            )
        return tuple(result)

    @property
    def average_policy(self) -> Policy:
        return self.normalized(self.averages)

    def step(self) -> None:
        self.iteration += 1
        tree = self.tree
        fuse_value, fuse_regret, fuse_average = self.arithmetic
        for target in (0, 1):
            policy = self.normalized(self.regrets)
            padded = np.zeros_like(tree.legal)
            for info, row in enumerate(policy):
                padded[info, : len(row)] = row
            edges = tree.edges(padded)
            reach = tree.reaches(edges)
            values = tree.terminal_values.tolist()
            for node in reversed(range(len(tree.player))):
                if tree.player[node] == -2:
                    continue
                value = 0.0
                for column, child in enumerate(tree.source.children[node]):
                    p, v = float(edges[node, column]), values[child]
                    value = self.fma(p, v, value) if fuse_value else value + p * v
                values[node] = value
            for node_index in np.flatnonzero(tree.player == target):
                node = int(node_index)
                info = int(tree.information[node])
                cf = float(tree.chance_reach[node] * reach[node, 1 - target])
                own = float(reach[node, target])
                for column, child in enumerate(tree.source.children[node]):
                    difference = (values[child] - values[node]) * (
                        1 if target == 0 else -1
                    )
                    previous = float(self.regrets[info][column])
                    self.regrets[info][column] = (
                        self.fma(cf, difference, previous)
                        if fuse_regret
                        else previous + cf * difference
                    )
                    previous_average = float(self.averages[info][column])
                    self.averages[info][column] = (
                        self.fma(
                            self.iteration * own, policy[info][column], previous_average
                        )
                        if fuse_average
                        else previous_average
                        + self.iteration * own * policy[info][column]
                    )
            for info_index in np.flatnonzero(tree.owners == target):
                info = int(info_index)
                self.regrets[info] = np.maximum(self.regrets[info], 0)
