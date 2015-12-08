#!/bin/sh

# install specific package $2 according to
# version specified in requirements file $1
pip install -U `grep $2 $1 | sed 's/#.*//'`
