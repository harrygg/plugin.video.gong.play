@ECHO OFF

rem setlocal ENABLEDELAYEDEXPANSION
rem ECHO Finding latest build version

rem set /p Build=<version.txt
rem ECHO Last build number: 1.0.!Build!

rem set /a Build=Build+1
rem ECHO Current build number: 1.0.!Build!


rem set Zip_Name=plugin.video.gong.play.1.0.%Build%.zip
set Zip_Name=plugin.video.gong.play.zip

ECHO Output filename: %Zip_Name%

ECHO Compressing files
"C:\Program Files\7-Zip\7za" a -tzip %Zip_Name% @build_files.txt -mx5

rem ECHO %Build%
rem ECHO !Build!>version.txt

rem set %Build%=""

endlocal