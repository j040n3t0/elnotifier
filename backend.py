# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, Response, jsonify
import os, subprocess
from elasticsearch import Elasticsearch

app = Flask(__name__)

###
def runDaemon():
    process_cmd = subprocess.Popen(['ps -aux |grep alertdaemon'], stdout=subprocess.PIPE, shell=True)
    (process, err) = process_cmd.communicate()
    if "alertdaemon.py" in str(process):
        # print("TEMOS QUE MATALO")
        # kill = str(process)
        # kill = kill.split(" ")
        # print(kill[1])
        # os.system("kill -9 %s" % kill[1])
        os.system('/usr/bin/pkill -f "/opt/elnotifier/alertdaemon.py"')
        subprocess.call(["/opt/elnotifier/alertdaemon.py"])
    else:
        subprocess.call(["/opt/elnotifier/alertdaemon.py"])
        print("TEMOS QUE INICIAR")
        


def update_config(address,timerefresh,bottoken,chatid):
    os.system("echo %s > /opt/elnotifier/elasticserver.txt" % address)
    
    print("To na funcao!")
    es = Elasticsearch([address],timeout=5)
    #print(es)
    
    # ignore 400 cause by IndexAlreadyExistsException when creating an index
    # es.indices.create(index='config-notifier', ignore=400)
    
    doc = {
        'address': address,
        'timerefresh': timerefresh,
        'bottoken': bottoken,
        'chatid': chatid,
    }

    print(doc)
    
    res = es.index(index="config-notifier", body=doc, id=1)
    print(res['result'])
    es.indices.refresh(index="config-notifier")
    runDaemon()
    print("Final da Funcao!")

def check_config():
    try:
        file = open("/opt/elnotifier/elasticserver.txt", "r")
        elasticIP = file.read()
        #Remover ultimo caracter
        elasticIP = elasticIP[:-1]
        #print(elasticIP)
        es = Elasticsearch([elasticIP],timeout=2)
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
                    result_alert.append("id;%s;index;%s;field;%s;value;%s;" % (hit["_id"],hit["_source"]["index"],hit["_source"]["field"],hit["_source"]["value"]))
            except:
                result_alert = ""
            return(result_list,result_alert)
    except:
        return("not found!")

def saveNewAlert(index,field,value,address):
    es = Elasticsearch([address],timeout=5)
    
    doc = {
        'address': address,
        'index': index,
        'field': field,
        'value': value,
    }

    print("\n\n --DOC-- \n\n %s" % doc)
    
    res = es.index(index="alert-notifier", body=doc)
    print(res['result'])
    es.indices.refresh(index="alert-notifier")
    runDaemon()
    print("Final da Função!")


def elastic_delete(id):
    file = open("/opt/elnotifier/elasticserver.txt", "r")
    elasticIP = file.read()
    #Remover ultimo caracter
    elasticIP = elasticIP[:-1]
    es = Elasticsearch([elasticIP])
    res = es.delete(index="alert-notifier", id=id)
    runDaemon()
    print(res['result'])

###
@app.route('/')
def home():
	# serve index template
	return render_template('index.html')

@app.route("/process", methods=["POST"])
def process():
    print(request.form)
    try:
        address = request.form['address']
        timerefresh = request.form['timerefresh']
        bottoken = request.form['bottoken']
        chatid = request.form['chatid']
        print(address,timerefresh,bottoken,chatid)
        update_config(address,timerefresh,bottoken,chatid)
        return jsonify({'output' : 'Configuracao realizada com sucesso!'}) 
    except:
        return jsonify({'output' : 'Falha na conexao com o servidor!'}) 

@app.route("/getConfig", methods=["POST"])
def getConfig():
    # print(request.form)
    # print("Initial Configure")
    try:
        config,alerts = check_config()
        # print(config)
        # print(alerts)
        if config == "not found!":
            return jsonify({'output' : 'Falha na configuracao!'}) 
        else:
            return jsonify({'output' : config,
            'alerts': alerts}) 
    except:
        return jsonify({'output' : 'Falha na configuracao!'}) 

@app.route("/saveAlert", methods=["POST"])
def saveAlert():
    index = request.form['index']
    field = request.form['field']
    value = request.form['value']
    address = request.form['address']
    message = "Alerta Salvo -> Index: %s | Field: %s | Value: %s" % (index,field,value)
    print("\n\n"+ message+"\n\n")
    saveNewAlert(index,field,value,address)
    return jsonify({'output' : message})

@app.route("/removeAlert", methods=["POST"])
def removeAlert():
    print("VAMOS DELETAR!!!")
    id_filter = str(request.data)
    id_filter = id_filter.split('"')
    id_filter = id_filter[6]
    id_filter = id_filter.split("\\")
    elastic_delete(id_filter[0])
    return jsonify({'output' : "DELETE ON"})



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
