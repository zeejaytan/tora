"""Use all allocated CPUs for spatial queries, without editing validated code.

The wear pipeline was running on ONE core of eight (job 28447941: 19:52 CPU
against 20:30 elapsed). Every `cKDTree.query` in it is single-threaded by
default, and the hot one is a nearest-neighbour search over a million vertices
per fragment.

The queries live in `fracture_mesh_ops.py` — GARF's validated mollifier, kept
here as an untracked local copy. Editing it would mean modifying validated
third-party code that produced every wear result so far, so instead this swaps
in a drop-in `cKDTree` that defaults to `workers=-1`.

`workers` only controls how the search is split across cores. Results are
identical, which `verify_parallel_kdtree.py` checks rather than assumes.

The functions in `fracture_mesh_ops` do `from scipy.spatial import cKDTree`
*inside* each function, so the name is resolved at call time — patching the
module attribute is picked up without touching the file.

Usage (before importing anything that builds trees):
    from parallel_kdtree import enable_parallel_kdtree
    enable_parallel_kdtree()
"""

import scipy.spatial as _sp

_REAL = _sp.cKDTree
_PATCHED = False


class ParallelKDTree:
    """cKDTree wrapper that spreads queries over all cores by default."""

    __slots__ = ("_t",)

    def __init__(self, *args, **kwargs):
        self._t = _REAL(*args, **kwargs)

    @staticmethod
    def _with_workers(kwargs):
        # scipy >= 1.6 calls it `workers`; older releases used `n_jobs`
        if "workers" not in kwargs and "n_jobs" not in kwargs:
            kwargs["workers"] = -1
        return kwargs

    def query(self, x, k=1, **kwargs):
        try:
            return self._t.query(x, k=k, **self._with_workers(dict(kwargs)))
        except TypeError:
            return self._t.query(x, k=k, **kwargs)      # very old scipy

    def query_ball_point(self, x, r, **kwargs):
        try:
            return self._t.query_ball_point(x, r, **self._with_workers(dict(kwargs)))
        except TypeError:
            return self._t.query_ball_point(x, r, **kwargs)

    def __getattr__(self, name):
        return getattr(self._t, name)


def enable_parallel_kdtree() -> bool:
    """Swap in the parallel tree. Returns True if patched, False if already on."""
    global _PATCHED
    if _PATCHED:
        return False
    _sp.cKDTree = ParallelKDTree
    try:
        import scipy.spatial.ckdtree as _ck        # some code imports from here
        _ck.cKDTree = ParallelKDTree
    except Exception:
        pass
    _PATCHED = True
    return True


def disable_parallel_kdtree() -> None:
    """Restore the original, for A/B comparison in the verifier."""
    global _PATCHED
    _sp.cKDTree = _REAL
    try:
        import scipy.spatial.ckdtree as _ck
        _ck.cKDTree = _REAL
    except Exception:
        pass
    _PATCHED = False
