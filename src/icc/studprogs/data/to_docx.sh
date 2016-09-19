#!/bin/bash

CMD="lowriter --convert-to docx *.doc"

find . -type d \( ! -name . \) -exec bash -c "cd '{}' && $CMD" \;
