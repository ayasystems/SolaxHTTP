# Integración regulador solar solax en domoticz
#
# Author: @ea4gkq 2020
# 
# 22/05/2020
# - Mejorada reconexión automática
# 19/05/2020 
# - Arreglado error cuando V es 0, error división por cero 
 
"""
<plugin key="SolaxHTTP" name="Solax HTTP" author="EA4GKQ" version="1.0.5" wikilink="https://github.com/ayasystems/SolaxHTTP" externallink="https://www.solaxpower.com/x1-boost/">
    <description>
        <h2>Solax HTTP Pluging</h2><br/>
        <h3>by @ea4gkq</h3>
		<br/>
		<a href="https://domotuto.com/integracion-del-inversor-solar-solax-boost-en-domoticz/">https://domotuto.com/integracion-del-inversor-solar-solax-boost-en-domoticz/</a>
		<br/>
		Para la versión V2 necesitarás conectar tu Raspberry a la red que publica el inversor Solax_XXXXXX
    </description>
    <params>
        <param field="Address" label="Solax IP" width="200px" required="true" default="5.8.8.8"/>
        <param field="Mode1" label="Protocol" width="75px">
            <options>
                <option label="HTTP" value="80"  default="true" />
            </options>
        </param>
        <param field="Mode2" label="Version" width="75px">
            <options>
                <option label="V1" value="V1"  default="true" />
                <option label="V2" value="V2"  default="true" />
            </options>
        </param>
        <param field="Mode3" label="Update speed" width="75px">
            <options>
                <option label="Normal" value="Normal"/>
                <option label="High" value="High"  default="true" />
            </options>
        </param>   
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>  
"""
errmsg = ""
try:
 import Domoticz
except Exception as e:
 errmsg += "Domoticz core start error: "+str(e)
try:
 import json
except Exception as e:
 errmsg += " Json import error: "+str(e)
try:
 import time
except Exception as e:
 errmsg += " time import error: "+str(e)
try:
 import re
except Exception as e:
 errmsg += " re import error: "+str(e)

class SolaxHTTP:
    httpConn = None
    interval = 2
    runAgain = interval
    disconnectCount = 0
    sProtocol = "HTTP"
    VERSION = "V2"
    S1_CURRENT = ""
    S2_CURRENT = ""
    S1_VOLTAGE = ""
    S2_VOLTAGE = ""
    S1_POWER   = ""
    S2_POWER   = ""
    TO_GRID = ""
    FROM_GRID = ""
    TEMP = ""
    FREQUENCY = ""
    GRID_W = ""	
    ERROR_LEVEL = ""

    def __init__(self):
        return

    def onStart(self):
     Domoticz.Error("onStart: "+errmsg)
     if errmsg =="":
      createDevices(self,"S1_CURRENT")
      createDevices(self,"S2_CURRENT")
      createDevices(self,"S1_VOLTAGE")
      createDevices(self,"S2_VOLTAGE")	
      createDevices(self,"S1_POWER")
      createDevices(self,"S2_POWER")	
      createDevices(self,"TO_GRID")		
      createDevices(self,"FROM_GRID")	 
      createDevices(self,"FV_POWER")		 
      createDevices(self,"TEMP")		 
      createDevices(self,"FREQUENCY")
      createDevices(self,"GRID_CURRENT")	  
      try:  
        if Parameters["Mode6"] == "": Parameters["Mode6"] = "-1"
        if Parameters["Mode6"] != "0":
            Domoticz.Error("if parameters mode 6: "+Parameters["Mode6"])	  
            Domoticz.Debugging(int(Parameters["Mode6"]))
            Domoticz.Error("DumpConfigToLog")	
            DumpConfigToLog()
            self.ERROR_LEVEL = Parameters["Mode6"]
        if (Parameters["Mode1"].strip()  == "443"): self.sProtocol = "HTTPS"
        if (Parameters["Mode2"].strip()  == "V1"): self.VERSION = "V1"	
        if (Parameters["Mode3"].strip()  == "High"): Domoticz.Heartbeat(1)
        self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"].strip() , Port=Parameters["Mode1"].strip() )
        self.httpConn.Connect()
      except Exception as e:
        Domoticz.Error("Plugin onStart error: "+str(e))
     else:
        Domoticz.Error("Your Domoticz Python environment is not functional! "+errmsg)

    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Solax connected successfully.")
            if(self.VERSION=="V2"):
             sendData = { 'Verb' : 'POST',
                          'URL'  : '/?optType=ReadRealTimeData',
                          'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                        'Connection': 'keep-alive', \
                                        'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                        'Host': Parameters["Address"]+":"+Parameters["Mode1"], \
                                        'User-Agent':'Domoticz/1.0' }
                        }
            else:
             sendData = { 'Verb' : 'GET',
                          'URL'  : '/api/realTimeData.htm',
                          'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                        'Connection': 'keep-alive', \
                                        'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                        'Host': Parameters["Address"]+":"+Parameters["Mode1"], \
                                        'User-Agent':'Domoticz/1.0' }
                        }
            Connection.Send(sendData)
        else:
            Domoticz.Error("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)
            self.httpConn = None
    def onMessage(self, Connection, Data):
        DumpHTTPResponseToLog(Data)
   
        strData = Data["Data"].decode("utf-8", "ignore")
        Status = int(Data["Status"])
        LogMessage(strData)

        if (Status == 200):
            if ((self.disconnectCount & 1) == 1):
                Domoticz.Log("Good Response received from Solax, Disconnecting.")
                self.httpConn.Disconnect()
            else:
                Domoticz.Log("Good Response received from Solax, Dropping connection.")
                self.httpConn = None
            self.disconnectCount = self.disconnectCount + 1
            processResponse(self,Data)     
        elif (Status == 302):
            Domoticz.Log("Solax returned a Page Moved Error.")
            sendData = { 'Verb' : 'POST',
                         'URL'  : Data["Headers"]["Location"],
                         'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                       'Host': Parameters["Address"]+":"+Parameters["Mode1"], \
                                       'User-Agent':'Domoticz/1.0' },
                        }
            Connection.Send(sendData)
        elif (Status == 400):
            Domoticz.Error("Solax returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("Solax returned a Server Error.")
        else:
            Domoticz.Error("Solax returned a status: "+str(Status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        #Domoticz.Trace(True)
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if (self.httpConn == None):
                    self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Mode1"])
                self.httpConn.Connect()
                self.runAgain = self.interval
            else:
                Domoticz.Debug("onHeartbeat called, run again in "+str(self.runAgain)+" heartbeats.")
        #Domoticz.Trace(False)

global _plugin
_plugin = SolaxHTTP()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def createDevices(self,unitname):
      OptionsSensor = {"Custom": "1;Hz"}
      iUnit = -1
      for Device in Devices:
       try:
        if (Devices[Device].DeviceID.strip() == unitname):
         iUnit = Device
         break
       except:
         pass
      if iUnit<0: # if device does not exists in Domoticz, than create it
        try:
         iUnit = 0
         for x in range(1,256):
          if x not in Devices:
           iUnit=x
           break
         Domoticz.Debug("Creating: "+unitname);
         if iUnit==0:
          iUnit=len(Devices)+1	  
         if(unitname=="S1_CURRENT"):
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName="Current (Single)",Used=1,DeviceID=unitname).Create()
         if(unitname=="S2_CURRENT"):
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName="Current (Single)",Used=1,DeviceID=unitname).Create()
         if(unitname=="S1_VOLTAGE"):
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName="Voltage",Used=1,DeviceID=unitname).Create()
         if(unitname=="S2_VOLTAGE"):
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName="Voltage",Used=1,DeviceID=unitname).Create()
         if(unitname=="FROM_GRID"):          
          Domoticz.Device(Name=unitname, Unit=iUnit,Type=248,Subtype=1,Used=1,DeviceID=unitname).Create()
         if(unitname=="TO_GRID"):          
          Domoticz.Device(Name=unitname, Unit=iUnit,Type=248,Subtype=1,Used=1,DeviceID=unitname).Create()
         if(unitname=="S1_POWER"):
          Domoticz.Device(Name=unitname, Unit=iUnit,Type=248,Subtype=1,Used=1,DeviceID=unitname).Create()
         if(unitname=="S2_POWER"):
          Domoticz.Device(Name=unitname, Unit=iUnit,Type=248,Subtype=1,Used=1,DeviceID=unitname).Create()
         if(unitname=="FV_POWER"):
          Domoticz.Device(Name=unitname, Unit=iUnit,Type=243,Subtype=29,Switchtype=0,Used=1,DeviceID=unitname).Create()
         if(unitname=="TEMP"):
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName="Temperature",Used=1,DeviceID=unitname).Create()		 
         if(unitname=="FREQUENCY"):		
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName='Custom',Options=OptionsSensor,Used=1,DeviceID=unitname).Create()		 
         if(unitname=="GRID_CURRENT"):
          Domoticz.Device(Name=unitname, Unit=iUnit,TypeName="Current (Single)",Used=1,DeviceID=unitname).Create()
        except Exception as e:
         Domoticz.Debug(str(e))
         return False
      return 
def processResponse(self,httpResp):
    #DAY_ENERGY = ""
    #PAC = ""
    #TOTAL_ENERGY = ""
    stringData =  httpResp["Data"].decode("utf-8", "ignore")
    #Domoticz.Error(stringData)
    if(self.VERSION=="V1"):
     stringData = stringData.replace(',,',',null,').replace(',,',',null,')
    try:
      json_object = json.loads(stringData)
    except Exception as e:
      Domoticz.Error("Error json parse: "+str(e))
      if(self.ERROR_LEVEL=="-1"):
        Domoticz.Error(str(stringData))	 
      return	  
    self.S1_CURRENT = str(json_object['Data'][0])
 
    self.S2_CURRENT = str(json_object['Data'][1])
 
    self.S1_VOLTAGE = str(json_object['Data'][2])
 
    self.S2_VOLTAGE = str(json_object['Data'][3])
 
    self.S1_POWER   = str(json_object['Data'][11])
 
    self.S2_POWER   = str(json_object['Data'][12])
 
    self.TO_GRID = json_object['Data'][10]
 
    if(self.TO_GRID<0):
      self.TO_GRID = 0



    self.FROM_GRID = json_object['Data'][10]*-1
 
    if(self.FROM_GRID<0):
      self.FROM_GRID = 0


    self.TO_GRID       = str(self.TO_GRID)
    self.FROM_GRID     = str(self.FROM_GRID)
    if(json_object['Data'][5]>0):	       
       self.GRID_CURRENT  = json_object['Data'][10] / json_object['Data'][5]
    else:
       self.GRID_CURRENT  = 0
    self.GRID_CURRENT  = round(self.GRID_CURRENT * -1 ,2)
    kwhdiario          = str(json_object['Data'][8]*1000)
    acumuladoKwh       = str(json_object['Data'][6])

    self.TEMP          = str(json_object['Data'][7])
	 

    self.FREQUENCY     = str(json_object['Data'][50])

    UpdateDevice("S1_CURRENT",    0, self.S1_CURRENT)
    UpdateDevice("S2_CURRENT",    0, self.S2_CURRENT)
    UpdateDevice("S1_VOLTAGE",    0, self.S1_VOLTAGE)
    UpdateDevice("S2_VOLTAGE",    0, self.S2_VOLTAGE)
    UpdateDevice("S1_POWER",      0, self.S1_POWER)
    UpdateDevice("S2_POWER",      0, self.S2_POWER)
    UpdateDevice("TO_GRID",       0, self.TO_GRID)
    UpdateDevice("FROM_GRID",     0, self.FROM_GRID)
    UpdateDevice("FV_POWER",      0, acumuladoKwh+";"+kwhdiario)
    UpdateDevice("TEMP",          0, self.TEMP)
    UpdateDevice("FREQUENCY",     0, self.FREQUENCY)
    UpdateDevice("GRID_CURRENT",  0, self.GRID_CURRENT)
 
    if(self.ERROR_LEVEL=="-1"):
       Domoticz.Error(json.dumps(json_object))
 
def debugDevices(self,device):
    value = ""
    try:
        value = getattr(self, device)
    except AttributeError:
        Domoticz.Error("Objeto "+device+" no existe el _self")
        #print 'No %s field' % field   
        return
    Domoticz.Debug(device+": "+value)
def DumpHTTPResponseToLog(httpResp, level=0):
    if (level==0): Domoticz.Debug("HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(indentStr + "a>'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(indentStr + "b>'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(indentStr + "c>'" + x + "':'" + str(httpResp[x]) + "'")
def UpdateDevice(unitname, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
	#        if (Devices[Device].DeviceID.strip() == unitname):
      iUnit = -1
      for Device in Devices:
       try:
        if (Devices[Device].DeviceID.strip() == unitname):
         iUnit = Device
         break
       except:
         pass
      if iUnit>=0: # existe, actualizamos	
            if (Devices[iUnit].nValue != nValue) or (Devices[iUnit].sValue != sValue):
                Devices[iUnit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[iUnit].Name+")")
