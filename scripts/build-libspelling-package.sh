#!/usr/bin/env bash
set -euo pipefail

if [[ $(uname) == Darwin ]]; then
    compiler=clang
    stdlib=macosx_deployment_target
    stdlib_version=11.0
else
    compiler=gcc
    stdlib=sysroot
    stdlib_version=2.17
fi

rattler-build build --recipe recipes/libspelling -c conda-forge \
    --variant c_compiler="$compiler" \
    --variant c_stdlib="$stdlib" \
    --variant c_stdlib_version="$stdlib_version"
