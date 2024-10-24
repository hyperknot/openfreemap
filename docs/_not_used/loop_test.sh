#!/bin/bash

# Define the source folder
source_folder="20231228_201550_pt"

# Define the number of copies you want to make
number_of_copies=40

# Loop and copy the folder into c1, c2, c3, c4, ...
for i in $(seq 1 $number_of_copies); do
  cp -r "$source_folder" "c$i"
  btrfstune -m "c$i/tiles.btrfs"
done