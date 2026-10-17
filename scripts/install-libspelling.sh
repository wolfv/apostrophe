#!/usr/bin/env bash
set -euo pipefail

if [[ -f "$CONDA_PREFIX/lib/girepository-1.0/Spelling-1.typelib" ]]; then
    exit
fi

version=0.4.10
sha256=56e3f01a3a18b575beea4c34349f99cdaba316e1f7c271b1231f7bcf5d9af73b
workdir="$PIXI_PROJECT_ROOT/.pixi/libspelling"
archive="$workdir/libspelling-$version.tar.xz"

mkdir -p "$workdir"
curl -L --fail --output "$archive" \
    "https://download.gnome.org/sources/libspelling/0.4/libspelling-$version.tar.xz"
echo "$sha256  $archive" | shasum -a 256 --check
rm -rf "$workdir/source" "$workdir/build"
mkdir "$workdir/source"
tar -xJf "$archive" -C "$workdir/source" --strip-components=1
meson setup "$workdir/build" "$workdir/source" \
    --prefix="$CONDA_PREFIX" --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Ddocs=false -Dvapi=false -Dsysprof=false
meson compile -C "$workdir/build"
meson install -C "$workdir/build"
