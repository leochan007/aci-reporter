#!/bin/bash

set -x

BUILD_FLAG=
if [ -n "$1" ]; then
    BUILD_FLAG=--no-cache
fi

echo 'BUILD_FLAG:'$BUILD_FLAG

source module_def.sh

docker rmi $img_name

docker rmi $PREFIX/$img_name:v1

docker build $BUILD_FLAG -t $img_name .

docker tag $img_name:latest $PREFIX/$img_name:v1
