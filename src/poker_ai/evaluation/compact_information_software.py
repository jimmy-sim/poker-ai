"""Explicit mocked-native IO fixture; never experimental comparison evidence."""

import numpy as np

from poker_ai.evaluation import compact_information_inputs as inputs
from poker_ai.postflop.compact_fixed import detail, mix
from poker_ai.postflop.compact_full_context import Context


def mocked_source(context: Context, mode: str, seed: int = 17) -> inputs.Input:
    tree = context.scoring.partition
    s = tree.normalize(tree.legal)
    f = np.zeros_like(s)
    f[:, 0] = 1
    if len(tree.keys) == 1:
        f[:] = [[0, 1]]
    packet = detail(
        context,
        mix(context, s, f, mode),
        dict(
            spot_file=context.spot_file,
            representation=context.representation,
            seed=seed,
            mixture=mode,
        ),
    )
    row = {
        k: v
        for k, v in packet.items()
        if k not in ("policy", "replies", "maximum_accounting_error_chips")
    }
    row["receipt"] = dict(file=mode + ".json.gz", sha256="a" * 64, bytes=1)
    native = dict(
        responses=[
            dict(
                target=t,
                exact_root_chips=r["exact_reply_value_chips"],
                restricted_root_chips=r["restricted_reply_value_chips"],
            )
            for t, r in enumerate(packet["responses"])
        ]
    )
    return inputs.Input(context, row, packet, native)
