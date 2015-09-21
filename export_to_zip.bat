@ECHO OFF

setlocal ENABLEDELAYEDEXPANSION
ECHO Finding latest build version

set /p Build=<version.txt
ECHO Last build number: 1.0.!Build!

set /a Build=Build+1
ECHO Current build number: 1.0.!Build!


set Zip_Name=plugin.video.gong.play.1.0.%Build%.zip

ECHO Output filename: %Zip_Name%

ECHO Compressing files
"C:\Program Files\7-Zip\7za" a -tzip %Zip_Name% @build_files.txt -mx5

ECHO %Build%
ECHO !Build!>version.txt

set %Build%=""

endlocal