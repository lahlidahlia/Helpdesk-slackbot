# Helpdesk-slackbot

This is a bot for PSU's OIT Helpdesk's slack channel. It is a general purpose bot that exists for any kinds of purpose that the Helpdesk needs. Currently it is mostly used to compile data from out ticketing system.

### Running your own helpdesk-slackbot
##### Slackbot
If you're the owner of a helpdesk bot and have your own bot token, skip to the RT setup section.

Create yourself a bot on Slack. Go to this link -> https://oit.slack.com/apps/A0F7YS25R-bots -> Add Configuration.
Once you've created your bot, find the API Token in its configuration page. You will need to use that to login with the bot.


##### RT setup
You need to have an RT login that is separate from the regular SSO login. The bot needs this in order to authorize itself with RT without using SSO (bot can't use SSO to authorize itself).
First login to your RT normally in a browser. Hover over the "Logged in as username" drop down -> Settings -> About me. There should be a section labeled "Password". Set your password. If you do not see an option to set a password, a tier 2 staff should be able to help you (Kai was able to help me setup my RT credentials) or shoot a ticket over to cis-unix.
DO NOT USE THE SAME PASSWORD AS YOUR ODIN ACCOUNT, AS THE PASSWORD ARE LOGGED SOMEWHERE IN RT SERVER.

Once you have your RT credentials make sure you are able to login to RT without SSO by going into incognito mode or private browsing and try logging into -> https://support.oit.pdx.edu/NoAuthCAS/. If that worked, try the link https://support.oit.pdx.edu/NoAuthCAS/REST/1.0/ticket/700000/ to fully verify that everything is working correctly.


##### Setting up the project
Clone or download this repository. Create a python virtual environment and install required packages:
```
virtualenv -p python3 venv
. ./venv/bin/activate
pip install -r requirements.txt
```

In the top directory, create a directory called "tokens", and in it are two files: "rt" and "slack". tokens/rt will contain your RT credentials that you created earlier as "username:password". tokens/slack will contain your slack token. Those two files will only contain those information and nothing else. Try to make sure there is no extra spaces or newlines at the end of the file. Note that it's fine to put your password and token and these local files because it is .gitignored and therefore won't be pushed upstream. If you find yourself pushing your credentials upstream, checkout Github's help page on removing sensitive data.

Next, create the "ticket_cache" directory on the top level directory. In it, create a file called "last_updated". In the file, put down the date that you want to start caching the tickets from. The date will be in the format "YYYY-MM-DD". Ex: 2016-12-21
Note that in the future when starting up the bot you shouldn't need to manually create the ticket cache directory and the last updated file. The bot should do that automagically.

Once that is setup, do the following to run the bot:
```
python src/main.py
```
To update the cache, DM the bot "!update" in order to update the bot. Note that it might take a very long time for the bot to update its cache depending on how far back you've set your last updated time to be.

Once done you can probably start adding the bot to other channels. 

Verify that the bot works by trying !untagged, !last_updated, !response 30, etc...
