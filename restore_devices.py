#Author: truezeros
'''
---------
This script will restore device configurations on the devices listed in devices.txt.
----------
'''

from os import listdir
import os
import time
from netmiko import ConnectHandler
import getpass
import datetime

# get current date&time
now = datetime.datetime.now()
currentTime = (now.strftime("%Y-%m-%d %H-%M-%S"))

# prompt user for ssh login credentials and enable mode password
sshUsername = input('Enter your SSH username: ')
sshPassword = getpass.getpass(prompt="Enter your SSH password: ")
enablePassword = getpass.getpass(prompt="Enter your privileged-exec mode password: ")

# open devices.txt and read IP addresses that were discovered to be active earlier
with open('devices.txt') as f:
    devicesList = f.read().splitlines()

# define a blank list to aggreagate devices for each sucessfully restored devices and the devices that failed
failedDevices = []
successDevices = []

# start a loop to iterate each active device
for deviceIp in devicesList:

    # find config file for each IP address in devices.txt
    for fileName in listdir(r".\\LAB3\\SavedConfigs\\"):
        
        # read files and match the management IP address in them to find the config file for each device
        with open(r".\\LAB3\\SavedConfigs\\" + fileName) as currentFile:
            text = currentFile.read()
            if ((deviceIp + " ") in text):
                time.sleep(1.5)
                print("\n - Configuration file for " + deviceIp + " is " + fileName + '.')
                configFile = (r".\\SavedConfigs\\" + fileName)
        

    print ("\n ---------------------------- Attempting SSH connection to " + deviceIp +". ---------------------------- \n")

    try:
        
        ios_device = {
        'device_type': 'cisco_ios',
        'ip': deviceIp,
        'username': sshUsername,
        'password': sshPassword,
        'secret': enablePassword
    }

        
        # establish a SSH connection to the each active host
        try:

            net_connect = ConnectHandler(**ios_device)
            print ("\t >>> SSH connection has been established to " + deviceIp +". \n")
            time.sleep(1.5)
        except:
            print ("\n\t--- ERROR ---: Unable to SSH to " + deviceIp + ".\n")
            continue

        # get to enable mode
        try:
            net_connect.enable()
        except:
            print ("\t --- ERROR ---: Unable to escelate to privileged-exec mode. Check your enable password.")
            continue

        # determine the config file for the specific device IP
        try:
            with open(configFile) as f:
                commands_list = f.read().splitlines()

            print ("\n\t - Restoring and saving configuration on " + deviceIp + " from " + configFile + "...")
            
            ## restore config from config file
            net_connect.send_config_set(commands_list)

            ## once all commands in the config files are written, save the running configuration as start-up config on the device
            net_connect.send_command('write memory')
            ## append device IP for logging
            successDevices.append(deviceIp)
            print ("\n\t >>> Configuration has been restored on " + deviceIp + " from " + configFile + ". \n")

        # indicate error if a config file does not exist
        except:
            time.sleep(2)
            print ("\n\t--- ERROR ---: SSH to " + deviceIp+ " successful. However, there is no configuration file for it in the inventory.")
            
            # if failed, append device IP for logging
            failedDevices.append(deviceIp)
            continue
    
    except:
        time.sleep(2)
        print ("\n\t --- ERROR ---: Unable to restore device configuration for " + deviceIp + ".\n") 
        #if failed, append device IP for logging
        failedDevices.append(deviceIp)
        continue


    # if all active devices' configs restored, indicate there is no error
    if not failedDevices :
        failedDevices = ">> No devices returned error"

# remove brackets when printing devices
failedDevices = (', '.join(failedDevices))
successDevices = (', '.join(successDevices))

# log the results and save to a new file each time the program is run
restoreResult =  ("\n Day and time: " + currentTime +
        "\n Restore configuration process has been completed: " + 
        "\n >> Device configurations have been restored on " + str (successDevices) +
        "\n -- Device configurations have been failed on " + str(failedDevices))

# save the logs in a file
save_result =  open(r".\\Logs\\" + "restore-configs_" + currentTime + ".txt", "w")
save_result.write (restoreResult)
save_result.write("\n")
save_result.close
print (restoreResult + "\n > Results have been saved to restore-configs_" + currentTime + ".txt")
