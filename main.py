import requests
import requests.auth
import time
from datetime import datetime
import json
from pymongo import MongoClient
from cfg import readJson, saveJson

settings = readJson('settings.json')
startTime = time.time()

# Set a few static variables with our credentials to use with our API calls
USER_AGENT = 'Modmail fetcher for r/globaloffensive'
userName = settings['reddit']['username']
passW = settings['reddit']['password']
clientID = settings['reddit']['client_id']
clientSecret = settings['reddit']['client_secret']

# Set our client_id and client_secret, data to send with the POST, and the header
client_auth = requests.auth.HTTPBasicAuth(clientID, clientSecret)
post_data = {"grant_type": "password", "username": userName, "password": passW}
req_headers = {"User-Agent": USER_AGENT}

# Send the POST to retrieve our access token
response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=req_headers)
res = response.json()

# Store access token and type
accToken = res['access_token']
tokenType = res['token_type']

# Send the actual GET request for modmail using our access token
oauth_headers = {"Authorization": "bearer {}".format(accToken), "User-Agent": USER_AGENT}
response = requests.get("https://oauth.reddit.com/api/mod/conversations?sort=recent&state=archived&limit=10", headers=oauth_headers)
modmail = response.json()
createJson = saveJson('output.json', modmail)

# Set up the db info and authenticate
client = MongoClient(settings['db']['host'], settings['db']['port'])
db = client[settings['db']['database']]
db.authenticate(settings['db']['username'], settings['db']['password'], mechanism='SCRAM-SHA-1')
collection = db['collection name']

modmailJson = readJson('output.json')
count = 0

for convoID in modmailJson['conversationIds']:
    # Convert the time format in the response to a unix timestamp
    unix_time = time.mktime(datetime.strptime(
        modmailJson['conversations'][convoID]['lastUpdated'].replace('T', ' ').split('.')[0], "%Y-%m-%d %H:%M:%S").timetuple())

    name = modmailJson['conversations'][convoID]['participant']['name']
    subject = modmailJson['conversations'][convoID]['subject']
    msgID = modmailJson['conversations'][convoID]['objIds'][0]['id']
    lastMsg = modmailJson['messages'][msgID]['bodyMarkdown']
    numReplies = modmailJson['conversations'][convoID]['numMessages'] - 1
    permalink = 'https://mod.reddit.com/mail/archived/{}'.format(convoID)

    # Send the GET request for specific conversation metadata (such as all messages)
    getMsgs = requests.get("https://oauth.reddit.com/api/mod/conversations/{}".format(convoID), headers=oauth_headers)
    convoMsgs = getMsgs.json()
    firstID = convoMsgs['conversation']['objIds'][0]['id']
    firstMsg = convoMsgs['messages'][firstID]['bodyMarkdown']

    collection.update_one({'_id': convoID}, {
        '$set': {
            'last_updated': unix_time,
            'author': name,
            'subject': subject,
            'body': firstMsg,
            'permalink': permalink,
            'replies': []
        }
    }, upsert=True)

    lastReplyIndex = len(convoMsgs['conversation']['objIds']) - 1
    i = 0

    # Make sure the last action was a message response and not a ModAction. If it's a ModAction, move
    # to the next most recent action performed on the conversation and re-check. New Modmail includes
    # ModActions such as archiving a conversation with the actual messages responses.
    while i != 1:
        if convoMsgs['conversation']['objIds'][lastReplyIndex]['key'] != 'messages':
            lastReplyIndex -= 1
        else:
            i = 1

    lastReplyID = convoMsgs['conversation']['objIds'][lastReplyIndex]['id']
    lastReply = convoMsgs['messages'][lastReplyID]['bodyMarkdown']

    unix_time_last_reply = time.mktime(datetime.strptime(
        convoMsgs['messages'][lastReplyID]['date'].replace('T', ' ').split('.')[0], "%Y-%m-%d %H:%M:%S").timetuple())

    lastReplyAuthor = convoMsgs['messages'][lastReplyID]['author']['name']

    collection.update_one({'_id': convoID}, {
        '$push': {
            'replies': {
                '_id': lastReplyID,
                'last_updated': unix_time_last_reply,
                'author': lastReplyAuthor,
                'body': lastReply
            }
        }
    }, upsert=True)

    count += 1

elapsedTime = str(round(time.time() - startTime, 2))
print('Finished logging {} modmail conversations in {}s!'.format(count, elapsedTime))

