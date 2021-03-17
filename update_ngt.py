#!/usr/bin/python

import sys
import getopt
import paramiko
import json
import logging
import os



gDebugLevel = logging.DEBUG

gScriptName = ""
pHost = ""
pPort = 22
pUser = ""
pPassword = ""
pKeyFile = ""
pAskPassword = False
pCreateSnapShot = "yes"
pVerbose = False



#######################################################
##      Definining Loggin
#######################################################
#FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


logPath = './logs/'
fileName = 'update_ngt.log'
if not os.path.isdir:
  os.mkdir( logPath )

# # create logger
rootLogger = logging.getLogger()
logFormatter = logging.Formatter( FORMAT )

fileHandler = logging.FileHandler("{0}/{1}".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

if pVerbose:
  rootLogger.setLevel( logging.DEBUG )
else:
  rootLogger.setLevel( gDebugLevel )


# 'application' code
# logger.debug('debug message')
# logger.info('info message')
# logger.warning('warn message')
# logger.error('error message')
# logger.critical('critical message')





#######################################################




#######################################################
##        execSSHCommand
#######################################################
def execSSHCommand( pCommand ):
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  ssh.connect( pHost, pPort, pUser )

  stdin, stdout, stderr = ssh.exec_command( pCommand )
  return stdout.readlines()



#######################################################
##        getAlertsNgt
#######################################################
def getAlertsNgt():

  getAlertsCmd = "ncli alerts ls"

  lines_alerts = execSSHCommand( getAlertsCmd )

  alert = {}
  alertsArr = []
  for lines in lines_alerts:
    # If empty line, save register, if exists
    if lines == "\n":
      if alert != {}:
        if alert["Title"] == "NGT Update Available":
          # Just get if it's for NGT Updates
          alertsArr.append( alert ) 
      alert = {}
      continue

    line_splited = lines.split( ':', 1 )
    alert[line_splited[0].strip()] = line_splited[1].strip()

  return alertsArr

#######################################################
##        getVMData
#######################################################
def getVMData( vmID="", vmName="" ):
  #Base Command: ncli vm ls id="00059c96-4748-7591-74cf-ac1f6b3793b3::0f1f9282-a4e3-40b0-917c-9c9847c1638f"


  if vmID == "" and vmName == "":
    rootLogger.error( 'Invalid getVMData call: vmID and vmName is blank !' )
    raise Exception('Invalid getVMData call: vmID and vmName is blank !')


  lCommand = "ncli vm ls"
  if vmID:
    lCommand += " id='{0}'".format( vmID ) 

  if vmName:
    lCommand += " name='{0}'".format( vmName ) 


  outPut = execSSHCommand( lCommand )

  if outPut[0].strip() == "[None]":
    return None

  vmData = {}
  for lines in outPut:
    # If empty line, save register, if exists
    lines = lines.strip()
    if not lines.strip() :
      continue

    line_splited = lines.split( ':' )
    vmData[line_splited[0].strip()] = line_splited[1].strip()


  return vmData





#######################################################
##        updateNGT
#######################################################

def updateNGT( createSnapShot = True, stopToConfirm=False ):
  alertas = getAlertsNgt()

  rootLogger.warning('Total NGT Alerts: ' + str( len( alertas ) ) )
  
  lID = alertas[0]['Entities On'][3:]

  vmData = getVMData( vmID=lID )

  if pCreateSnapShot:
    vmCreateSnaptShot( lID )




  

#######################################################
#######################################################
def usage():
  ## Print Usage menu
  print('                  ')
  print('               Usage: ' + gScriptName + ' -h -u [-p] [-w] [-W] [-f] [--help] [--create-snapshot=<yes|no>] [-v]' )
  print('                  ')
  print('           -h --host: Target host for SSH Connection ( Nutanix CVM ).')
  print('           -u --user: User for SSH Connection.')
  print('           -p --port: (optional) Port for SSH connection.')
  print('                      Default 22')
  print('       -w --password: (optional) Password for SSH connection will be Asked in run time.')
  print('   -W --set-password: (optional) Inform password for SSH connection ( Not recommended ).')
  print('                             ')
  print('                      Attention: If -w or -W is Not defined, SSH connection will be tried without password.')
  print('                                 If Key file Not specified by -f / --file, default key file will be used.')
  print('                             ')
  print('           -f --file: (optional) Inform key file for SSH connection.')
  print('-s --create-snapshot: (optional) Shuold be created a snapshot before NGT update. Default = yes')
  print('                  -v: Verbose.')
  print('                  ')
  print('--------------------------------------------------------------------------------')
  print('                  ')



#######################################################
# Main Script
#######################################################

def main(argv):

  try:
      opts, args = getopt.getopt(sys.argv[1:], "h:u:p:wW:f:vs:", ["host=","user=","port=","password", "set-password=", "file=","help", "create-snapshot="])
  except getopt.GetoptError as err:
      # print help information and exit:
      print(err)  # will print something like "option -a not recognized"
      usage()
      sys.exit(2)

  
  for o, a in opts:
      if o == "-v":
          pVerbose = True
      elif o in ("--help"):
          usage()
          sys.exit()
      elif o in ("-h", "--host"):
          pHost = a
      elif o in ("-u", "--user"):
          pUser = a
      elif o in ("-p", "--port"):
          pPort = a
      elif o in ("-w", "--password"):
          pAskPassword = True
      elif o in ("-W", "--set-password"):
          pPassword = a
      elif o in ("-f", "--file"):
          pKeyFile = a
      elif o in ("-s", "--create-snapshot"):
          pCreateSnapShot = a
      else:
          print(' Wrong arguments!')
          print('')
          usage()
  
  
  
  rootLogger.warning('\n\n                                    Initializing Execution...\n\n')

  updateNGT()

  rootLogger.warning('\n\n                                    End Execution...\n\n')
  




#######################################################
# Script Main Execute
#######################################################

if __name__ == "__main__":
   gScriptName = os.path.basename(__file__)  
   
   main(sys.argv[1:])




'''
##############################
#Alert Output example
##############################

ID                        : 7bd06d60-025c-4268-9e1b-20f866082428
Message                   : It is recommended that NGT on the VM SpiderWebProxy with uuid 0f1f9282-a4e3-40b0-917c-9c9847c1638f should be upgraded to the latest version supported by the cluster.NGT update contains bug fixes and improvements, which will improve the overall product experience.
Severity                  : kWarning
Title                     : NGT Update Available
Created On                : Wed Feb 17 00:00:42 BRT 2021
Acknowledged              : false
Acknowledged By           : 
Acknowledged On           : 
Resolved                  : false
Auto Resolved             : false
Resolved By               : 
Resolved On               : 
Entities On               : vm:00059c96-4748-7591-74cf-ac1f6b3793b3::0f1f9282-a4e3-40b0-917c-9c9847c1638f
''' 


'''
##############################
#VM Data Output example
##############################

    Id                        : 00059c96-4748-7591-74cf-ac1f6b3793b3::0f1f9282-a4e3-40b0-917c-9c9847c1638f
    Uuid                      : 0f1f9282-a4e3-40b0-917c-9c9847c1638f
    Name                      : VMName
    VM IP Addresses           : 172.16.0.100
    Hypervisor Host Id        : 00059c96-4748-7591-74cf-ac1f6b3793b3::5
    Hypervisor Host Uuid      : 68da1941-ef08-4a21-a675-c98cf5616412
    Hypervisor Host Name      : NodeNTNX
    Memory                    : 8 GiB (8,589,934,592 bytes)
    Virtual CPUs              : 6
    VDisk Count               : 1
    VDisks                    : 00059c96-4748-7591-74cf-ac1f6b3793b3::NFS:5:0:777
    Protection Domain         : DP-INFRA
    Consistency Group         : VMGROUP

''' 