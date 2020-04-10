import os
import json
import pandas as pd
from tqdm import tqdm
from colorama import Fore
import sys

def jsonappendfile(filepath,items):
    prevExists = True
    if not os.path.exists(filepath) or os.path.getsize(filepath)==0:
        prevExists = False
        with open(filepath, "ab+") as f:
            f.write("[]".encode())

    with open(filepath, "ab+") as newZ:  # so dont have to store whole json in memory
        newZ.seek(-1, 2)
        newZ.truncate()
        if prevExists:
            newZ.write(",".encode())
        for y in items[:-1]:
            newZ.write(json.dumps(y).encode())
            newZ.write(",".encode())
        newZ.write(json.dumps(items[-1]).encode())
        newZ.write(']'.encode())


def checkifIPalreadyparsed(ipaddress,dbtype="Elastic",multi=False,skiptimeouts=False): #types are Elastic or Mongo
    import ODBconfig
    import ijson
    dbtype = dbtype.title().strip("db")
    basepath = ODBconfig.basepath
    oldips = ODBconfig.oldips

    if ":" in ipaddress:
        ipaddress = ipaddress.split(":")[0]
    if not basepath:
        basepath = os.path.join(os.getcwd(), "open directory dumps")

    if not os.path.exists(basepath):
        os.makedirs(basepath)

    if os.path.exists(os.path.join(basepath,f"{dbtype}Found.json")):
        if os.path.getsize(os.path.join(basepath, f"{dbtype}Found.json")) != 0:
            with open(os.path.join(basepath,f"{dbtype}Found.json")) as outfile:
                doneips = list(ijson.items(outfile, "item.ipaddress")) #inly load ipadrdess key into memory in case file gets crazy big

        else:
            doneips =[]
    else:
        doneips = []
    pd.set_option('display.max_colwidth', -1)
    doneips = doneips+oldips

    if multi:
        parsedones = [x for x in ipaddress if x in doneips]
        return parsedones
    else:
        if ipaddress in doneips:
            return True
        else:
            return False


def convertjsondumptocsv(jsonfile,flattennestedjson=True,olddumps=False,getridofuselessdata=False):
    import pathlib
    from pandas.io.json import json_normalize
    import numpy as np
    p = pathlib.Path(jsonfile)
    foldername = p.parent.name
    issuesflattening = False
    if not os.path.exists(os.path.join(p.parent,"JSON_backups")):
        os.makedirs(os.path.join(p.parent,"JSON_backups"))
    try:
        if olddumps:#use this to convert generic ES dumps where entire record is on each line
            with open(jsonfile,encoding="utf8") as f:
                content = f.readlines()
            con2 = [json.loads(x) for x in content]
            try:
                con2 =[x["_source"] for x in con2 if x['_source']] #get rid of empty values
            except:
                pass
            #outfile = jsonfile.replace('.json','.csv')
        else:
            try:
                with open(jsonfile,encoding="utf8",errors="replace") as f:

                    con2 = json.load(f)
            except ValueError: #for times when have json objects not seperated by a comma
                with open(jsonfile, encoding="utf8", errors="replace") as f:
                    content = f.read()
                con2 = []
                decoder = json.JSONDecoder()
                while content:
                    value, new_start = decoder.raw_decode(content)
                    content = content[new_start:].strip()
                    # You can handle the value directly in this loop:
                    #print("Parsed:", value)
                    # Or you can store it in a container and use it later:
                    con2.append(value)
                #print("yes")
        outfile = jsonfile.replace('.json','.csv')
        if flattennestedjson:
            try:
                dic_flattened = [flatten_json(d) for d in con2]
                df = pd.DataFrame(dic_flattened)
            except Exception:
                try:
                    df = json_normalize(con2, errors="ignore")

                except Exception as e:
                    df = pd.DataFrame(con2)
                    issuesflattening = True

        else:
            df = pd.DataFrame(con2)
        if getridofuselessdata:
            df.replace("blank", np.nan, inplace=True)
            df.replace("Null", np.nan, inplace=True)
            df.replace("", np.nan, inplace=True)

            df = df.astype("object")
            df.dropna(axis=1, how='all', inplace=True)
            droplist = [x for x in df.columns if all(len(str(y).split(".",1)[0]) < 3 for y in df[x].tolist())]  # find columns if all values only 1 character long e.g. 0,1 y, n
            df.drop(droplist, axis=1, inplace=True)  # drop them

            df = df.dropna(axis=1, thresh=int(.001 * len(df)))  # drop all columns that have less than .001 values
            df.replace(np.nan, '', regex=True, inplace=True)



        df.replace(np.nan, '', regex=True,inplace=True)
        cols = df.columns
        dropcols = ["_id", '__v']  # id columns I don't want
        cols1 = [x for x in cols if x in dropcols]  # check to see if column is in my df
        df.drop(cols1, axis=1, inplace=True)  #
        df = df.applymap(str)
        df.drop_duplicates(inplace=True)
        df = df.replace({'\n': '<br>',"\r":"<br>"}, regex=True)
        df.to_csv(outfile,index=False,escapechar='\n') #ignore newline character inside strings
        os.rename(jsonfile,os.path.join(p.parent,"JSON_backups",p.name)) #move json file to jsonbackups folder to keep things tidy
        try:
            os.rename(jsonfile.replace(".json","_mapping.json"), os.path.join(p.parent, "JSON_backups",
                                             p.name.replace(".json","_mapping.json")))  # move json file to jsonbackups folder to keep things tidy
        except:
            pass
    except Exception as e:
        issuesflattening = True
        print(f"{jsonfile}: {str(e)}")
    return issuesflattening

def jsonfoldert0mergedcsv(folder,flattennestedjson=False,olddumps=False,getridofuselessdata=False):
    files = [x for x in os.listdir(folder) if x.endswith(".json") and "_mapping.json" not in x]
    t = tqdm(files,desc="Now Converting",leave=True)
    issues = []
    for x in t:
        t.set_description(F"Converting: {Fore.LIGHTRED_EX}{x}{Fore.RESET}")
        t.refresh()
        res = convertjsondumptocsv(os.path.join(folder,x),flattennestedjson=flattennestedjson,olddumps=olddumps,getridofuselessdata=getridofuselessdata)
        if res:
            issues.append(x)
    if issues:
        print(F"    {Fore.LIGHTGREEN_EX}Error{Fore.RESET} with following files:")
        for y in issues:
            print(f"        {y}")

def megajsonconvert(directory,flattennestedjson=False,olddumps=False):
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory,folder)):
            jsonfoldert0mergedcsv(os.path.join(directory,folder),flattennestedjson=flattennestedjson,olddumps=olddumps)

def convert_timestamp(item_date_object):
    import datetime
    if isinstance(item_date_object, (datetime.date, datetime.datetime)):
        return item_date_object.timestamp()

def iterate_all(iterable, returned="key"):
    """Returns an iterator that returns all keys or values
       of a (nested) iterable.

       Arguments:
           - iterable: <list> or <dictionary>
           - returned: <string> "key" or "value"

       Returns:
           - <iterator>
    """

    if isinstance(iterable, dict):
        for key, value in iterable.items():
            if returned == "key":
                yield key
            elif returned == "value":
                if not (isinstance(value, dict) or isinstance(value, list)):
                    yield value
            else:
                raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
            for ret in iterate_all(value, returned=returned):
                yield ret
    elif isinstance(iterable, list):
        for el in iterable:
            for ret in iterate_all(el, returned=returned):
                yield ret


def shodan_query(query,limit=1000):
    import ODBconfig
    import shodan
    counter =0
    limit = int(limit) #convert to int as passed as string from cli.
    try:
        api = shodan.Shodan(ODBconfig.SHODAN_API_KEY)
        result = api.search_cursor(query)
        shodanres = []
        for x in result:
            shodanres.append((x["ip_str"],x["product"],x["port"])) #lets only grab these fields to lower memory overhead
            counter+=1
            if counter>=limit: #so we don't go over limit you set. Helps to avoid runnign through all your credits
                break
        return shodanres

    except shodan.APIError as e:
        print(Fore.RED + e.value + Fore.RESET)
        return False

def valid_ip(address):
    if ":" in address:
        address = address.split(":",1)[0]

    try:
        host_bytes = address.split('.')
        valid = [int(b) for b in host_bytes]
        valid = [b for b in valid if b >= 0 and b<=255]
        return len(host_bytes) == 4 and len(valid) == 4
    except:
        return False

def ipsfromfile(filepath):
    with open(filepath,encoding="utf8",errors="ignore") as f:
        ips = f.readlines()
    ips = [x.replace("\n", "").strip("/https//:") if not x[0].isdigit() else x.replace("\n", "") for x in ips]
    ips = list(set((filter(None,ips))))
    goodips = [x for x in ips if valid_ip(x)]
    badips = (set(ips).difference(goodips))
    return goodips,badips

def ipsfromclipboard():
    import pyperclip
    ips = pyperclip.paste().splitlines()
    ips = list(set((filter(None, ips))))
    ips = [x.strip("/https//:") if not x[0].isdigit() else x for x in ips]
    goodips = [x for x in ips if valid_ip(x)]
    badips = (set(ips).difference(goodips))
    return goodips,badips

def printsummary(donedbs,totalrecords):
    from colorama import Fore
    summ = [f"{Fore.LIGHTRED_EX}RUN SUMMARY{Fore.CYAN}", F"{Fore.RESET}Dumped {Fore.LIGHTBLUE_EX}{str(donedbs)}{Fore.RESET} databases with a total of {Fore.LIGHTBLUE_EX}{totalrecords:,d}{Fore.RESET} records.{Fore.CYAN}", f"{Fore.RESET}{Fore.LIGHTRED_EX}Have a nice day!{Fore.CYAN}"]

    maxlen = max(len(s) for s in summ)
    colwidth = maxlen - 12
    border = colwidth + 2
    print(f"{Fore.CYAN}{'#' * border}")
    print(f'#{summ[0]:^{colwidth + 10}}#')
    print(f'#{summ[1]:^{colwidth + 30}}#')
    print(f'#{summ[2]:^{colwidth + 15}}#')
    print(f"{'#' * border}{Fore.RESET}")

def updatestatsfile(donedbs=0,totalrecords=0,parsedservers=0,type="ElasticSearch"):
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(absolute_path,"ODBstats.json")
    if not os.path.exists(fpath):
        prevExists = False
        item = {}
        elastic ={}
        mongo={}
        elastic["databases dumped"]=0
        elastic["total records dumped"] =0
        elastic["parsed servers"] = 0
        mongo["databases dumped"]=0
        mongo["total records dumped"] =0
        mongo["parsed servers"] = 0
        item["ElasticSearch"] = elastic
        item["MongoDB"] = mongo

        with open(fpath, "w") as f:
            json.dump(item,f)
    with open(fpath) as f:
        con = json.load(f)
    con[type]["total records dumped"]=con[type]["total records dumped"]+totalrecords
    con[type]["databases dumped"]=con[type]["databases dumped"]+donedbs
    con[type]["parsed servers"]=con[type]["parsed servers"]+parsedservers
    with open(fpath, "w") as f:
        json.dump(con, f)

def getstats():
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(absolute_path, "ODBstats.json")
    if not os.path.exists(fpath):
        item = {}
        elastic ={}
        mongo={}
        elastic["databases dumped"]=0
        elastic["total records dumped"] =0
        elastic["parsed servers"] = 0
        mongo["databases dumped"]=0
        mongo["total records dumped"] =0
        mongo["parsed servers"] = 0
        item["ElasticSearch"] = elastic
        item["MongoDB"] = mongo

        with open(fpath, "w") as f:
            json.dump(item,f)

    #fpath = os.path.join("ODBlib","ODBstats.json")
    with open(fpath) as f:
        con = json.load(f)
    donedbs = 0
    parsed =0
    totalrecs = 0
    for x in con.keys():
        parsed += con[x]["parsed servers"]
        totalrecs += con[x]["total records dumped"]
        donedbs += con[x]["databases dumped"]
    return parsed,totalrecs,donedbs


def flatten_json(dictionary):
    from itertools import chain, starmap
    """Flatten a nested json file"""

    def unpack(parent_key, parent_value):
        """Unpack one level of nesting in json file"""
        # Unpack one level only!!!

        if isinstance(parent_value, dict):
            for key, value in parent_value.items():
                temp1 = parent_key + '_' + key
                yield temp1, value
        elif isinstance(parent_value, list):
            i = 0
            for value in parent_value:
                temp2 = parent_key + '_' + str(i)
                i += 1
                yield temp2, value
        else:
            yield parent_key, parent_value

            # Keep iterating until the termination condition is satisfied

    while True:
        # Keep unpacking the json file until all values are atomic elements (not dictionary or list)
        dictionary = dict(chain.from_iterable(starmap(unpack, dictionary.items())))
        # Terminate condition: not any value in the json file is dictionary or list
        if not any(isinstance(value, dict) for value in dictionary.values()) and \
                not any(isinstance(value, list) for value in dictionary.values()):
            break

    return dictionary

def binaryedgecheck(BEkey):
    import requests
    headers = {'X-Key': BEkey}
    end = 'https://api.binaryedge.io/v2/user/subscription'
    req = requests.get(end,headers=headers)
    req = req.json()
    return req["requests_left"]

def binaryedgeQuery(query,limit):
    from pybinaryedge import BinaryEdge
    import ODBconfig
    BEkey = ODBconfig.BINARY_API_KEY

    requestleft = binaryedgecheck(BEkey)
    if requestleft>0:
        limit = int(limit)
        #params country:us port
        pages = int(limit / 20) + (limit % 20 > 0) #20 results per page, see how many pages need to grab by rounding up
        if pages >999:
            pages = 1000
            print("Max pages is 1000")
        be = BinaryEdge(BEkey)

        counter = 0
        BEres = []
        results = be.host_search(query)
        total = results["total"]
        maxpages = int(total / 20) + (total % 20 > 0) #20 results per page, see how many pages need to grab by rounding up
        if pages>maxpages:
            pages = maxpages
        if results["events"]:
            for x in results["events"]:
                if "error" in x["result"]:
                    if not x["result"]["error"]: #one more step to get rid of crap
                        BEres.append((x["target"]["ip"],x["origin"]["type"],x["target"]["port"]))
                else:
                    BEres.append((x["target"]["ip"], x["origin"]["type"], x["target"]["port"]))

        try:
            for i in range(2,maxpages+1):
                results = be.host_search(query, i)
                if not results["events"]:
                    break

                for x in results["events"]:
                    if "error" in x["result"]:

                        if not x["result"]["error"]:
                            BEres.append((x["origin"]["ip"], x["origin"]["type"], x["target"]["port"]))
                    else:
                        BEres.append((x["target"]["ip"], x["origin"]["type"], x["target"]["port"]))
        except Exception as e:
            print(str(e))
        BEres = list(set(BEres)) #for some reason return sdupe records
        BEres = BEres[:limit]
        return BEres
    elif requestleft ==0:
        print(
            f"{Fore.RED}ERROR! {Fore.RESET}Your {Fore.CYAN}BinaryEdge{Fore.RESET} plans has {Fore.GREEN}no more queries left{Fore.RESET}. Wait til requests cycle or pay for a plan")
        sys.exit()

"""
Notes:
def check_rsync(results):
    if results:
        for service in results:
            print('rsync://'+service['target']['ip'])
            print("Server status: " + service['result']['data']['state']['state'])
            try:
                print(Fore.GREEN + service['result']['data']['service']['banner'] + Fore.RESET,)
            except:
                print(Fore.RED + 'No information' + Fore.RESET)
            print("------------------------------")

"""