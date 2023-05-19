# TweetMyRiver

This repository contains the three python files of the three execuatbles of automated processes in the plug-in (Data extraction, data translation and filtering, and the final predictions).

From this code we generater the ".exe" files used in the plug-in by using the "pyinstaller" library.

The ".exe" files are accessible inside the plug-in folder. To find this folder first you need to access the QGIS folder (usually inside the "roaming" folder) then you have to enter the "QGIS3" folder, after that enter in "profiles", then "default" (or the profile from which you work in QGIS), then "python", then "plugins", after that enter on the plugin (you need to have it downloaded first) "Tweet my river", then "allProcesses", and finally inside the "EXECUTABLES" folder you can find and replace the ".exe" files. Note that if you replace the files with your code they MUST have the same name as they have now, otherwise the plugin might not work as expected.

For any changes and suggestions for the plug-in code, please contact us at ollorente@icra.cat.
