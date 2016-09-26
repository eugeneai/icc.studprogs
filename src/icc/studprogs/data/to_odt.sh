#!/bin/bash

CMD="lowriter --convert-to odt *.doc"

find . -type d \( ! -name . \) -exec bash -c "cd '{}' && $CMD" \;

CMD="lowriter --convert-to odt *.doc"

find . -type d \( ! -name . \) -exec bash -c "cd '{}' && $CMD" \;
