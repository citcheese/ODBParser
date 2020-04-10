"""
###################
# Do what it says #
###################
"""
#put your Shodan key here
SHODAN_API_KEY = ""

#put your BinaryEdge API key here
BINARY_API_KEY= ""

#specify minium number of documents in database that you want to bother with
mindocs =10

#specify max number of docs ODBgrabber will automatically collect. Can always set --nosizelimits for specifi dbs you want all of
maxdocs= 800000

#choose directory where want to put the files, otherwise will go wherever you run script
basepath = r""

#fields you want to make sure are in ES indices and MongoDb collections. Add your own! Or if you want to grab the DB no matter what fields are in there, leave this list blank. Will probably end up with lots of crap, but whatever
typelist = ['email',"username","alias","name","socialsecuritynumber","patient","password","employee","ssn","phone","ipaddress","mobile"]

#choose number of fields from above that must be in index or collection. For example if you want to have index with field containing the word 'email' AND a field containing the word 'IP' you would pick 2.
numfieldsrequired = 2

#choose what Mongodb collection names you care about. Script will see if one of the terms below is in collection/index name,
# e.g. if have term "client", script will pull index called "clients" or "client_data." Here some examples or leave blank if you don't care and want to evaluate all collections for fields you care about.
collectionamesIwant = ["user","employee","patient","customer","client","payments","member","people"]

#ignore indices that are prob just logs, feel free to add more items to this list. or delete some. whatever
ESindicesdontwant = ["metricbeat-","filebeat-","packetbeat-","heartbeat-","_sample_data", "apm-", "metrics__", "charts__",
                   "access-log","logstash-","-logs","-log-","monitoring","alerts","prod-java","prod-php","reporttrafficinfo"]  

#same as above but for ES, in case care about different things, I prefer to keep these blank but up to you. If you want same names as mongodb just set variable equal to collectionsIwant, e.g. ESindicesIwant = collectionamesIwant
ESindicesIwant=[]

#if you have list of IPs from prior scans you want to avoid re-dumping, put them here
oldips = []
