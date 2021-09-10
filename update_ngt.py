#!/usr/bin/python

import sys
import getopt
import paramiko
import json
import logging
import os

## Just for Default parameters in Debug Mode
INDEVELOPMENT=True
gDebugLevel = logging.ERROR



cactMOUNT = 1
cactUNMOUNT = 2
gVerbose=False
gScriptName = os.path.basename(__file__)  
gCVMPassword=""
gCVMKeyFile=""
gCVMAskPassword=False
gCVMHost=""
gCVMPort=22
gCVMUser=""

gTargetUser=""
gTargetPort=22

if INDEVELOPMENT:

  gCVMHost = "192.168.20.11"
  gCVMPort = 22
  gCVMUser = "admin"

  gTargetUser = "adriano.cortes"
  gTargetPort = 20000



#######################################################
##      Definining Loggin
#######################################################
#FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


logPath = './logs/'
fileName = '{0}.log'.format( gScriptName )
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

if gVerbose:
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
def execSSHCommand( pCommand, pHost, pUser, pPort, pPassword="" ):

  try:
  
    if not pCommand:
      rootLogger.error( 'Invalid execSSHCommand call: pCommand can not be BLANK!' )
      raise Exception('Invalid execSSHCommand call: pCommand can not be BLANK!')

    if not pHost:
      rootLogger.error( 'Invalid execSSHCommand call: pHost can not be BLANK!' )
      raise Exception('Invalid execSSHCommand call: pHost can not be BLANK!')

    if not pUser:
      rootLogger.error( 'Invalid execSSHCommand call: pUser can not be BLANK!' )
      raise Exception('Invalid execSSHCommand call: pUser can not be BLANK!')

    if not pPort:
      rootLogger.error( 'Invalid execSSHCommand call: pPort can not be BLANK!' )
      raise Exception('Invalid execSSHCommand call: pPort can not be BLANK!')




    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()  
    ## TODO: Treatment for Password use
    if gCVMKeyFile:
      ssh.connect( pHost, pPort, pUser, key_filename=gCVMKeyFile )
    else:
      ssh.connect( pHost, pPort, pUser )

    stdin, stdout, stderr = ssh.exec_command( pCommand )

    return stdout.readlines()
  except Exception as ve:
    rootLogger.error( 'Error in execSSH: "{0}"!'.format( ve ) )


#######################################################
##        removeAlert
#######################################################
def removeAlert( pAlertID ):
    
  try:

    lCommand = "/home/nutanix/prism/cli/ncli alerts resolve ids='{0}'".format( pAlertID )
    

    return_mount = execSSHCommand( lCommand, gCVMHost, gCVMUser, gCVMPort )

    lCommand = "/home/nutanix/prism/cli/ncli alerts ack ids='{0}'".format( pAlertID )

    return_mount = execSSHCommand( lCommand, gCVMHost, gCVMUser, gCVMPort )
    
  except Exception as ve:
    rootLogger.error( 'Error in removeAlert: {0}!'.format( ve ) )


#######################################################




#######################################################
##        getAlertsNgt
#######################################################
def getAlertsNgt():
  try:
    getAlertsCmd = "/home/nutanix/prism/cli/ncli alerts ls"

    # TODO: Treatment for Password ask or use from parameters
    lines_alerts = execSSHCommand( getAlertsCmd, gCVMHost, gCVMUser, gCVMPort )

    alert = {}
    alertsArr = []
    for lines in lines_alerts:
      # If empty line, save register, if exists
      if ( lines == "\n" ) or (lines == "\r\n"):
        if alert != {}:
          if alert["Title"] == "NGT Update Available":
            # Just get if it's for NGT Updates
            alertsArr.append( alert ) 
        alert = {}
        continue

      line_splited = lines.split( ':', 1 )
      alert[line_splited[0].strip()] = line_splited[1].strip()

    return alertsArr

  except Exception as ve:
    rootLogger.error( 'Error in getAlertsNgt: {0}!'.format( ve ) )


#######################################################
##        getVMData
#######################################################
def getVMData( vmID="", vmName="" ):
    #Base Command: ncli vm ls id="00059c96-4748-7591-74cf-ac1f6b3793b3::0f1f9282-a4e3-40b0-917c-9c9847c1638f"
    
  try:

    if vmID == "" and vmName == "":
      rootLogger.error( 'InvalVMId getVMData call: vmID and vmName is blank !' )
      raise Exception('InvalVMId getVMData call: vmID and vmName is blank !')


    lCommand = "/home/nutanix/prism/cli/ncli vm ls"
    if vmID:
      lCommand += " id='{0}'".format( vmID ) 

    if vmName:
      lCommand += " name='{0}'".format( vmName ) 


    outPut = execSSHCommand( lCommand, gCVMHost, gCVMUser, gCVMPort )

    if outPut[0].strip() == "[None]":
      return None


    vmData = {}
    for lines in outPut:
      # If empty line, save register, if exists
      lines = lines.strip()
      if not lines:
        continue

      line_splited = lines.split( ':' )
      vmData[line_splited[0].strip()] = line_splited[1].strip()


    return vmData

  except Exception as ve:
    rootLogger.error( 'Error in getVMData: {0}!'.format( ve ) )




#######################################################
##        mountNGT
#######################################################

def mountNGT( pVMId, pAction=cactMOUNT ):

  try:
    if not pVMId:
      rootLogger.error( 'InvalVMId mountNGT call: pVMId is Blank!' )
      raise Exception('InvalVMId mountNGT call: pVMId is Blank!')

    if pAction not in [ cactMOUNT, cactUNMOUNT ]:
      rootLogger.error( 'InvalVMId mountNGT call: pAction should be cactMOUNT or cactUNMOUNT!' )
      raise Exception('InvalVMId mountNGT call: pAction should be cactMOUNT or cactUNMOUNT!')


    
    lCommand = "/home/nutanix/prism/cli/ncli ngt {0} vm-id='{1}'".format( ("mount" if pAction == cactMOUNT else "unmount" ), pVMId )
    

    return_mount = execSSHCommand( lCommand, gCVMHost, gCVMUser, gCVMPort )
    
    if 'Error: No empty CD-ROM slot available.\n' in return_mount:
        rootLogger.debug( 'NGT CD alredy mounted!' )
        return True

    if 'Successfully initiated unmount of Nutanix Guest Tools.\n' in return_mount:
      rootLogger.debug( 'NGT CD unmounted Sucessifully!' )
      return True
    
    if 'Successfully initiated mount of Nutanix Guest Tools.\n' in return_mount:
      rootLogger.debug( 'NGT CD mounted Sucessifully!' )
      return True
    
    
    rootLogger.debug( 'NGT CD NOT {0} !'.format( "mounted" if cactMOUNT else "unmounted") )
    return False

  except Exception as ve:
    rootLogger.error( 'Error in mountNGT: {0}!'.format( ve ) )


  

#######################################################
##        mountCDDevice
#######################################################

def mountCDDevice( pVMIp, pAction ):
  #TODO: Test parameters

  try:



    if not pVMIp:
      rootLogger.error( 'Invalid mountCDDevice call: pVMIp is Blank!' )
      raise Exception('Invalid mountCDDevice call: pVMIp is Blank!')

    if pAction not in [ cactMOUNT, cactUNMOUNT ]:
      rootLogger.error( 'Invalid mountCDDevice call: pAction should be cactMOUNT or cactUNMOUNT!' )
      raise Exception('Invalid mountCDDevice call: pAction should be cactMOUNT or cactUNMOUNT!')



    if pAction == cactMOUNT:
      lCommand = 'sudo mount /dev/sr0 /mnt'
    else:
      lCommand = 'sudo umount /dev/sr0'

    
    result = execSSHCommand( lCommand, pVMIp, gTargetUser, gTargetPort )

    if result == []:
      return True
    else:
      return False

  except Exception as ve:
    rootLogger.error( 'Error in mountCDDevice: {0}!'.format( ve ) )



#######################################################
##        installNGTinVM
#######################################################

def installNGTinVM( pVMIp ):

  try:

    lCommand = "sudo /mnt/installer/linux/install_ngt.py"
    result = execSSHCommand( lCommand, pVMIp, gTargetUser, gTargetPort )

    if  result == []:
      return True
    else:
      return False

  except Exception as ve:
    rootLogger.error( 'Error in installNGTinVM: {0}!'.format( ve ) )




#######################################################
##        updateAllNGT
#######################################################

def updateAllNGT( stopToConfirm=False ):

  #Get all alerts for NGT Update
  alerts = getAlertsNgt()
  if not alerts:
    rootLogger.info("There is NO NGT Alert NOW!!!")
    exit()

  rootLogger.info('Total NGT Alerts: ' + str( len( alerts ) ) )
  

  for alert in alerts:
    try:
      
      lVMId = alert['Entities On'][3:]
      
      lVMName = alert['Message'].split(" ")[8]
      lAlertId = alert['ID']

      vmData = getVMData( vmName=lVMName )
      rootLogger.debug( 'VM Data' )

      rootLogger.info( "**************************************************" )
      rootLogger.info( "VM ID: {0}".format( lVMId) )
      rootLogger.info( "VM Name: {0}".format( lVMName ) )

      lIP = vmData['VM IP Addresses'].split(",")[0].strip()

      if not lIP:
        rootLogger.warning( "VM Without IP!!!" )
        continue

      

      installed = False

      if mountNGT( lVMId, cactMOUNT ):

        if mountCDDevice( lIP, cactMOUNT ):
          installed = installNGTinVM( lIP )
          mountCDDevice( lIP, cactUNMOUNT )
        else:
          rootLogger.info(" Error in mount CD in VM ")
          rootLogger.info("*** NOT Updated ***")
          continue
          
        mountNGT( lVMId, cactUNMOUNT )

        if installed:
          removeAlert( lAlertId )
          rootLogger.info("Update Sucessifully!!!")
        else:
          rootLogger.info("*** NOT Updated ***")
      else:
        rootLogger.info("Error in NGT Mount")
        rootLogger.info("*** NOT Updated ***")


    except Exception as ve:
      rootLogger.error( 'Error in Alert "{0}": {1}!'.format( lAlertId, ve ) )

  

#######################################################
#######################################################
def usage():
  ## Print Usage menu
  print('                  ')
  print('               Usage: ' + gScriptName + ' -h -u [-p] [-w] [-W] [-f] -t [-P] [--help] [-v]' )
  print('                  ')
  print('       -h --cvm-host: Target host for SSH Connection ( Nutanix CVM ).')
  print('       -u --cvm-user: User for SSH Connection.')
  print('       -p --cvm-port: (optional) Port for SSH connection.')
  print('                      Default 22')
  print('       -w --password: (optional) Password for CVM SSH connection will be Asked in run time.')
  print('   -W --set-password: (optional) Inform password for CVM SSH connection ( Not recommended ).')
  print('                             ')
  print('                      Attention: If -w or -W is Not defined, SSH connection will be tried without password.')
  print('                                 If Key file Not specified by -f / --file, default key file will be used.')
  print('                             ')
  print('           -f --file: (optional) Inform key file for SSH connection.')
  print('    -t --target-user: Target User for SSH Connections.')
  print('    -P --target-port: Target Port for SSH Connections.')
  print('                  -v: Verbose.')
  print('                  ')
  print('--------------------------------------------------------------------------------')
  print('             ATENTION: SSH access should be setuped with default keyfile and SUDO with NOPASSWORD     ')
  print('--------------------------------------------------------------------------------')
  print('                  ')
  


#######################################################
# Main Script
#######################################################

def main(argv):

  try:
      opts, args = getopt.getopt(sys.argv[1:], "h:u:p:wW:t:P:f:vs:", ["cvm-host=","cvm-user=","cvm-port=","password", "set-password=", "target-user=", "target-port=", "file=","help"])
  except getopt.GetoptError as err:
      # print help information and exit:
      rootLogger.error(err)  # will print something like "option -a not recognized"
      usage()
      sys.exit(2)


  
  for o, a in opts:
      if o == "-v":
          global gVerbose
          gVerbose = True
      elif o in ("--help"):
          usage()
          sys.exit()
      elif o in ("-t", "--target-user"):
          global gTargetUser
          gTargetUser = a
      elif o in ("-", "--target-port"):
          global gTargetPort
          gTargetPort = a
      elif o in ("-h", "--cvm-host"):
          global gCVMHost
          gCVMHost = a
      elif o in ("-u", "--cvm-user"):
          global gCVMUser
          gCVMUser = a
      elif o in ("-p", "--cvm-port"):
          global gCVMPort
          gCVMPort = a
      elif o in ("-w", "--password"):
          global gCVMAskPassword
          gCVMAskPassword = True
      elif o in ("-W", "--set-password"):
          global gCVMPassword
          gCVMPassword = a
      elif o in ("-f", "--file"):
          global gCVMKeyFile
          gCVMKeyFile = a
      else:
          rootLogger.info(' Wrong arguments!')
          rootLogger.info('')
          usage()
  
  

  if not gCVMHost:
    rootLogger.error('\n\n Wrong usage!!!\n')  
    rootLogger.error('CVM Target Host should be Passed!\n\n')
    usage()
    sys.exit()
  
  if not gCVMUser:
    rootLogger.error('\n\n Wrong usage!!!\n')  
    rootLogger.error('CVM Target SSH User should be Passed!\n\n')
    usage()
    sys.exit()
  
  if not gCVMPort:
    rootLogger.error('\n\n Wrong usage!!!\n')  
    rootLogger.error('CVM Target SSH Port should be Passed!\n\n')
    usage()
    sys.exit()
  
  if not gTargetUser:
    rootLogger.error('\n\n Wrong usage!!!\n')  
    rootLogger.error('Target VM SSH User should be Passed!\n\n')
    usage()
    sys.exit()
  


  rootLogger.info('\n#################################################################################\n')
  rootLogger.info('\n\n                                    Initializing Execution...\n\n')

  updateAllNGT()

  rootLogger.info('\n\n                                    End Execution...\n\n')
  rootLogger.info('\n#################################################################################\n')
  




#######################################################
# Script Main Execute
#######################################################

if __name__ == "__main__":

  main(sys.argv[1:])




'''
##############################
#Alert Output example
##############################

ID                        : 7bd06d60-025c-4268-9e1b-20f866082428
Message                   : It is recommended that NGT on the VM VMName with uuid 0f1f9282-a4e3-40b0-917c-9c9847c1638f should be upgraded to the latest version sugCVMPorted by the cluster.NGT update contains bug fixes and improvements, which will improve the overall product experience.
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