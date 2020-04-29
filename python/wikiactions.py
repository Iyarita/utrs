import mysql.connector
from mysql.connector import Error
import credentials
import re
import hashlib
from datetime import datetime,timedelta

import mwclient
import login

masterwiki =  mwclient.Site('en.wikipedia.org')
masterwiki.login(login.username,login.password)
metawiki =  mwclient.Site('meta.wikimedia.org')
metawiki.login(login.username,login.password)
ptwiki =  mwclient.Site('pt.wikipedia.org')
ptwiki.login(login.username,login.password)

regex = "((^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$))"

def callAPI(params):
    return masterwiki.api(**params)

def callmetaAPI(params):
    return metawiki.api(**params)

def callptwikiAPI(params):
    return ptwiki.api(**params)

def calldb(command,style):
    try:
        print command
        connection = mysql.connector.connect(host=credentials.ip,
                                             database=credentials.database,
                                             user=credentials.user,
                                             password=credentials.password)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(command)
            if style == "read":
                record = cursor.fetchall()
            if style == "write":
                connection.commit()
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
        if style == "read":return record
        else:return "Done"
def verifyusers():
    results = calldb("select * from wikitasks where task = 'verifyaccount';","read")
    for result in results:
        wtid=result[0]
        user = result[2]
        userresults = calldb("select * from users where id = '"+str(user)+"';","read")
        for userresult in userresults:
            username = userresult[1]
            if username == None:continue
            params = {'action': 'query',
            'format': 'json',
            'meta': 'tokens'
            }
            raw = callAPI(params)
            try:code = raw["query"]["tokens"]["csrftoken"]
            except:
                print raw
                print "FAILURE: Param not accepted."
                quit()
            mash= username+credentials.secret
            confirmhash = hashlib.md5(mash.encode()) 
            params = {'action': 'emailuser',
            'format': 'json',
            'target': username,
            'subject': 'UTRS Wiki Account Verification',
            'token': code.encode(),
            'text': 
"""
Thank you for registering your account with UTRS. Please verify your account by going to the following link.

http://utrs-beta.wmflabs.org/verify/"""+str(confirmhash.hexdigest())+"""

Thanks,
UTRS Developers"""
            }
            raw = callAPI(params)
            calldb("update users set u_v_token = '"+confirmhash.hexdigest()+"' where id="+str(user)+";","write")
            calldb("delete from wikitasks where id="+str(wtid)+";","write")
            checkPerms(username,user)
def checkPerms(user, id):
    enperms = {"user":False,"sysop":False,"checkuser":False,"oversight":False}
    ptperms = {"user":False,"sysop":False,"checkuser":False,"oversight":False}
    metaperms = {"user":False,"steward":False,"staff":False}
    ##############################
    ###Enwiki checks##############
    params = {'action': 'query',
            'format': 'json',
            'list': 'users',
            'ususers': user,
            'usprop': 'groups|editcount'
            }
    raw = callAPI(params)
    results = raw["query"]["users"][0]["groups"]
    for result in results:
        if "sysop" in result:
            enperms["sysop"]=True
        if "checkuser" in result:
            enperms["checkuser"]=True
        if "oversight" in result:
            enperms["oversight"]=True
    editcount = raw["query"]["users"][0]["editcount"]
    if editcount >500:enperms["user"]=True
    ##############################
    ###Ptwiki checks##############
    raw = callptwikiAPI(params)
    results = raw["query"]["users"][0]["groups"]
    for result in results:
        if "sysop" in result:
            ptperms["sysop"]=True
        if "checkuser" in result:
            ptperms["checkuser"]=True
        if "oversight" in result:
            ptperms["oversight"]=True
    editcount = raw["query"]["users"][0]["editcount"]
    if editcount >500:ptperms["user"]=True
    ##############################
    ###Meta checks##############
    params = {'action': 'query',
            'format': 'json',
            'list': 'globalallusers',
            'agufrom': user,
            'agulimit':1,
            'aguprop': 'groups'
            }
    raw = callmetaAPI(params)
    results = raw["query"]["globalallusers"][0]["groups"]
    for result in results:
        if "steward" in result:
            metaperms["steward"]=True
        if "staff" in result:
            metaperms["staff"]=True
    params = {'action': 'query',
            'format': 'json',
            'list': 'users',
            'ususers': user,
            'usprop': 'editcount'
            }
    raw = callptwikiAPI(params)
    editcount = raw["query"]["users"][0]["editcount"]
    if editcount >500:metaperms["user"]=True
    ###################################
    ###Set allowed Wikis###############
    string = ""
    if enperms['user']:
        string += "enwiki"
    if ptperms['user']:
        if string != "":string +=",ptwiki"
        else:string +="ptwiki"
    if metaperms['user']:
        if string != "":string +=",global"
        else:string +="global"
    calldb("update users set wikis = '"+string+"' where id="+str(id)+";","write")
    ###################################
    ###Set permissions#################
    if enperms['user']:
        calldb("insert into permissions (userid,wiki,oversight,checkuser,admin,user) values ("+str(id)+",'enwiki',"+str(int(enperms["oversight"]))+","+str(int(enperms["checkuser"]))+","+str(int(enperms["sysop"]))+",1);","write")
    if ptperms['user']:
        calldb("insert into permissions (userid,wiki,oversight,checkuser,admin,user) values ("+str(id)+",'ptwiki',"+str(int(ptperms["oversight"]))+","+str(int(ptperms["checkuser"]))+","+str(int(ptperms["sysop"]))+",1);","write")
    if metaperms['user']:
        calldb("insert into permissions (userid,wiki,steward,staff,user) values ("+str(id)+",'*',"+str(int(metaperms["steward"]))+","+str(int(metaperms["staff"]))+",1);","write")
def verifyblock():
    results = calldb("select * from appeals where status = 'VERIFY';","read")
    for appeal in results:
        target = appeal[1]
        wiki=appeal[13]
        if wiki == "enwiki" or wiki == "ptwiki":
            if not re.match(regex,target):
                params = {'action': 'query',
                'format': 'json',
                'list': 'blocks',
                'bkusers': target
                }
                raw = runAPI(wiki, params)
                if len(raw["query"]["blocks"])>0:
                    updateBlockinfoDB(raw,appeal)
                    continue
                else:
                    calldb("update appeals set status = 'NOTFOUND' where id="+str(appeal[0])+";","write")
                    blockNotFound(target,wiki,appeal[0])
            else:
                params = {'action': 'query',
                'format': 'json',
                'list': 'blocks',
                'bkip': target
                }
                raw = runAPI(wiki, params)
                if len(raw["query"]["blocks"])>0:
                    updateBlockinfoDB(raw,appeal)
                    continue
                else:
                    params = {'action': 'query',
                    'format': 'json',
                    'list': 'blocks',
                    'bkids': target
                    }
                    raw = runAPI(wiki, params)
                    if len(raw["query"]["blocks"])>0:
                        updateBlockinfoDB(raw,appeal)
                        continue
                    else:
                        calldb("update appeals set status = 'NOTFOUND' where id="+str(appeal[0])+";","write")
                        if re.match(regex,appeal[0]) == None:blockNotFound(target,wiki,appeal[0])
                        continue
        if wiki == "global":
            params = {'action': 'query',
            'format': 'json',
            'list': 'globalallusers ',
            'agufrom': target,
            'agulimit':1,
            'aguprop':'lockinfo'
            }
            raw = runAPI(wiki, params)
            try:
                if raw["query"]["globalallusers"][0]["locked"]=="":locked=True
                params = {'action': 'query',
                'format': 'json',
                'list': 'logevents',
                'lefrom': "User:"+target+"@global",
                'letype':'globalauth',
                'lelimit':1,
                'leprop':'user|comment'
                }
                raw = runAPI(wiki, params)
                updateBlockinfoDB(raw,appeal)
                continue
            except:
                params = {'action': 'query',
                'format': 'json',
                'list': 'globallocks ',
                'bgip': target,
                'bglimit':1,
                'bgprop':'lockinfo'
                }
                raw = runAPI(wiki, params)
                if len(raw["query"]["globalblocks"])>0:
                    updateBlockinfoDB(raw,appeal)
                    continue
                else:
                    calldb("update appeals set status = 'NOTFOUND' where id="+str(appeal[0])+";","write")
                    if re.match(regex,appeal[0]) == None:blockNotFound(target,wiki,appeal[0])
                    continue
def blockNotFound(username,wiki,id):
    print "Block not found email: " + username
    mash= username+credentials.secret
    confirmhash = hashlib.md5(mash.encode()) 
    subject="UTRS Appeal #"+str(id)+" - Block not found"
    text="""
Your block that you filed an appeal for on the UTRS Platform has not been found. Please verify the name or IP address being blocked.

http://utrs-beta.wmflabs.org/fixblock/"""+str(confirmhash)+"""

Thanks,
UTRS Developers"""
    sendemail(username,subject,text,wiki)

def runAPI(wiki, params):
    if wiki == "enwiki":raw = callAPI(params)
    if wiki == "ptwiki":raw = callptwikiAPI(params)
    if wiki == "global":raw = callmetaAPI(params)
    return raw
def updateBlockinfoDB(raw,appeal):
    calldb("update appeals set blockfound = 1 where id="+str(appeal[0])+";","write")
    calldb("update appeals set blockingadmin = '"+raw["query"]["blocks"][0]["by"]+"' where id="+str(appeal[0])+";","write")
    calldb("update appeals set blockreason = '"+raw["query"]["blocks"][0]["reason"]+"' where id="+str(appeal[0])+";","write")
    results = calldb("select * from appeals where status = 'VERIFY';","read")
    if results[0][2] != results[0][3]:calldb("update appeals set status = \"PRIVACY\" where id="+str(appeal[0])+";","write")
    else:calldb("update appeals set status = \"OPEN\" where id="+str(appeal[0])+";","write")
def sendemail(target,subject,text,wiki):
    params = {'action': 'query',
            'format': 'json',
            'meta': 'tokens'
            }
    raw = runAPI(wiki, params)
    try:code = raw["query"]["tokens"]["csrftoken"]
    except:
        print raw
        print "FAILURE: Param not accepted."
        quit()
    params = {'action': 'emailuser',
    'format': 'json',
    'target': target,
    'subject': subject,
    'token': code.encode(),
    'text': text
            }
    raw = callAPI(params)
def clearPrivateData():
    results = calldb("select * from privatedatas;","read")
    for result in results:
        appeal = calldb("select * from appeal where id = "+str(result['id'])+";","read")
        if appeal[0]['status'] != "CLOSED":continue
        logs = calldb("select timestamp from logs where referenceobject = "+str(result[id])+" and action = 'closed' and objecttype = 'appeal';","read")
        timediff = datetime.strptime(logs[0]["timestamp"], '%Y-%m-%d %H:%M:%S') - timedelta(days=7)
        if timediff.days > 7:
            calldb("delete from privatedatas where appealID = "+str(result['id'])+";","write")
verifyusers()
verifyblock()
clearPrivateData()
