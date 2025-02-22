#!/bin/bash
#
# Script to run pylint on Travis-CI.
#
# This file is generated by l2tdevtools update-dependencies.py, any dependency
# related changes should be made in dependencies.ini.

# Exit on error.
set -e;

pylint --version

for FILE in `find setup.py config esedbrc scripts tests -name \*.py`;
do
	echo "Checking: ${FILE}";

	pylint --rcfile=.pylintrc ${FILE};
done
