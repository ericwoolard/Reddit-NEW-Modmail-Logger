New-Modmail Fetcher
------------
This was created using the bare Reddit API for new-modmail, since at the time PRAW had yet to update.
The new-modmail API is pretty messy, so I did the best I could with what I gots. 

INFO
----------
It currently runs every 2 minutes, checks the most recent 10 modmails in the 'Archived' section of modmail,
and writes the response to a cached json file. It then goes through the cached copy, grabs info for each 
conversation and logs a new document in the modmail.new collection in mongo. Since individual message replies
to a particular modmail conversation are not accessible from the initial request, it also makes a separate
request to the `/conversations/{ConversationID}` endpoint to retrieve individual responses for each modmail
conversation stored in the cached response. If it finds a conversation by ID that already exists in the 
mongodb collection, it updates it with any new messages.

One downside to the new-modmail API is that the response does not include a key for a created_at value. 
Instead, we're given times for `lastUpdated`, `lastUserUpdate` and `lastModUpdate`. This script uses 
`lastUpdated`, so if a modmail conversation gets a new message, that timestamp also gets updated. 
