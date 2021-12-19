# Database mongodb configuration informations
MONGO_PRIMARY_DB_URL = "mongodb://mongo-rs-one:27017"
MONGO_SECONDARY_DB_URL = "mongodb://mongo-rs-two:27017"

# xp services base url and path
DECODER_BASE_URL = "http://10.10.14.116:513/api"
SESSION_SERVICE = {
    "CHECK": "/decoder",
    "APPID": "app_id",
    "SID": "sid",
    "ALIAS": "alias"
}
