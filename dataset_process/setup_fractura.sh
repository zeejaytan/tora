#!/bin/bash
# Create per-dataset symlinks for bone_synthetic.hdf5 and fractura_real.hdf5
#
# Both HDF5s contain multiple datasets under data_split/<name>/..., but the
# datamodule derives the dataset name from the filename. Symlinks make each
# name resolve to the same file.
#
# bone_synthetic.hdf5 -> {hip, leg, pig, rib, vertebra}.hdf5
# fractura_real.hdf5  -> {bones, ceramics, egg}.hdf5

DIR="${1:?"Usage: bash setup_fractura.sh <data_root>"}"

BONE_SYN="$DIR/bone_synthetic.hdf5"
if [ -f "$BONE_SYN" ]; then
    for name in hip leg pig rib vertebra; do
        ln -sfv "$BONE_SYN" "$DIR/${name}.hdf5"
    done
else
    echo "WARNING: $BONE_SYN not found, skipping bone_synthetic symlinks."
fi

FRACTURA_REAL="$DIR/fractura_real.hdf5"
if [ -f "$FRACTURA_REAL" ]; then
    for name in bones ceramics egg; do
        ln -sfv "$FRACTURA_REAL" "$DIR/${name}.hdf5"
    done
else
    echo "WARNING: $FRACTURA_REAL not found, skipping fractura_real symlinks."
fi

echo "Done."
