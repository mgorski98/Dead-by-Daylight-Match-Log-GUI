del /S /Q ..\builds\* rem /S deletes all files from subdirs, /Q is a "quiet mode" - doesnt ask you if you are sure you want to delete the files
python ../src/setup.py build -b ../builds rem build process
pause