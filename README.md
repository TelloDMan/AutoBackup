# Steps:
=========
> Make Sure You have Python installed on your system 
>

- After Installing the Zip Unzip and Run `pip install -r requirments.txt` in the current directory of the file

- After finishing to install the required libraries now enter in edit mode to the CiscoDevice.py and JuniperDevice.py and add the IP-s of the Clients. or if using main.py store the ip-s in All_Devices.txt.

- Put the Username and Password also the Enable Secret in the .env file
!!Attention it is not suggested to store plaintext passwords in scripting files.(To reduce the risks of the following bug, make sure this user only has read access to the devices).

- Now from terminal run `python3 filename.py` this will create a local backup folder /year/month/year-month-day/...
 
