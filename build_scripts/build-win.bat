del /S /Q ..\builds\* Rem /S deletes all files from subdirs, /Q is a "quiet mode" - doesnt ask you if you are sure you want to delete the files
python ../src/setup.py build -b ../builds Rem build process
pause