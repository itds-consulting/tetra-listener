#!/bin/bash

set -e

ROOT=$(dirname $(realpath $0))

cd $ROOT
mkdir -p codec
cd $ROOT/codec

CHASH=1fe18c4773c8ccb52ef23ca5b4a0b0841b38d54ddd5d9c7d86eb8b060f132f39

# download audio codec, if needed
echo "$CHASH  en_30039502v010301p0.zip" | sha256sum -c - || (
    rm -f en_30039502v010301p0.zip
    wget http://www.etsi.org/deliver/etsi_en/300300_300399/30039502/01.03.01_60/en_30039502v010301p0.zip
    )

# check that the downloaded file is OK
echo "$CHASH  en_30039502v010301p0.zip" | sha256sum -c - || (
    echo "Downloaded codec does not match checksum $CHASH, will not continue!"
    exit 1
    )

# build audio codec
rm -rf amr-code c-code c-word
unzip -L en_30039502v010301p0.zip

for p in `cat $ROOT/osmo-tetra/etsi_codec-patches/series`; do
    patch -p1 --binary < $ROOT/osmo-tetra/etsi_codec-patches/$p;
done
patch -p0 --binary < $ROOT/etsi_codec-patches-brm/cflags.patch

make -C amr-code
make -C c-code

# build osmo-tetra
cd $ROOT
make -C osmo-tetra/src
