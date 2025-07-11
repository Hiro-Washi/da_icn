#!/bin/bash

cd
echo "deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /" | sudo tee -a /etc/apt/sources.list.d/zenoh.list > /dev/null
sudo apt update
sudo apt install zenoh

# Install Cargo and Rust
# 1: standard install
etho 1 | curl https://sh.rustup.rs -sSf | sh

git clone https://github.com/eclipse-zenoh/zenoh
cd zenoh
cargo build --release --all-targets
# ^ めっちゃ長い
