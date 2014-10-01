#/bin/sh

set -e

ROOT=$(dirname $(realpath $0))

cd $ROOT
mkdir -p codec
cd $ROOT/codec
echo "1fe18c4773c8ccb52ef23ca5b4a0b0841b38d54ddd5d9c7d86eb8b060f132f39  en_30039502v010301p0.zip" | sha256sum -c - || (
    rm -f en_30039502v010301p0.zip
    wget http://www.etsi.org/deliver/etsi_en/300300_300399/30039502/01.03.01_60/en_30039502v010301p0.zip
    )
rm -rf amr-code c-code c-word
unzip -L en_30039502v010301p0.zip

for p in `cat $ROOT/osmo-tetra/etsi_codec-patches/series`; do
    patch -p1 < $ROOT/osmo-tetra/etsi_codec-patches/$p;
done

patch -p1 < $ROOT/etsi_codec-patches-brm/cflags.patch

make -C amr-code
make -C c-code
