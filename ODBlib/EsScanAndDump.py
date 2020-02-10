#!/usr/bin/python

import ODBlib.ESindexdump as ESindexdump
from elasticsearch import Elasticsearch,exceptions
import os
import pandas as pd
import ODBconfig
from colorama import Fore
import traceback
import datetime
from ODBlib.ODBhelperfuncs import convertjsondumptocsv, iterate_all, jsonappendfile, updatestatsfile

pd.set_option('display.max_colwidth', -1)
#pd.options.display.width = 0
"""
To do:
1. 
3. mulithread
"""

basepath = ODBconfig.basepath
typelist = ODBconfig.typelist
oldips=ODBconfig.oldips
numfieldsreq = int(ODBconfig.numfieldsrequired)
indicesIwant = ODBconfig.ESindicesIwant #collectionamesIwant = ["users","employees","patients","customers","clients"]

if not basepath:
    basepath = os.path.join(os.getcwd(),"open directory dumps")

if not os.path.exists(basepath):
    os.makedirs(basepath)


def identifyindices(ipaddress,keywordlist=[],typelist=[],ignorelogfile=False,portnumber=9200): #filter indices to ones we care about
    import pandas as pd
    import datetime
    import os
    import json
    import time, msvcrt
    onestocheck=[]

    if os.path.exists(os.path.join(basepath,"ElasticFound.json")):
        with open(os.path.join(basepath,"ElasticFound.json")) as outfile:
            oldjson = json.load(outfile)
            doneips = [x['ipaddress'] for x in oldjson]  # check if already searched IP address

    else:
        doneips = []
        #oldjson = []
    pd.set_option('display.max_colwidth', -1)
    doneips = doneips+oldips
    if ignorelogfile:
        doneips=[]
    if ipaddress in doneips:
        print(F"\033[92mAlready parsed\x1b[0m ES instance at: {ipaddress}. {Fore.LIGHTRED_EX}Leave the poor server alone!{Fore.RESET}\n")
        pass

    else:
        es = Elasticsearch([{'host': ipaddress, 'port': portnumber,"timeout":4,"requestTimeout":2,'retry_on_timeout':True,'max_retries':2}])
        try:
            indexstats = es.cat.indices(format="json")
            print(f"{Fore.GREEN}Connection made{Fore.RESET}, now grabbing indices...")
            df = pd.DataFrame.from_dict(indexstats)
            indextotal = df[df['docs.count'].notnull()]['docs.count'].astype(int).sum()
            print (f"    Found\033[94m {str(len(indexstats))}\x1b[0m indices with total of \033[94m{indextotal:,d}\x1b[0m documents")

            all = []
            item ={}
            item['ipaddress']= ipaddress
            item["time_check"]=str(datetime.datetime.now())
            item["indices"]=indexstats
            all.append(item)
            for x in indexstats:
                indexName = x['index']
                indicesdontwant=["beat-","_sample_data","apm-","metrics__","charts__"] #ignore indices that are prob just logs, feel free to add more items to this list. or delete some. whatever


                if not any(x in indexName for x in indicesdontwant) and not indexName.startswith("."):#avoid system indices and ones that usually have BS logging

                    if x['docs.count']: #check to see if docs.count is not None
                        if int(x['docs.count']) > 100: #only worry about indices with more than 100 documents
                            if indicesIwant: #check if there is list of index names I want to filter to
                                if any(z in indexName for z in indicesIwant):
                                    mapping = es.indices.get_mapping(index=indexName)  # get all fields in index
                                    keyfields = set(
                                        list(iterate_all(mapping)))  # iterate through nested json and pull all fields
                                    keyfields = [z.lower() for z in keyfields]
                                    if typelist:  # usually want to just go through indices and look for interesting fields
                                        if len([x for x in keyfields if any(y in x for y in
                                                                        typelist)])>=numfieldsreq:  # look for fields like phone, email etc and then if find them add that index to list, only if two or more fields are present
                                            if "test" not in x["index"]:  # forget about indice that are tests
                                                onestocheck.append(F"{x['index']}??|??{x['docs.count']}")
                                    elif keywordlist:  # but if for whatever reason want to just look at indices with certain names, we can do below
                                        if any(y in x['index'].lower() for y in
                                               keywordlist):  # check if kw in indexname
                                            onestocheck.append(F"{x['index']}??|??{x['docs.count']:,d}")
                            else: #if dont care about names of index do this. Need to clean this up but good for now
                                mapping=es.indices.get_mapping(index=indexName) #get all fields in index
                                keyfields = set(list(iterate_all(mapping))) #iterate through nested json and pull all fields
                                keyfields = [z.lower() for z in keyfields]
                                if typelist: #usually want to just go through indices and look for interesting fields
                                    if [x for x in keyfields if any(y in x for y in typelist)]: #look for fields like phone, email etc and then if find them add that index to list
                                        if "test" not in x["index"]: #forget about indice that are tests
                                            onestocheck.append(F"{x['index']}??|??{x['docs.count']}")
                                elif keywordlist: #but if for whatever reason want to just look at indices with certain names, we can do below
                                    if any(y in x['index'].lower() for y in keywordlist): #check if kw in indexname
                                        onestocheck.append(F"{x['index']}??|??{x['docs.count']}")
            ok = [x.replace("??|??"," | ") for x in onestocheck]
            ok = "\n        "+"\n        ".join(ok)
            print(F"    Found \033[91m{str(len(onestocheck))}\x1b[0m indices that have fields that match your desired fields: {ok}")

            #newjson = oldjson+all #
            jsonappendfile(os.path.join(basepath,"ElasticFound.json"),all)
            #with open(os.path.join(basepath,"ElasticFound.json"), 'w') as outfile:
             #   outfile.write(json.dumps(newjson))
        except exceptions.ConnectionError:
            print(f"    {Fore.LIGHTGREEN_EX}Bummer{Fore.RESET}, connection to {Fore.LIGHTRED_EX}{ipaddress} {Fore.RESET}timed out after {Fore.LIGHTBLUE_EX}3{Fore.RESET} tries.")
        except Exception as e:
            fullError = traceback.format_exc()

            with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
                outfile.write(f"\n{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")
            print(F"Issue with {Fore.RED}{x}{Fore.RED} (check logs for more info)")
        if len(onestocheck)>20: #added this as sometimes got list back of obviously bad dbs but cant create rule for everythign otherwise will rule out good dbs
            timeout = 10
            startTime = time.time()
            inp = None
            print(f"\nSeems found {Fore.LIGHTBLUE_EX}{str(len(onestocheck))}{Fore.RESET} databases which may imply found bunch of BS dbs. \n    If you want to skip this server just {Fore.RED}hit 'esc' key {Fore.RESET}in next 10 seconds or forever hold your peace.")
            while True:
                print(round(time.time() - startTime), end="\r")

                if msvcrt.kbhit():
                    inp = msvcrt.getwch()
                    if inp == chr(27):
                        break
                elif time.time() - startTime > timeout:
                    break

            if inp == chr(27):
                print(f"\n{Fore.LIGHTGREEN_EX}Got it, skipping this server...{Fore.RESET}")
                onestocheck =[]
            else:
                print("Ok, gonna grab em all then, but don't say I didn't warn you...")

        return onestocheck


def main(ipaddress,Icareaboutsize=True,portnumber=9200,ignorelogs=False,csvconvert=False,index=""):
    print(F"Starting scan of ES instance at \033[94m{ipaddress}:{str(portnumber)}\x1b[0m")
    portnumber = int(portnumber) #make sure port is INT otherwise wont work right
    indicestodump =""
    done=[]
    if index:
        indicestodump = [f"{index}??|??0"]
    else:
        try:
            indicestodump = identifyindices(ipaddress,portnumber=portnumber,typelist=typelist,ignorelogfile=ignorelogs)
        except Exception as e:
            fullError = traceback.format_exc()

            with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
                outfile.write(f"{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")
            print(f"{ipaddress} {Fore.RED}had an issue (check logs for more info){Fore.RESET}")
    toobig = []
    count = 0
    if indicestodump:
        for x in indicestodump:
            indexName,docCount = x.split("??|??")
            if Icareaboutsize:
                if int(docCount)>800000:
                    print(F"\n    {Fore.LIGHTRED_EX}{indexName}{Fore.RESET} has \033[94m{int(docCount):,d}\x1b[0m docs! Added info to {Fore.CYAN}'Elastictoobig.json'{Fore.RESET}. Set 'nosizelimit' flag, if you want it")
                    try:
                        es = Elasticsearch([{'host': ipaddress, 'port': portnumber, "timeout": 1, "requestTimeout": 2,
                                             'retry_on_timeout': True, 'max_retries': 3}])

                        results = es.search(index=indexName, scroll="1m", size=5)
                        sample= [x["_source"] for x in results['hits']['hits']]
                    except:
                        sample=["Error getting sample record"]
                    item = {}
                    item['server'] = f"{ipaddress}:{portnumber}"
                    item["index"] = indexName
                    item["date_checked"] = str(datetime.datetime.now())
                    item["docCount"] = docCount
                    item["SampleItems"] = sample
                    toobig.append(item)

                else:
                    try:
                        ESindexdump.newESdump(ipaddress,indexName,os.path.join(basepath, ipaddress),portnumber=portnumber)

                        count += int(docCount)
                        done.append(indexName)
                    except Exception as e:
                        fullError = traceback.format_exc()

                        with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
                            outfile.write(f"{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")
                        print(F"    {indexName} {Fore.RED}had an issue (check logs for more info){Fore.RESET}")
            else:
                try:
                    ESindexdump.newESdump(ipaddress, indexName, os.path.join(basepath, ipaddress),
                                          portnumber=portnumber)

                    count+=int(docCount)
                    done.append(indexName)
                except Exception as e:
                    fullError = traceback.format_exc()

                    with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
                        outfile.write(f"{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")
                    print(F"{indexName} had an issue (check logs for more info)")
            if csvconvert: #ok so you want to convert json to csv, fine
                if os.path.isfile(os.path.join(basepath,ipaddress,f"{ipaddress}_{indexName}_ES.json")): #check if the file exists first
                    convertjsondumptocsv(os.path.join(basepath,ipaddress,f"{ipaddress}_{indexName}_ES.json"))
                    print(f"{Fore.LIGHTGREEN_EX}        Converted{Fore.RESET} dump to CSV for you...")

        if toobig:
            jsonappendfile(os.path.join(basepath,"Elastictoobig.json"),toobig)
        if index:
            count1 = "whatever it says above"
        else:
            count1= f"{count:,d}"
        print(F"\n{Fore.LIGHTGREEN_EX}Server Summary:{Fore.RESET} Succesfully dumped \033[94m{str(len(done))}\x1b[0m databases with a total of \033[94m{count1}\x1b[0m records.\n")
    else:
       pass
    print(f'{Fore.RED}#############################################\n{Fore.RESET}')
    return (len(done),count)


def singleclustergrab(ipaddress,portnumber=9200,careaboutsize=True,ignorelogs=False,convertTOcsv=False,index=""):
    donedbs = 0
    totalrecords = 0

    donecount, recordcount = main(ipaddress,portnumber=portnumber,Icareaboutsize=careaboutsize,ignorelogs=ignorelogs,csvconvert=convertTOcsv,index=index)
    donedbs += donecount
    totalrecords += recordcount
    updatestatsfile(donedbs, totalrecords, 1)

    if not index:
        print('###########-----\033[91mCluster Summary\x1b[0m-----################\n')
        print(F"  Succesfully dumped \033[94m{str(donedbs)}\x1b[0m databases with a total of \033[94m{totalrecords:,d}\x1b[0m records. \n            YOU ARE WELCOME.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", '-ip', help="grab one IP")
    parser.add_argument("--ignore", '-i', action='store_true', help="add this flag to ignore ES log and rescrape server")

    args = parser.parse_args()

    if args.ip:
        ip = args.ip
        ip = ip.strip("/https//:")
        singleclustergrab(ip)

