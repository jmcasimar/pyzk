#!/usr/bin/env python3

# Import modules
import json
import http.client
from time import time
import websocket as ws
from urllib.parse import urlencode, quote_plus

class parseClient:
    def __init__(self, server, appId, restKey, port = 80, mountPath = "/parse", liveQuery = {}, logger = None):
        self.server = server
        self.mountPath = mountPath
        self.appId = appId
        self.restKey = restKey
        self.port = port
        self.log = logger
        if liveQuery == {}: self.liveQuery = None
        else:
            self.liveServer = 'wss://{}{}'.format(server, mountPath)
            self.liveQuery = ParseLiveClient(self.liveServer, self.appId, self.log)
            for query in liveQuery['query']: self.liveQuery.addQuery(query)
            self.liveQuery.subscribe()
    
    def createObject(self, Class, Object):
        connection = http.client.HTTPConnection(self.server, self.port)
        connection.connect()
        
        if type(Object) is list:
            objectList = []
            for obj in Object:
                objectList.append({"method": "POST",
                                  "path": "/parse/classes/{}".format(Class),
                                  "body": obj
                                  })
            connection.request('POST', '{}/batch'.format(self.mountPath), json.dumps({"requests": objectList}),
             {
               "X-Parse-Application-Id": self.appId,
               "X-Parse-REST-API-Key": self.restKey,
               "Content-Type": "application/json"
             })
        else:
            connection.request('POST', '{}/classes/{}'.format(self.mountPath, Class), json.dumps(Object), {
               "X-Parse-Application-Id": self.appId,
               "X-Parse-REST-API-Key": self.restKey,
               "Content-Type": "application/json"
             })
        
        results = json.loads(connection.getresponse().read())
        return results
    
    def query(self, Class, where = {}, order = '', count=0, limit=100):
        connection = http.client.HTTPConnection(self.server, self.port)
        params = urlencode({"where":json.dumps(where), "order":json.dumps(order), 'count':count, 'limit':limit})
        connection.connect()
        connection.request('GET', '{}/classes/{}?{}'.format(self.mountPath, Class, params), '', {
               "X-Parse-Application-Id": self.appId,
               "X-Parse-REST-API-Key": self.restKey
             })
        result = json.loads(connection.getresponse().read())
        return  result
    
    def update(self, Class, objectId, keys):
        connection = http.client.HTTPConnection(self.server, self.port)
        connection.connect()
        connection.request('PUT', '{}/classes/{}/{}'.format(self.mountPath, Class, objectId), json.dumps(keys), {
               "X-Parse-Application-Id": self.appId,
               "X-Parse-REST-API-Key": self.restKey,
               "Content-Type": "application/json"
             })
        result = json.loads(connection.getresponse().read())
        return result
    
    def cloudCode(self, functionName, data):
        connection = http.client.HTTPConnection(self.server, self.port)
        connection.connect()
        connection.request('POST', '{}/functions/{}'.format(self.mountPath, functionName), json.dumps(data), {
        "X-Parse-Application-Id": self.appId,
        "X-Parse-REST-API-Key": self.restKey,
        "Content-Type": "application/json"
        })
        result = json.loads(connection.getresponse().read())
        return result
    
    def loop(self):
        if(self.liveServer == None): return {'op': 'error', 'error': 'LiveQuery not configured'}
        else: return self.liveQuery.loop()

class ParseLiveClient:
    def __init__(self, server, appId, logger):
        self.server = server
        self.appId = appId
        self.log = logger
        self.connect()
        self.reconnectTimer = time()
        self.queries = []
        
    def connect(self):
        self.ws = ws.create_connection(self.server, timeout = 0.1)
        self.subscribeCounter = 1
        connectDict = {
            "op": "connect",
            "applicationId": self.appId
        }
        self.ws.send(json.dumps(connectDict))
        resp = self.recv()
        if(resp['op'] == 'connected'):
            self.connected = True
            self.writeLog('info,LiveClient connected')
        else:
            self.connected = False
            self.reconnectTimer = time()
            self.writeLog('info,LiveClient connection failed')

    def writeLog(self, msg):
        if self.log == None: print(msg)
        else: self.Msg2Log(self.log.logger, msg)

    def Msg2Log(self, logger, mssg):
        if(mssg.startswith("debug,")): logger.debug(mssg.split(",")[1])
        elif(mssg.startswith("info,")): logger.info(mssg.split(",")[1])
        elif(mssg.startswith("warning,")): logger.warning(mssg.split(",")[1])
        elif(mssg.startswith("error,")): logger.error(mssg.split(",")[1])
        elif(mssg.startswith("critical,")): logger.critical(mssg.split(",")[1])
        else: logger.debug(mssg)

    def addQuery(self, query): self.queries.append(query)

    def subscribe(self):
        if self.connected:
            for query in self.queries:
                subscribeDict = {
                    "op": "subscribe",
                    "requestId": self.subscribeCounter,
                    "query": query
                }
                self.ws.send(json.dumps(subscribeDict))
                resp = self.recv()
                if(resp['op'] == 'subscribed'):
                    self.writeLog("info,Subscription {} to className {} succeed".format(self.subscribeCounter, query["className"]))
                    self.subscribeCounter += 1
                else: self.writeLog('info,Subscription failed\n{}'.format(resp))
        
    def reconnect(self):
        if time() - self.reconnectTimer > 60:
            self.reconnectTimer = time()
            self.connect()
            self.subscribe()
            if self.connected: self.writeLog(("info,LiveClient reconnected"))
            else: self.writeLog(("info,LiveClient cannot be reconnected"))

    def recv(self):
        try:
            resp = self.ws.recv()
            return json.loads(resp)
        except ws._exceptions.WebSocketTimeoutException:
            return {'op': 'error', 'type': 'timeOut', 'error': 'Tiempo de lectura agotado (timeout error)'}
        except ws._exceptions.WebSocketConnectionClosedException:
            self.ws.close()
            self.connected = False
            self.reconnectTimer = time()
            return {'op': 'error', 'type': 'connectionLost', 'error': 'Se perdió la conexión en tiempo real'}
        except Exception as e:
            self.ws.close()
            self.connected = False
            self.reconnectTimer = time()
            raise e
    
    def loop(self):
        if(self.connected):
            resp = self.recv()
            if(resp['op'] != 'error'): 
                if(resp['object']['className'] == 'ProductCatalog'): return {'action': 'UpdateProducts'}
                elif(resp['object']['className'] == 'GerminationSystems' or resp['object']['className'] == 'ProductionSystems'): return {'action': 'UpdateWorklist'}
                elif(resp['object']['className'] == 'GerminationSpaces'): return {'action': 'UpdateSpaces', 'object': resp['object']}
                else: 
                    self.writeLog('info,{}'.format(resp))
                    return {'action': ''}
            elif(resp['op'] == 'error' and resp['type'] != 'timeOut'): return {'action': 'error', 'error': resp['error']}
            else: return {'action': ''}
        else: 
            self.reconnect()
            return {'action': ''}