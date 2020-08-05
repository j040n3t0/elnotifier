#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import os, time

def elastic_search(index,field,value,timerefresh):
    file = open("/opt/elnotifier/elasticserver.txt", "r")
    elasticIP = file.read()
    #Remover ultimo caracter
    elasticIP = elasticIP[:-1]
    es = Elasticsearch([elasticIP],timeout=5)

    doc = {
        'index': index,
        'field': field,
        'value': value,
        'timerefresh': timerefresh,
    }

    # print("\n\n" + str(doc) + "\n\n")
    index = str(doc['index'])
    field = str(doc['field'])
    value = str(doc['value'])
    
    res = es.search(index=index, body={"query": {
                                        "bool": { 
                                            "must": { 
                                                "query_string": { 
                                                    "query": ""+field+": "+value+"" }
                                            },
                                        "filter": {
                                            "range": {
                                                "@timestamp": {
                                                    "gt": "now-"+timerefresh+"s",
                                                    "lt": "now"
                                                }
                                            }
                                        }}}})
    #	res = es.search(index="usuarios", body={"query": {"match_all": {}}})
    # print("\n\n" + str(res) + "\n\n") 
    # print(res)
    # print("Got %d Hits" % res['hits']['total']['value'])
    hits = res['hits']['total']['value']
    result_list = []
    last_value = ""
    for hit in res['hits']['hits']:
        # print(hit)
        # print("\n\n>> ")
        # print(hit["_source"]["message"])
        # print("\n\n")
        #print "ID: %s " % hit["_id"]
    
        try:
            if "heartbeat" in hit["_index"]:
                result_list.append("ALERT!!\nA pesquisa no index %s por %s igual a %s retornou True!" % (hit["_index"], field ,value))
                last_value = str(hit["_source"]["url"]["domain"])
            
            else:
                # print("ID: %s | field: %s e value: %s" % (hit["_index"], field ,hit["_source"][field]))
                result_list.append("ALERT!!\nA pesquisa no index %s por %s igual a %s retornou True!" % (hit["_index"], field ,value))
                last_value = str(hit["_source"][field])
                last_value = last_value.replace("\"","")
        except:
            result_list.append("Ups... Something is wrong with %s" %field)
            last_value = "This Field is not available. Please report it!"
        
        
    
    return result_list, hits, last_value


def sendAlert(message,chatid,bottoken,hits,last_value):
    # print(message)
    # print(chatid)
    # print(bottoken)
    message = message + "\nQtd hits: %s" % hits
    message = message + "\n\nLast value: %s" % last_value


    os.system("curl -s -X POST \
        -H 'Content-Type: application/json' \
        -d '{\"chat_id\": %s, \"text\": \"%s\", \"disable_notification\": true}' \
        https://api.telegram.org/bot%s/sendMessage >> /dev/null" % (chatid,message,bottoken))

def load_config():
    try:
        file = open("/opt/elnotifier/elasticserver.txt", "r")
        elasticIP = file.read()
        #Remover ultimo caracter
        elasticIP = elasticIP[:-1]
        #print(elasticIP)
        es = Elasticsearch([elasticIP])
        if not es.ping():
            return("not found!")
        else:
            res = es.search(index="config-notifier", body={"query": {"match_all": {}}})
            result_list = []
            for hit in res['hits']['hits']:
                result_list.append("address: %s | timerefresh: %s | bottoken: %s | chatid: %s " % (hit["_source"]["address"],hit["_source"]["timerefresh"],hit["_source"]["bottoken"],hit["_source"]["chatid"]))
            
            try:
                res2 = es.search(index="alert-notifier", body={"query": {"match_all": {}}})
                result_alert = []
                for hit in res2['hits']['hits']:
                    result_alert.append("index;%s;field;%s;value;%s;" % (hit["_source"]["index"],hit["_source"]["field"],hit["_source"]["value"]))
            except:
                result_alert = ""
            return(result_list,result_alert)
    except:
        return("not found!")

while True:

    config,alerts = load_config()

    argumments = config[0].split(" ")
    timerefresh = argumments[4]
    bottoken  = argumments[7]
    chatid = argumments[10]

    for i in alerts:
        argumments = i.split(";")
        print(argumments)
        index = argumments[1]
        field = argumments[3]
        value = argumments[5]
        message,hits,last_value = elastic_search(index,field,value,timerefresh)
        #print(message[0])
        if int(hits) > 0:
            print("\n\nMESSAGE: "+message[0]+"\n\n")
            sendAlert(message[-1],chatid,bottoken,hits,last_value)

    # print("[*] Running: %s" % str(datetime.today()))
    #print(datetime.today() - timedelta(seconds=int(timerefresh)))
    time.sleep(int(timerefresh))

