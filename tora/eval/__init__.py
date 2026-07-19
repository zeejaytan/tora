from .metrics import (
    align_anchor,
    compute_object_cd,
    compute_part_acc,
    compute_transform_errors,
)
from .evaluator import Evaluator
# NOTE: upstream `tora.eval.spatial` is referenced in training-time probing
# callbacks but the module file is not present in this commit. The eval
# entrypoint (sample.py) does not need it, so the re-exports are disabled
# here to unblock inference.
