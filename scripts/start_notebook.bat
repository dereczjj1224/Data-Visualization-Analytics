SET mypath=%~dp0

PUSHD %mypath%
PUSHD ..\notebooks

jupyter notebook

popd
