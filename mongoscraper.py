import pymongo
import pandas as pd
import os
import json
from colorama import Fore
import ODBconfig
from bson import json_util
from ODBlib.ODBhelperfuncs import convertjsondumptocsv, jsonappendfile,updatestatsfile,checkifIPalreadyparsed
from tqdm import tqdm


pd.options.display.width = 0


numfieldsreq = int(ODBconfig.numfieldsrequired)
basepath = ODBconfig.basepath
typelist = ODBconfig.typelist
collectionamesIwant = ODBconfig.collectionamesIwant

if not basepath:
    basepath = os.path.join(os.getcwd(),"open directory dumps")

if not os.path.exists(basepath):
    os.makedirs(basepath)


def getCollectionKeys(collection):
    """Get a set of keys from a collection"""
    keys_list = []
    collection_list = collection.find().limit(300) #otherwise pulls all records just to get schema which is bit wasteful. Yea, may miss some field names, but it's good compromise
    for document in collection_list:
        for field in document.keys():
            keys_list.append(field.lower())
    keys_set = set(keys_list)
    return keys_set

def dumpMongoDbcollectiontoCSV(database, collection, dbip,portnumber,convertTOcsv=False):
    client = pymongo.MongoClient(f"mongodb://{dbip}:{str(portnumber)}",
                                 serverSelectionTimeoutMS=5000)  # defaults to port 27017, timeout in ms

    cursor = client[database][collection].find({}, {'_id': False})  # grab all records
    if not os.path.exists(os.path.join(basepath, dbip)):
        os.makedirs(os.path.join(basepath, dbip))

    print(
        f"                Dumping records from {Fore.LIGHTRED_EX}{collection}{Fore.RESET} in {Fore.LIGHTRED_EX}{database} {Fore.RESET}")

    count9 = 0
    with open(os.path.join(basepath, dbip, f"{dbip}_{database}_{collection}_MDB.json"), "w") as f:
        f.write('[')
        for document in cursor:
            f.write(json.dumps(document, default=json_util.default))  # json_util.default))
            f.write(',')
            count9 += 1
            sumt = count9 / 50
            if sumt.is_integer():
                print(f"                    Now writing record: {count9:,d}", end='\r')  # to show some progress of dumping file
        f.seek(0, os.SEEK_END)
        f.seek(f.tell() - 1,
               os.SEEK_SET)  # to avoid switching file mode to binary as discussed here: https://stackoverflow.com/questions/21533391/seeking-from-end-of-file-throwing-unsupported-exception
        f.truncate()
        f.write("]")
    #print(
     #   f"        Dumped {Fore.LIGHTBLUE_EX}{count9:,d}{Fore.RESET} records from {Fore.LIGHTRED_EX}{collection}{Fore.RESET} in {Fore.LIGHTRED_EX}{database} {Fore.RESET}")
    if convertTOcsv:
        if os.path.isfile(os.path.join(basepath, dbip,
                                       f"{dbip}_{database}_{collection}_MDB.json")):  # check if the file exists first
            convertjsondumptocsv(
                os.path.join(basepath, dbip, f"{dbip}_{database}_{collection}_MDB.json"))
            print(f"{Fore.GREEN}        Converted{Fore.RESET} dump to CSV for you...")

    return (count9)


def mongodbscraper(dbip,portnumber=27017,careaboutpwnedcollections=True,careaboutpwneddbs=True,ignorelogfile=False,Icareaboutsize=True,convertTOcsv=False,typelist=typelist,getall=False,getcollection=""):
    import datetime
    global collectionamesIwant
    global basepath
    global numfieldsreq


    doneips = []
    cdict = []

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
        go = True
    else:
        if checkifIPalreadyparsed(dbip, dbtype="Elastic"):
            go = False
        else:
            go = True

    if not go: #ignore IPs that have already been scrapped.
        print(F"\033[92mAlready parsed\x1b[0m MongoDB instance at: {dbip}. {Fore.LIGHTRED_EX}Leave the poor server alone!!{Fore.RESET}")
        pass
    else:
        print(f"{Fore.GREEN}Connecting{Fore.RESET} to db at {Fore.LIGHTRED_EX}{dbip}:{portnumber}{Fore.RESET}...")
        client = pymongo.MongoClient(f"mongodb://{dbip}:{str(portnumber)}",serverSelectionTimeoutMS=5000) # defaults to port 27017, timeout in ms


        try:
            listofdbs = client.list_database_names()
        except Exception as e:
            print(f"    {Fore.LIGHTRED_EX}Error: {Fore.RESET} {str(e)} (error logged)")
            listofdbs = []
            with open(os.path.join(basepath, "MongoErrors.txt"), 'a') as outfile:
                outfile.write(f"{dbip}:{str(e)}\n")
        if getcollection:
            #print("yes")
            db,collection = getcollection.split(":")
            #print(f"Database:{db},{collection}")
            totalrecords = dumpMongoDbcollectiontoCSV(db,collection,dbip,portnumber,convertTOcsv=convertTOcsv)
            cdict = [{"ipaddress": dbip, "databaseinfo": ""}]

            totaldbs = 1

        else:
            if listofdbs:
                toobig = []

                collectionNames = []
                totalnumofcollection=0
                if any(z in listofdbs for z in pwnedDBs):
                    print(f"    {Fore.LIGHTRED_EX}{dbip}{Fore.RESET} has been {Fore.GREEN}PWNED{Fore.RESET}, moving on")
                    pass
                else:
                    #totalcollectionrecords = sum([client[x].command("dbstats")["objects"] for x in listofdbs])
                    print(f"    Found {Fore.LIGHTBLUE_EX}{len(listofdbs)}{Fore.RESET} databases. Now gathering collections in each DB & checking for desired fields:")
                    if getall:
                        typelist = []
                        collectionamesIwant = []
                    for x in listofdbs:
                        collections = client[x].list_collection_names() #to sub collection name as variable is string
                        totalnumofcollection+= len(collections)

                        collections = [x for x in collections if "system." not in x] #filter out mongodob system files
                        if any(z in collections for z in pwnedcollections): #check if any of the collections have been pwned, if so skip the index
                            print(f"        {Fore.LIGHTRED_EX}{x}{Fore.RESET} has been {Fore.GREEN}PWNED{Fore.RESET}, moving on")
                            collections = []
                        else:
                            collectionNames.append({x:collections})

                        if collections:
                            t = tqdm(collections, leave=True)
                            t.refresh()
                            for y in t: #next 3 lines check if term i want is part of collection name
                                t.set_description(
                                    F"        Parsing {Fore.CYAN}{x}{Fore.RESET}:{Fore.LIGHTRED_EX}{y}{Fore.RESET}")
                                if collectionamesIwant:  # check if care about collection names
                                    if any(z in y for z in collectionamesIwant):
                                        if typelist:
                                            collectionkeys = getCollectionKeys(client[x][y])  # get all keys in collection
                                            if len([x for x in collectionkeys if any(y in x for y in typelist)]) > numfieldsreq:
                                                collectionstoget.append((x, y))
                                        else:
                                            collectionstoget.append((x, y))

                                else:
                                    if typelist:

                                        collectionkeys = getCollectionKeys(client[x][y])  # get all keys in collection
                                        if len([x for x in collectionkeys if any(y in x for y in typelist)]) > numfieldsreq:
                                            collectionstoget.append((x, y))
                                    else:
                                        collectionstoget.append((x, y))

                            if collectionstoget:
                                ok = "\n                " + "\n                ".join([f"{Fore.LIGHTRED_EX}{x[1]}{Fore.RESET} in database {Fore.LIGHTRED_EX}{x[0]}{Fore.RESET}" for x in collectionstoget[:5]])
                                print(F"            Found {Fore.LIGHTBLUE_EX}{str(len(collectionstoget))}{Fore.RESET} collections in {Fore.LIGHTRED_EX}{x}{Fore.RESET} that I'll be grabbing including: {ok}")

                                for col in collectionstoget:
                                    db, collection = col
                                    docsize = client[db][collection].estimated_document_count()
                                    if docsize > 50:  # check to see if collection has at least X number of items
                                        if Icareaboutsize:
                                            if docsize < 800000:  # change this number if you want
                                                recordcount = dumpMongoDbcollectiontoCSV(db,collection,dbip,portnumber,convertTOcsv=convertTOcsv)
                                                totalrecords += recordcount
                                                totaldbs += 1

                                            # print(f"        A collection you may want is: {Fore.LIGHTRED_EX}{y} in {x}{Fore.RESET} with {Fore.LIGHTBLUE_EX}{client[x][y].estimated_document_count():,d} {Fore.RESET}documents",end='\r')

                                            else:
                                                item = {}
                                                item['server'] = f"{dbip}:{portnumber}"
                                                item["collection"] = y
                                                item["database"] = x
                                                item["date_checked"] = str(datetime.datetime.now())
                                                item["docCount"] = client[x][y].estimated_document_count()
                                                item["SampleItems"] = [json.dumps(x, default=json_util.default) for x in
                                                                       client[x][y].find({}, {'_id': False}).limit(
                                                                           5)]  # need to use json_util to deal w/ mongo datetime object serialization issues
                                                toobig.append(item)
                                        else:
                                            recordcount = dumpMongoDbcollectiontoCSV(db, collection, dbip, portnumber,
                                                                                     convertTOcsv=convertTOcsv)
                                            totalrecords += recordcount
                                            totaldbs += 1
                                    else:
                                        print(f"            Skipping {Fore.LIGHTRED_EX} {db}:{collection} {Fore.RESET} because only has {Fore.LIGHTBLUE_EX}{docsize}{Fore.RESET} records")
                    if totalrecords == 0:
                        print(f"    {Fore.LIGHTGREEN_EX}No collections{Fore.RESET} with fields matching specified strings found!")
                cdict = [{"ipaddress": dbip, "databaseinfo": collectionNames}]
                if toobig:
                    jsonappendfile(os.path.join(basepath, "Mongotoobig.json"), toobig)
                    print("    Following collection:database have more than 800,000 records. Info addedd to 'mongotoobig.json'")
                    for x in toobig:
                        print(f"        {Fore.LIGHTRED_EX} {x['database']}:{x['collection']} {Fore.RESET}| {Fore.LIGHTBLUE_EX}{x['docCount']}{Fore.RESET}")

        if cdict:
            jsonappendfile(os.path.join(basepath, "MongoFound.json"), cdict)

        if totalrecords>0:
            print (f"\nDumped \033[94m{totalrecords:,d}\x1b[0m total records from \033[94m{str(totaldbs)}\x1b[0m collections")

    print(f'{Fore.RED}#############################################{Fore.RESET}')
    updatestatsfile(totaldbs, totalrecords, 1, type="MongoDB")

    return totaldbs,totalrecords





