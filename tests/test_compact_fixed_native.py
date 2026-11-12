"""Optional independent native check of a genuine coarse-information fixture."""

import pytest

from poker_ai.evaluation.compact_fixed_software import (
    analytical_fixture as native_fixture,
)
from poker_ai.evaluation.compact_fixed_software import (
    coarse_context as context,
)
from poker_ai.postflop.compact_fixed import native_check
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare

pytest.importorskip("pyspiel")


def test_real_reference_matches_positive_information_fixture() -> None:
    c = context()
    own, _ = native_fixture()
    actual = compare(
        c.scoring,
        (ScalarReference(c.scoring.exact), ScalarReference(c.scoring.partition)),
        own,
    )
    assert native_check(own, actual) < 1e-12
    assert actual["native_metrics"]["extra_information_gap_chips"] > 0.4
