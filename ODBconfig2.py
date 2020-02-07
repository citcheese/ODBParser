

"""


##################
Do what it says.
##################

"""
#put your Shodan key here
SHODAN_API_KEY = ""

#choose directory where want to put the files, otherwise will go wherever you run
basepath = r""

#fields you want to make sure are in ES indices and MongoDb collections. Add your own! Or if you want to grab the DB no matter what fields are in there, leave this list blank. Will probably end up with lots of crap, but whatever
typelist = ['email',"first_name","last_name","username","alias","firstname","lastname","social security number","surname","patient","password","emails","fullname","employee"]

#choose number of fields from above that must be in index or collection. For example if you want to have index with field containing the word 'email' AND a field containing the word 'IP' you would pick 2.
numfieldsrequired = 1

#choose what Mongodb collection names you care about. Script will see if one of the terms below is in collection/index name,
# e.g. if have term "client", script will pull index called "clients" or "client_data." Here some examples or leave blank if you don't care and want to evaluate all collections for fields you care about.
collectionamesIwant = ["user","employee","patient","customer","client","payments","member","people"]

#same as above but for ES, in case care about different things, I prefer to keep these blank but up to you. If you want same names as mongodb just set variable equal to collectionsIwant, e.g. ESindicesIwant = collectionamesIwant
ESindicesIwant=[]

#if you have list of IPs from prior scans you want to avoid re-dumping, put them here
oldips = []
