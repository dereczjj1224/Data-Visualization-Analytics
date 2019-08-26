REM
REM Be sure to activate the environment prior to starting
REM

SET mypath=%~dp0

PUSHD %mypath%
PUSHD ..
SET FLASK_APP=bipolo
SET PYTHONPATH=.\

flask run

popd
