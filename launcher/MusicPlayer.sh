#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

exec 2> $SCRIPT_DIR/bin/error.log
exec 1> $SCRIPT_DIR/bin/output.log

export PYSDL2_DLL_PATH=/usr/lib

#if $SCRIPT_DIR/hello_aarch64_new exist mv to $SCRIPT_DIR/hello_aarch64
if [ -f "$SCRIPT_DIR/bin/hello_aarch64_new" ]; then
    mv $SCRIPT_DIR/bin/hello_aarch64_new $SCRIPT_DIR/bin/hello_aarch64
fi


chmod +x $SCRIPT_DIR/bin/hello_aarch64
$SCRIPT_DIR/bin/hello_aarch64
