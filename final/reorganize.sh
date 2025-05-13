#!/bin/bash

# Move all files from subdirectories to main final/ directory
cd final

# Get all unique subdirectory names
for dir in */*/; do
    dirname=$(basename "$dir")
    mkdir -p "$dirname"
    cp -r "$dir"* "$dirname/" 2>/dev/null
done

# Remove the regional directories
rm -rf east north west

echo "Done! New structure:"
ls -la