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
    es = Elasticsearch([elasticIP])

    doc = {
        'index': index ,
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
                                                "term": { ""+field+"": ""+value+"" }
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
    #print "\n\n" + str(res) + "\n\n" 
    # print(res)
    # print("Got %d Hits" % res['hits']['total']['value'])
    hits = res['hits']['total']['value']
    result_list = []
    for hit in res['hits']['hits']:
        # print(hit)
        #print "ID: %s " % hit["_id"]
        # print("ID: %s | field: %s e value: %s" % (hit["_index"], field ,hit["_source"][field]))
        result_list.append("ALERT!!\nA pesquisa no index %s por %s igual a %s retornou True!" % (hit["_index"], field ,value))
    
    return result_list, hits


def sendAlert(message,chatid,bottoken,hits):
    # print(message)
    # print(chatid)
    # print(bottoken)
    message = message + "\nQtd hits: %s" % hits

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
                    result_alert.append("index: %s | field: %s | value: %s " % (hit["_source"]["index"],hit["_source"]["field"],hit["_source"]["value"]))
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
        argumments = i.split(" ")
        index = argumments[1]
        field = argumments[4]
        value = argumments[7]
        message,hits = elastic_search(index,field,value,timerefresh)
        #print(message[0])
        if int(hits) > 0:
            sendAlert(message[0],chatid,bottoken,hits)

    # print("[*] Running: %s" % str(datetime.today()))
    #print(datetime.today() - timedelta(seconds=int(timerefresh)))
    time.sleep(int(timerefresh))

