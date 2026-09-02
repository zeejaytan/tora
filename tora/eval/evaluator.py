import json
from pathlib import Path
from typing import Any, Dict

import torch
import lightning as L

from .metrics import (
    compute_object_cd,
    compute_part_acc,
    compute_transform_errors,
    align_anchor,
    unit_box_scale,
)


class Evaluator:
    """Evaluator for TORA model. """

    def __init__(self, model: L.LightningModule):
        self.model = model

    def _compute_metrics(
        self,
        data: Dict[str, Any],
        pointclouds_pred: torch.Tensor,
        rotations_pred: torch.Tensor | None = None,
        translations_pred: torch.Tensor | None = None,
        output_dict: torch.Tensor | None = None,
    ) -> Dict[str, torch.Tensor]:
        """Compute evaluation metrics."""
        pts = data["pointclouds"]                       # (B, N, 3)
        pts_gt = data["pointclouds_gt"]                 # (B, N, 3)
        points_per_part = data["points_per_part"]       # (B, P)
        anchor_parts = data["anchor_parts"]             # (B, P)
        scales = data["scales"]                         # (B,)

        # WHICH FRAME THE THRESHOLDS ARE SCORED IN.
        #
        # compute_part_acc passes a fragment when its chamfer distance is under
        # a fixed 0.01. That number is not a physical length anyone chose: it is
        # tau from Breaking Bad, and Breaking Bad states it in a specific frame
        # -- "We re-scale each of them to fit a unit-length box ... This
        # normalization scheme allows our method to be scale invariant."
        #
        # This evaluator used to multiply the clouds back to each object's own
        # stored units and then apply 0.01 there, which throws away exactly the
        # scale invariance the benchmark was built on. It is harmless while
        # every dataset happens to be stored unit-box (Breaking Bad is, at
        # max|coord| ~ 0.5), and silently catastrophic when one is not:
        # Fractura's real scans are in MILLIMETRES, so the same line asked a
        # ceramic fragment to land within 0.1 mm on a pot 150 mm across, about
        # 125x tighter in linear terms than the synthetic case. Nothing but the
        # anchor -- clamped at ground truth by construction, chamfer ~0 -- could
        # pass, and all 27 real Fractura objects scored exactly 1/n_parts. That
        # zero was the ruler, not the model. See docs/notes/FRACTURA_WHY_IT_FAILS.md.
        #
        # So the threshold is now applied in the unit-box frame, which is what
        # tau = 0.01 has always meant. For data already stored that way this
        # changes nothing measurable (Breaking Bad's box side is 0.98-1.00);
        # for data stored in any other unit it is the difference between a
        # measurement and an artefact. The previous value is still reported, as
        # part_accuracy_absolute, so runs scored before this can be compared.
        B, _, _ = pts_gt.shape
        pointclouds_pred = pointclouds_pred.view(B, -1, 3)
        unit = unit_box_scale(pts_gt)                    # (B,) longest GT bbox side
        u = unit.view(B, 1, 1)
        pts_gt_unit = pts_gt / u
        pts_pred_unit = pointclouds_pred / u

        # Align the predicted anchor parts to the ground truth anchor parts using ICP (only used in anchor-free mode)
        # ICP is scale-equivariant, so aligning once here and scaling afterwards
        # gives the same answer as aligning in each frame separately.
        if self.model.anchor_free:
            pts_pred_unit = align_anchor(pts_gt_unit, pts_pred_unit, points_per_part, anchor_parts)

        # Back to the object's own stored units, for the metrics that were
        # already reported there -- object_chamfer in particular, which
        # config/trainer/main.yaml monitors to pick checkpoints. Do not change
        # its meaning: it would change which epoch gets saved.
        f = (unit * scales).view(B, 1, 1)
        pts_gt_rescaled = pts_gt_unit * f
        pts_pred_rescaled = pts_pred_unit * f

        object_cd = compute_object_cd(pts_gt_rescaled, pts_pred_rescaled)
        object_cd_unit = compute_object_cd(pts_gt_unit, pts_pred_unit)
        part_acc, matched_parts = compute_part_acc(pts_gt_unit, pts_pred_unit, points_per_part)
        part_acc_abs, _ = compute_part_acc(pts_gt_rescaled, pts_pred_rescaled, points_per_part)
        metrics = {
            "part_accuracy": part_acc,
            "part_accuracy_absolute": part_acc_abs,
            "object_chamfer": object_cd,
            "object_chamfer_unit": object_cd_unit,
        }

        raw_errors = None
        gt_algo = self.model.gt_algo
        if rotations_pred is not None and translations_pred is not None:
            if "raw_errors" in self.model.extra_metrics:
                raw_errors = {}
            rot_errors, trans_errors = compute_transform_errors(
                pts, pts_gt, rotations_pred, translations_pred, points_per_part, anchor_parts, matched_parts, scales,
                raw_errors=raw_errors, gt_algo=gt_algo,
            )
            rot_recalls = self._recall_at_thresholds(rot_errors, [5, 10])
            trans_recalls = self._recall_at_thresholds(trans_errors, [0.01, 0.05])
            # recall_at_1cm/5cm carry the same defect part accuracy did: they
            # threshold an absolute distance, and their names only describe it
            # if the object is stored in metres. On Fractura's millimetre scans
            # they read "within 0.01 mm" and are always zero. The _frac pair is
            # the same question asked scale-free -- within 1% and 5% of the
            # object's longest dimension -- which on a 150 mm pot is 1.5 mm and
            # 7.5 mm. The originals are kept unchanged for continuity.
            #
            # trans_errors is rms(t) * scales in the dataloader frame, so
            # dividing by (scales * unit) lands it in the unit-box frame. No
            # second ICP pass needed: translation error is linear in scale.
            trans_errors_unit = trans_errors / (scales * unit).clamp_min(1e-8)
            trans_recalls_unit = self._recall_at_thresholds(trans_errors_unit, [0.01, 0.05])
            metrics.update({
                "rotation_error": rot_errors,
                "translation_error": trans_errors,
                "translation_error_unit": trans_errors_unit,
                "recall_at_5deg": rot_recalls[0],
                "recall_at_10deg": rot_recalls[1],
                "recall_at_1cm": trans_recalls[0],
                "recall_at_5cm": trans_recalls[1],
                "recall_at_1pct_frac": trans_recalls_unit[0],
                "recall_at_5pct_frac": trans_recalls_unit[1],
            })

        if "euler" in self.model.extra_metrics:
            if rotations_pred is not None and translations_pred is not None:
                _, _, euler_re = compute_transform_errors(
                    pts, pts_gt, rotations_pred, translations_pred,
                    points_per_part, anchor_parts, matched_parts, scales, euler=True,
                    gt_algo=gt_algo,
                )
                metrics["euler/rotation_error"] = euler_re

        # Compute GT metrics using stored ground truth rotations and translations
        if "gt" in self.model.extra_metrics:
            if rotations_pred is not None and translations_pred is not None:
                gt_rots = data["rotations"]      # (B, P, 3, 3) from dataset
                gt_trans = data["translations"]   # (B, P, 3) from dataset
                gt_re, gt_te = compute_transform_errors(
                    pts, pts_gt, rotations_pred, translations_pred,
                    points_per_part, anchor_parts, matched_parts, scales,
                    gt_algo="procrustes",
                    rotations_gt=gt_rots, translations_gt=gt_trans,
                )
                gt_rot_recalls = self._recall_at_thresholds(gt_re, [5, 10])
                gt_trans_recalls = self._recall_at_thresholds(gt_te, [0.01, 0.05])
                metrics.update({
                    "gt/rotation_error": gt_re,
                    "gt/translation_error": gt_te,
                    "gt/recall_at_5deg": gt_rot_recalls[0],
                    "gt/recall_at_10deg": gt_rot_recalls[1],
                    "gt/recall_at_1cm": gt_trans_recalls[0],
                    "gt/recall_at_5cm": gt_trans_recalls[1],
                })

                if "euler" in self.model.extra_metrics:
                    _, _, gt_euler_re = compute_transform_errors(
                        pts, pts_gt, rotations_pred, translations_pred,
                        points_per_part, anchor_parts, matched_parts, scales, euler=True,
                        gt_algo="procrustes",
                        rotations_gt=gt_rots, translations_gt=gt_trans,
                    )
                    metrics["gt/euler_rotation_error"] = gt_euler_re

        if "unitless" in self.model.extra_metrics:
            # Compute metrics on non-rescaled (normalized) point clouds.
            #
            # NOTE this is the DATALOADER frame (max|coord| = 1, so a box of
            # side 2), not the benchmark's unit-length box. It is scale-free,
            # but 0.01 applied here is 4x stricter than tau. The top-level
            # part_accuracy above is the calibrated one; prefer it. This block
            # is kept because older runs reported it.
            unitless_cd = compute_object_cd(pts_gt, pointclouds_pred)
            unitless_pa, unitless_matched = compute_part_acc(pts_gt, pointclouds_pred, points_per_part)
            metrics["unitless/object_chamfer"] = unitless_cd
            metrics["unitless/part_accuracy"] = unitless_pa

            if rotations_pred is not None and translations_pred is not None:
                _, unitless_te = compute_transform_errors(
                    pts, pts_gt, rotations_pred, translations_pred,
                    points_per_part, anchor_parts, unitless_matched, scale=None,
                    gt_algo=gt_algo,
                )
                metrics["unitless/translation_error"] = unitless_te

                if "euler" in self.model.extra_metrics:
                    _, _, unitless_euler_re = compute_transform_errors(
                        pts, pts_gt, rotations_pred, translations_pred,
                        points_per_part, anchor_parts, unitless_matched, scale=None, euler=True,
                        gt_algo=gt_algo,
                    )
                    metrics["unitless/euler_rotation_error"] = unitless_euler_re

        self._raw_errors = raw_errors
        return metrics

    @staticmethod
    def _recall_at_thresholds(metrics: torch.Tensor, thresholds: list[float]) -> list[torch.Tensor]:
        """Compute metrics of shape (B,) at thresholds."""
        return [(metrics <= threshold).float() for threshold in thresholds]

    def _save_single_result(
        self,
        data: Dict[str, Any],
        metrics: Dict[str, torch.Tensor],
        idx: int,
        generation_idx: int = 0,
    ) -> None:
        """Save a single evaluation result to JSON.

        Args:
            data: Input data dictionary.
            metrics: Computed metrics dictionary.
            idx: Index of the sample in the batch.
            generation_idx: Generation index for the result file name.
        """
        dataset_name = data["dataset_name"][idx]
        entry = {
            "name": data["name"][idx],
            "dataset": dataset_name,
            "num_parts": int(data["num_parts"][idx]),
            "generation_idx": generation_idx,
            "scales": float(data["scales"][idx]),
        }
        entry.update({k: float(v[idx]) for k, v in metrics.items()})

        out_dir = Path(self.model.trainer.log_dir) / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / f"{dataset_name}_sample{int(data['index'][idx]):05d}_generation{generation_idx:02d}.json"
        filepath.write_text(json.dumps(entry))

        if self._raw_errors is not None:
            torch.save({
                "raw_err_rot": self._raw_errors["rotations"][idx].cpu(),
                "raw_err_trans": self._raw_errors["translations"][idx].cpu(),
            }, filepath.with_suffix(".pt"))

    def run(
        self,
        data: Dict[str, Any],
        pointclouds_pred: torch.Tensor,
        rotations_pred: torch.Tensor | None = None,
        translations_pred: torch.Tensor | None = None,
        output_dict: torch.Tensor | None = None,
        save_results: bool = False,
        generation_idx: int = 0,
    ) -> Dict[str, torch.Tensor]:
        """Run evaluation and optionally save results.

        Args:
            data: Input data dictionary, containing:
                pointclouds_gt (B, N, 3): Ground truth point clouds.
                scales (B,): scales factors.
                points_per_part (B, P): Points per part.
                name (B,): Object names.
                dataset_name (B,): Dataset names.
                index (B,): Object indices.
                num_parts (B,): Number of parts.

            pointclouds_pred (B, N, 3) or (B*N, 3): Model output samples.
            rotations_pred (B, P, 3, 3), optional: Estimated rotation matrices.
            translations_pred (B, P, 3), optional: Estimated translation vectors.
            output_dict, optional: Model outputs from forward.
            save_results (bool): If True, save each result to log_dir/results.
            generation_idx (int): The index of the generation (mainly for best-of-n generations).

        Returns:
            A dictionary with:

                object_chamfer_dist (B,): Object Chamfer distance in meters.
                part_accuracy (B,): Part accuracy.

            If rotations_pred and translations_pred are provided, also return:

                rotation_error (B,): Rotation errors in degrees.
                translation_error (B,): Translation errors in meters.
                recall_at_5deg (B,): Recall at 5 degrees.
                recall_at_10deg (B,): Recall at 10 degrees.
                recall_at_1cm (B,): Recall at 1 cm.
                recall_at_5cm (B,): Recall at 5 cm.
        """
        metrics = self._compute_metrics(data, pointclouds_pred, rotations_pred, translations_pred, output_dict)
        if save_results:
            B = data["points_per_part"].size(0)
            for i in range(B):
                self._save_single_result(data, metrics, i, generation_idx)
        return metrics
