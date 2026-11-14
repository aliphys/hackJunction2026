"""Run a saved LightGBM model with numpy only.

The UNO Q app image ships numpy but not LightGBM, and the board may be offline,
so this reads the text model written by ``Booster.save_model`` and walks the
trees directly. It covers numerical splits with the multiclass, binary and
regression objectives. Categorical splits and linear trees raise an error.
"""
from pathlib import Path

import numpy as np

ZERO_THRESHOLD = 1e-35
MISSING_ZERO, MISSING_NAN = 1, 2


def _fields(block):
    return dict(line.split("=", 1) for line in block.splitlines() if "=" in line)


def _numbers(text, kind):
    return np.array(text.split(), dtype=kind) if text else np.empty(0, dtype=kind)


class Booster:
    def __init__(self, model_file):
        text = Path(model_file).read_text(encoding="utf-8")
        body = text.split("\nend of trees", 1)[0]
        header, *blocks = body.split("\nTree=")
        info = _fields(header)
        if "average_output" in header:
            raise ValueError("Random forest models are not supported.")

        self.feature_names = info["feature_names"].split()
        self.num_features = int(info["max_feature_idx"]) + 1
        self.trees_per_round = int(info.get("num_tree_per_iteration", 1))
        self.objective = info.get("objective", "regression").split()
        self.num_trees = len(blocks)

        feature, threshold, decision, left, right, leaf, roots = [], [], [], [], [], [], []
        nodes = leaves = 0
        for block in blocks:
            tree = _fields(block)
            if int(tree.get("num_cat", 0)) or int(tree.get("is_linear", 0)):
                raise ValueError("Categorical splits and linear trees are not supported.")
            values = _numbers(tree["leaf_value"], np.float64)
            count = len(values) - 1  # internal nodes
            if count:
                children = []
                for key in ("left_child", "right_child"):
                    child = _numbers(tree[key], np.int64)
                    # Internal nodes keep a global index. Leaves become -(global leaf) - 1.
                    children.append(np.where(child >= 0, child + nodes, child - leaves))
                left.append(children[0])
                right.append(children[1])
                feature.append(_numbers(tree["split_feature"], np.int64))
                threshold.append(_numbers(tree["threshold"], np.float64))
                decision.append(_numbers(tree["decision_type"], np.int64))
                roots.append(nodes)
            else:
                roots.append(-leaves - 1)
            leaf.append(values)
            nodes += count
            leaves += len(values)

        join = lambda parts, kind: np.concatenate(parts) if parts else np.empty(0, dtype=kind)
        self._feature = join(feature, np.int64)
        self._threshold = join(threshold, np.float64)
        self._left = join(left, np.int64)
        self._right = join(right, np.int64)
        decision = join(decision, np.int64)
        self._default_left = (decision & 2) > 0
        self._missing = (decision >> 2) & 3
        self._leaf = np.concatenate(leaf)
        self._roots = np.array(roots, dtype=np.int64)

    def predict_raw(self, data):
        data = np.atleast_2d(np.asarray(data, dtype=np.float64))
        if data.shape[1] != self.num_features:
            raise ValueError(f"Expected {self.num_features} features, got {data.shape[1]}.")
        node = np.tile(self._roots, (len(data), 1))
        while True:
            row, tree = np.nonzero(node >= 0)
            if not row.size:
                break
            at = node[row, tree]
            value = data[row, self._feature[at]]
            missing = self._missing[at]
            nan = np.isnan(value)
            value = np.where(nan & (missing != MISSING_NAN), 0.0, value)
            absent = ((missing == MISSING_ZERO) & (np.abs(value) <= ZERO_THRESHOLD)) | (
                (missing == MISSING_NAN) & nan
            )
            go_left = np.where(absent, self._default_left[at], value <= self._threshold[at])
            node[row, tree] = np.where(go_left, self._left[at], self._right[at])
        scores = self._leaf[-node - 1]
        return scores.reshape(len(data), -1, self.trees_per_round).sum(axis=1)

    def predict(self, data):
        raw = self.predict_raw(data)
        kind = self.objective[0]
        if kind == "multiclass":
            raw = np.exp(raw - raw.max(axis=1, keepdims=True))
            return raw / raw.sum(axis=1, keepdims=True)
        if kind == "binary":
            slope = next((float(p.split(":")[1]) for p in self.objective if p.startswith("sigmoid:")), 1.0)
            return 1.0 / (1.0 + np.exp(-slope * raw[:, 0]))
        if kind in ("regression", "regression_l1", "huber", "fair", "quantile"):
            return raw[:, 0]
        raise ValueError(f"Objective {kind} is not supported.")
