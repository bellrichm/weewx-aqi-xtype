#! /bin/bash
#
#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#
source ./devtools/python_versions.sh

export PYENV_VERSION=$weewx_default_python_version
PYTHONPATH=bin:../weewx/src python -m pylint bin/user/tests/test_aqi_searchlist.py
PYTHONPATH=bin:../weewx/src python -m pylint bin/user/tests/test_epaaqi.py
PYTHONPATH=bin:../weewx/src python -m pylint bin/user/tests/test_nowcast.py
PYTHONPATH=bin:../weewx/src python -m pylint bin/user/aqitype.py
