#!/bin/bash
# This file assumes that it is executed from / the current working directory is the root folder of the local ufotest
# cloned repository!

# recompile all scss stylesheets
sass --verbose ./ufotest/static/scss:./ufotest/static/css

# Install the new version of he package
python3 -m pip install --user .

# This line will execute the init command in "update" mode, where ufotest checks if the installed python version for
# ufotest contains any new static assets and copies them to the actual ufotest installation folder.
ufotest init --update

#ufotest init -f
#ufotest --verbose --mock test single_frame
#ufotest --verbose --mock test --suite "full"

# Now we start the web interface server
ufotest --mock ci serve




