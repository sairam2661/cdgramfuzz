# Need to set this (requires AFL++ to be set up already)
export AFL_PATH="/abc/AFLplusplus"

cd benchmarks
wget https://download.gnome.org/sources/libxml2/2.9/libxml2-2.9.10.tar.xz
tar xf libxml2-2.9.10.tar.xz
cd libxml2-2.9.10/
mkdir -p output
./autogen.sh --without-python
CC=$AFL_PATH/afl-gcc-fast CXX=$AFL_PATH/afl-g++-fast ./configure --prefix=$(pwd)/output --without-python
make clean
make
make install
cd ..

$AFL_PATH/afl-g++-fast -I libxml2-2.9.10/output/include/libxml2/ -L libxml2-2.9.10/output/lib/ parse_libxml_stdin.c -lm -lxml2 -o parse_libxml_stdin
cd ..

$AFL_PATH/afl-fuzz -i output/seeds -o output/findings -x $AFL_PATH/dictionaries/xml.dict -- ./benchmarks/parse_libxml_stdin

# python src/mutation/afl_runner.py \
#   --seeds-dir output/seeds \
#   --target-binary /data/saiva/cdgramfuzz/benchmarks/libxml_stdin \
#   --output-dir output/afl_run \
#   --timeout 10 \
#   --tmin \
#   --top-k 5 \
#   --afl-binary $AFL_PATH/afl-fuzz \
#   --dict $AFL_PATH/dictionaries/xml.dict