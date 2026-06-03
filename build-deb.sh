#!/bin/bash
set -e

PROJECT_NAME="ubs-engine"
PROJECT_VERSION="1.0.0"
PROJECT_RELEASE="1"
TAR_NAME="${PROJECT_NAME}-${PROJECT_VERSION}"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SOURCE_DIR}/_build_deb"

echo "============================================"
echo " Building DEB packages for ${PROJECT_NAME}"
echo "============================================"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

if [ ! -f "${SOURCE_DIR}/${TAR_NAME}.tar.gz" ]; then
    echo "ERROR: ${TAR_NAME}.tar.gz not found in ${SOURCE_DIR}"
    exit 1
fi

tar xzf "${SOURCE_DIR}/${TAR_NAME}.tar.gz" -C "${BUILD_DIR}"

PKG_DIR="${BUILD_DIR}/${TAR_NAME}"
if [ ! -d "${PKG_DIR}" ]; then
    echo "ERROR: Extracted directory ${PKG_DIR} not found"
    exit 1
fi

echo "[1/4] Copying debian directory..."
cp -r "${SOURCE_DIR}/debian" "${PKG_DIR}/debian"

echo "[2/4] Applying patches..."
for patch_file in $(ls "${SOURCE_DIR}"/*.patch 2>/dev/null | sort); do
    echo "  Applying $(basename "${patch_file}")..."
    if ! patch -p1 -d "${PKG_DIR}" < "${patch_file}"; then
        echo "ERROR: Failed to apply $(basename "${patch_file}")"
        exit 1
    fi
done

echo "[3/4] Building DEB packages..."
cd "${PKG_DIR}"
dpkg-buildpackage -us -uc -b

echo "[4/4] Collecting DEB packages..."
DEB_OUTPUT="$(dirname "${SOURCE_DIR}")"
find "${BUILD_DIR}" -maxdepth 1 -name "*.deb" -exec cp {} "${DEB_OUTPUT}/" \;

echo "============================================"
echo " DEB packages built successfully!"
echo " Output directory: ${DEB_OUTPUT}"
echo "============================================"
ls -lh "${DEB_OUTPUT}/"