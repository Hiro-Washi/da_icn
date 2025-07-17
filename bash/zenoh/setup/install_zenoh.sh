#!/bin/bash

cd
echo "deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /" | sudo tee -a /etc/apt/sources.list.d/zenoh.list > /dev/null
sudo apt update
sudo apt install -y zenoh tshark

## check version
pi@yahboom:~/zenoh-dissector $ zenohd --version
2025-07-17T08:26:41.056249Z  INFO main ThreadId(01) zenohd: zenohd v1.4.0 built with rustc 1.85.0 (4d91de4e4 2025-02-17)
zenohd v1.4.0 built with rustc 1.85.0 (4d91de4e4 2025-02-17)

# Install Cargo and Rust
# 1: standard install
etho 1 | curl https://sh.rustup.rs -sSf | sh

git clone https://github.com/eclipse-zenoh/zenoh
cd zenoh
cargo build --release --all-targets
# ^ めっちゃ長い

cd
mkdir pyvenv
python -m venv pyvenv/zenoh
. pyvenv/zenoh/bin/activate
pip install eclipse-zenoh

# Capture Test
## zenoh-dissector
cd zenoh-dissector
vim Corgo.lock # version 4 -> 3
cargo build --release

### memo

1 

X1: vim Cargo.toml # change as env_logger = "0.11.7"


pi@yahboom:~/zenoh-dissector $ cargo build --release
    Updating crates.io index
    Updating git repository `https://github.com/eclipse-zenoh/zenoh.git`
error: failed to select a version for `env_logger`.
    ... required by package `zenoh-dissector v1.4.0 (/home/pi/zenoh-dissector/zenoh-dissector)`
versions that meet the requirements `^0.11.6` (locked to 0.11.7) are: 0.11.7

the package `zenoh-dissector` depends on `env_logger`, with features: `anstream` but `env_logger` does not have these features.
 It has an optional dependency with that name, but that dependency uses the "dep:" syntax in the features table, so it does not have an implicit feature with that name.


failed to select a version for `env_logger` which could resolve this conflict


## Execute Capturing
python ~/zenoh-python/examples/z_sub.py
python ~/zenoh-python/examples/z_pub.py

tshark
