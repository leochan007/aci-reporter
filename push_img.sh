#!/bin/bash

set -x

source module_def.sh

docker push $PREFIX/$img_name:v1
