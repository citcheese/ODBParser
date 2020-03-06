#!/usr/bin/python

import ODBlib.ESindexdump as ESindexdump
from elasticsearch import Elasticsearch,exceptions
import os,sys
import pandas as pd
import ODBconfig
from colorama import Fore
import traceback
import datetime
from ODBlib.ODBhelperfuncs import convertjsondumptocsv, iterate_all, jsonappendfile,checkifIPalreadyparsed
from tqdm import tqdm

pd.set_option('display.max_colwidth', -1)
#pd.options.display.width = 0

basepath = ODBconfig.basepath
typelist = ODBconfig.typelist
numfieldsreq = int(ODBconfig.numfieldsrequired)
indicesIwant = ODBconfig.ESindicesIwant #collectionamesIwant = ["users","employees","patients","customers","clients"]
indicesdontwant = ODBconfig.ESindicesdontwant

if not basepath:
    basepath = os.path.join(os.getcwd(),"open directory dumps")

if not os.path.exists(basepath):
    os.makedirs(basepath)


def identifyindices(ipaddress,portnumber=9200,indicesIwant=indicesIwant): #filter indices to ones we care about
    import pandas as pd
    import datetime
    import os
    import time
    if sys.platform == "win32":
        import msvcrt
    onestocheck=[]

    es = Elasticsearch([{'host': ipaddress, 'port': portnumber,"timeout":10,"requestTimeout":2,'retry_on_timeout':True,'max_retries':2}])
    x=""
    indexName=ipaddress
    try:
        indexstats = es.cat.indices(format="json")
        print(f"{Fore.GREEN}Connection made{Fore.RESET}, now grabbing indices...")
        df = pd.DataFrame.from_dict(indexstats)
        indextotal = df[df['docs.count'].notnull()]['docs.count'].astype(int).sum()
        orig = len(indexstats)
        all = []
        item ={}
        item['ipaddress']= ipaddress
        item["port"]=portnumber
        item["time_check"]=str(datetime.datetime.now())
        item["indices"]=indexstats #lets add keys here
        all.append(item)

        indexstats =[x for x in indexstats if not any(y in x["index"] for y in indicesdontwant) and not x["index"].startswith(".")] #ignore system indices and ones that usually have BS logging
        print (f"    Found\033[94m {orig:,d}\x1b[0m indices with total of \033[94m{indextotal:,d}\x1b[0m documents (ignoring {Fore.LIGHTBLUE_EX}{orig - len(indexstats)}{Fore.RESET} of them as per configfile)")

        t = tqdm(indexstats, leave=True)
        t.refresh()
        for x in t:
            indexName = x['index']
            if len(indexName)>24:
                spacing = 25
            else:
                spacing = len(indexName)
            t.set_description_str(F"        Parsing {Fore.CYAN}{indexName[:24]}{Fore.RESET} { ' ' * (25-spacing)}")

            try:
                mapping = es.indices.get_mapping(index=indexName)  # get all fields in index
                keyfields = set(
                    list(iterate_all(mapping)))  # iterate through nested json and pull all fields
                keyfields = [z.lower() for z in keyfields]
                x["db_fields"] = keyfields #add fields to server dict which will get written to file
                if x['docs.count']: #check to see if docs.count is not None
                    if int(x['docs.count']) > 50: #only worry about indices with more than 100 documents

                        if indicesIwant: #check if there is list of index names I want to filter to
                            if any(z in indexName for z in indicesIwant):

                                if typelist:  # usually want to just go through indices and look for interesting fields
                                    if len([x for x in typelist if any(x in y for y in keyfields)])>=numfieldsreq:  # look for fields like phone, email etc and then if find them add that index to list, only if two or more fields are present. or to swap logic keyfields if any(y in x for y in typelist)]
                                        if "test" not in x["index"]:  # forget about indice that are tests
                                            onestocheck.append(F"{x['index']}??|??{int(x['docs.count']):,d}")
                                else:
                                    onestocheck.append(F"{x['index']}??|??{int(x['docs.count']):,d}")
                        else: #if dont care about names of index do this. Need to clean this up but good for now

                            if typelist: #usually want to just go through indices and look for interesting fields
                                if len([x for x in typelist if any(x in y for y in keyfields)])>=numfieldsreq: #look for fields like phone, email etc and then if find them add that index to list
                                    if "test" not in x["index"]: #forget about indice that are tests
                                        onestocheck.append(F"{x['index']}??|??{int(x['docs.count']):,d}")
                            else:
                                onestocheck.append(F"{x['index']}??|??{int(x['docs.count']):,d}")
            except Exception as e:
                fullError = traceback.format_exc()

                with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
                    outfile.write(
                        f"\n{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")

                pass
        t.close()
        ok = [x.replace("??|??",f" {Fore.CYAN}|{Fore.RESET} ") for x in onestocheck]
        ok = "\n        "+"\n        ".join(ok)
        print(F"    Found \033[91m{str(len(onestocheck))}\x1b[0m indices that have fields that match what you want: {ok}")

        jsonappendfile(os.path.join(basepath,"ElasticFound.json"),all)

    except exceptions.ConnectionError:
        print(f"    {Fore.GREEN}Bummer{Fore.RESET}, connection to {Fore.LIGHTRED_EX}{ipaddress} {Fore.RESET}timed out after {Fore.LIGHTBLUE_EX}3{Fore.RESET} tries.")
    except Exception as e:
        fullError = traceback.format_exc()

        with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
            outfile.write(f"\n{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")
        print(F"Issue with {Fore.RED}{indexName}{Fore.RESET} (check logs for more info)")
    if sys.platform == "win32": #check if user has windows otherwise below will result in error
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
                print(f"\n{Fore.GREEN}Got it, skipping this server...{Fore.RESET}")
                onestocheck =[]
            else:
                print("Ok, gonna grab em all then, but don't say I didn't warn you...")

    return onestocheck


def main(ipaddress,Icareaboutsize=True,portnumber=9200,ignorelogs=False,csvconvert=False,index="",getall=False):
    portnumber = int(portnumber) #make sure port is INT otherwise wont work right
    indicestodump =""


    done=[]
    if index:
        print(F"Starting scan of ES instance at \033[94m{ipaddress}:{str(portnumber)}\x1b[0m")

        indicestodump = [f"{index}??|??0"]
    elif getall:
        print(F"Starting scan of ES instance at \033[94m{ipaddress}:{str(portnumber)}\x1b[0m")

        es = Elasticsearch([{'host': ipaddress, 'port': portnumber,"timeout":10,"requestTimeout":2,'retry_on_timeout':True,'max_retries':2}])

        indexstats = es.cat.indices(format="json")
        indicestodump = [F"{x['index']}??|??{int(x['docs.count']):,d}" for x in indexstats]

    else:
        if not ignorelogs:
            if checkifIPalreadyparsed(ipaddress,dbtype="Elastic"):
                print(
                    F"{Fore.GREEN}Already parsed\x1b[0m ES instance at: {ipaddress}. {Fore.LIGHTRED_EX}Leave the poor server alone!{Fore.RESET}\n")
                go = False
            else:
                go = True
        else:
            go = True

        if go:
            try:
                print(F"Starting scan of ES instance at \033[94m{ipaddress}:{str(portnumber)}\x1b[0m")

                indicestodump = identifyindices(ipaddress,portnumber=portnumber)
            except Exception as e:
                fullError = traceback.format_exc()

                with open(os.path.join(basepath, "EsErrors.txt"), 'a') as outfile:
                    outfile.write(f"{ipaddress}:{str(fullError)}\n---------------------------------------------------------\n")
                print(f"    {ipaddress} {Fore.RED}had an issue (check logs for more info){Fore.RESET}")
    toobig = []
    count = 0
    indexcount = 0
    if indicestodump:
        if Icareaboutsize:
            bigones = [x for x in indicestodump if int(x.split("??|??",1)[1].replace(',', ''))>800000] #started changing method to get all sample recrs for toobig and dump right away just in case errors later on
            for z in bigones:
                indexName, docCount = z.split("??|??")
                docCount = int(docCount.replace(',', ''))
                try:
                    es = Elasticsearch([{'host': ipaddress, 'port': portnumber, "timeout": 1, "requestTimeout": 2,
                                         'retry_on_timeout': True, 'max_retries': 3}])

                    results = es.search(index=indexName, scroll="1m", size=5)
                    sample = [x["_source"] for x in results['hits']['hits']]
                except:
                    sample = ["Error getting sample record"]
                item = {}
                item['server'] = f"{ipaddress}:{portnumber}"
                item["index"] = indexName
                item["date_checked"] = str(datetime.datetime.now())
                item["docCount"] = docCount
                item["SampleItems"] = sample
                toobig.append(item)
            if toobig:
                jsonappendfile(os.path.join(basepath, "Elastictoobig.json"), toobig)
                ok = [x.replace("??|??", " | ") for x in bigones]
                ok = "          " + "\n        ".join(ok)
                print(F"    The following indices {Fore.LIGHTGREEN_EX}are too big{Fore.RESET}. Adding info to {Fore.CYAN}'Elastictoobig.json'{Fore.RESET}(Set 'nosizelimit' flag, if you want them): {ok}")

            indicestodump = [x for x in indicestodump if x not in bigones]


        for x in indicestodump:
            indexcount+=1
            indexName,docCount = x.split("??|??")
            docCount = int(docCount.replace(',', ''))

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
                    print(f"{Fore.GREEN}        Converted{Fore.RESET} dump to CSV for you...")

        if index:
            print(F"\n{Fore.GREEN}Server Summary:{Fore.RESET} Database Dump complete.\n")
        else:
            print(F"\n{Fore.GREEN}Server Summary:{Fore.RESET} Succesfully dumped \033[94m{str(len(done))}\x1b[0m databases with a total of \033[94m{count:,d}\x1b[0m records.\n")

    else:
       pass
    print(f'{Fore.RED}#############################################\n{Fore.RESET}')
    return (len(done),count)




