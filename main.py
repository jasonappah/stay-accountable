# FINAL TODO LIST: 
#   Finish prettyprint function (ln 168)
#   Change user to a list so that users can add multiple challenge admins.
#   Make sure all input coming into the program is safe to use, valid and cleansed.
#   Test all Slack interface functions: help, create, active, edit, delete
#   Deploy to Azure App Service

import schedule
import time
import os
from datetime import datetime
from slack import WebClient
from slack.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
import threading
from dotenv import load_dotenv
load_dotenv(verbose=True)
SLACK_BOT_ID = os.environ["SLACK_BOT_ID"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, endpoint="/slack/events")
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

# This program assumes it is being run on a server in UTC time zone.

actions = ["help", "create", "delete", "active", "edit"]
ChallengeManager = []
admins = ["UN6C43287", ]
def listchallenges(list=ChallengeManager, user="nonefornow"):
    tmp = []
    for idx in list:
        if idx.user == user:
            tmp.append({idx.id, idx.question})
    return tmp

def getTime():
    return (datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ": ")

def sendSlackMsg(channel="#bot-spam", txt="", emoji="rocket", botname="Challenger"):
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=txt, icon_emoji=emoji, username=botname)
        assert response["message"]["text"] == txt
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"{getTime()}Got an error: {e.response['error']}")

class Challenge:
    def __init__(self, user = "nonefornow", UTCTime = "12:00", question="Enter your question here.", cta="React with :upvote: for yes, :downvote: for no.", startday=1, endday=100, currentday=1,endmsg="This is the final day.", channel="#bot-spam", emoji=":rocket:", botname="Challenger"):
        # remind user to enter time in UTC
        self.user = user
        self.UTCTime = UTCTime
        self.question = question
        self.cta = cta

        #see ln 66 for more info
        self.startday=startday

        self.endday=endday
        self.currentday=currentday
        self.endmsg = endmsg
        self.isActive = True
        self.channel=channel
        self.id = len(ChallengeManager)
        self.emoji=emoji
        self.botname=botname
        ChallengeManager.append(self)
        print(f"{getTime()}User {self.user} created a new {endday} day challenge with ID {self.id}.")
        self.schedule()
        self.getId()
    
    def job(self):
        if not self.currentday < 1:
            # if self.currentday is less than 1, we essentially use it as a countdown clock to postpone the beginning of a given challenge.
            msg = ""
            if self.endday==self.currentday:
                msg = msg + self.endmsg + " "
            msg = f"Day {self.currentday}: "
            msg = msg + self.question + " " + self.cta
            sendSlackMsg(self.channel, msg, self.emoji, self.botname)
            print(f"{getTime()}Attempted to send message for {self.user}: {msg}")

        self.currentday += 1

        if self.endday==self.currentday:
            self.delete()

    def getId(self):
        return self.id

    def schedule(self, re=False):
        self.scheduleditem = schedule.every().day.at(self.UTCTime).do(self.job)
        if re == False:
            print(f"{getTime()}User {self.user} scheduled challenge id {self.id} with time {self.time}.")
        else:
            print(f"{getTime()}User {self.user} rescheduled challenge id {self.id} with time {self.time}.")

    def edit(self, param, val):
        self.__setattr__(param, val)
        if (self.__getattribute__(param) == val):
            print(f"{getTime()}User {self.user} set param {param} of challenge id {self.id} to {val}.")
        else: 
            print(f"{getTime()}User {self.user} tried to set param {param} of challenge id {self.id} to {val} but was unsuccessful.")
        if param == "time":
            schedule.cancel_job(self.scheduleditem)
            self.schedule(True)

    def delete(self):
        self.isActive = False
        schedule.cancel_job(self.scheduleditem)
    
    def toJSON(self):
        pass

# borrowed from https://github.com/mrhwick/schedule/blob/master/schedule/__init__.py
def run_continuously(schedule=schedule, interval=1):
        """Continuously run, while executing pending jobs at each elapsed
        time interval.
        @return cease_continuous_run: threading.Event which can be set to
        cease continuous run.
        Please note that it is *intended behavior that run_continuously()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you set a continuous run interval
        of one hour then your job won't be run 60 times at each interval but
        only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run

def slackInterface():
    print(f"{getTime()}Starting Slack event handler stuff... ")

    @slack_events_adapter.on("app_mention")
    def app_mention(event_data):
        print(f"{getTime()}{event_data}")
        event = event_data["event"]
        main_handler(event, event_data["type"])

    @slack_events_adapter.on("message")
    def messageim(event_data):
        print(f"{getTime()}{event_data}")
        event = event_data["event"]
        main_handler(event, event_data["type"])
    
    def help(msgdest):
        help = "Mention *<@{SLACK_BOT_ID}>* with the options *create*, *active*, *edit [challengeid:int] [paramtoedit:str] [newparamval:str|int]*, or *delete [challengeid]*."
        sendSlackMsg(channel=msgdest,txt=help)

    def create(event, eventtype, split):
        msgdest=event["channel"]
        user=event["user"]
        errmsg=f"That's not the correct usage of create. Usage: *<@{SLACK_BOT_ID}> create*. DM <@UN6C43287> if this seems wrong."
        try:
            if len(split) == 2:
                id = Challenge(user=user)
                sendSlackMsg(msgdest, "Successfully created a new challenge! To set it up, use the id shown here with the edit command: *<@{SLACK_BOT_ID}> edit [challengeid:int] [param:str] [val:str|int]*")
                active(event, eventtype, split, id)
            else:
                sendSlackMsg(msgdest, errmsg)
        except:
            sendSlackMsg(msgdest, errmsg)

    def active(event={}, eventtype="", split=[],id=""):
        def prettyprint(id):
            # TODO: get all info for given challenge id and send it in a slack message.
            pass
        
        msgdest=event["channel"]
        user=event["user"]
        errmsg=f"That's not the correct usage of active. Usage: *<@{SLACK_BOT_ID}> active*. DM <@UN6C43287> if this seems wrong."
        if id == "":
            tmp = []
            try:
                if len(split) == 2:
                    for c in ChallengeManager:
                        if c.user == user:
                            if c.isActive:
                                tmp.append(c.id)
                else:
                    sendSlackMsg(msgdest, errmsg)
                
                if len(tmp) > 0:
                    prettyprint(id)
                else:
                    sendSlackMsg(msgdest, f"You don't have any active challenges. Create one using *<@{SLACK_BOT_ID}> create*. DM <@UN6C43287> if this seems wrong.")
            except:
                sendSlackMsg(msgdest, errmsg)
        else:
            prettyprint(id)

    def edit(event, eventtype, split):
        msgdest=event["channel"]
        user=event["user"]
        errmsg=f"That's not the correct usage of edit. Usage: *<@{SLACK_BOT_ID}> edit [challengeid:int] [param:str] [val:str|int]*. You can get a list of parameters that can be edited by running *<@{SLACK_BOT_ID}> active*. DM <@UN6C43287> if this seems wrong."
        try:
            id=split[2]
            id=int(id)
            if len(split) == 5:
                if ChallengeManager[id].isActive:
                    if ChallengeManager[id].user == user:
                        ChallengeManager[id].edit(split[3],split[4])
                    else:
                        sendSlackMsg(msgdest, f"You can't edit challenge ID {id} as you did not create it. DM <@UN6C43287> if this seems wrong.")
            else:
                sendSlackMsg(msgdest, errmsg)
        except:
            sendSlackMsg(msgdest, errmsg)

    def delete(event, eventtype, split):
        msgdest=event["channel"]
        user=event["user"]
        errmsg=f"That's not the correct usage of delete. Usage: *<@{SLACK_BOT_ID}> delete [challengeid:int]*. You can get the ID of an existing challenge by using *<@{SLACK_BOT_ID}> active*, or create a new challenge by using *<@{SLACK_BOT_ID}> create*. DM <@UN6C43287> if this seems wrong."
        try:
            id=split[2]
            id=int(id)
            if len(split) == 3:
                if ChallengeManager[id].isActive:
                    if ChallengeManager[id].user == user:
                        ChallengeManager[id].delete()
                    else:
                        sendSlackMsg(msgdest, f"You can't delete challenge ID {id} as you did not create it. DM <@UN6C43287> if this seems wrong.")
            else:
                sendSlackMsg(msgdest, errmsg)
        except:
            sendSlackMsg(msgdest, errmsg)

    def main_handler(event, eventtype):
        text = event["text"]
        try:
            user = event["user"]
        except KeyError:
            user = "bot"
        print(f"{getTime()}{text}")
        split = text.split(" ")
        if eventtype != "app_mention":
            if split[0] != f"<@{SLACK_BOT_ID}>":
                split.insert(0,f"<@{SLACK_BOT_ID}>")
        if f"<@{SLACK_BOT_ID}>" == split[0]:
            print(f"{getTime()}{split}", "was sent in channel", event["channel"])
            if not user == "bot":
                if len(split) > 1:
                    if not(split[1] in actions):
                        help(event["channel"])
                    else:
                        if split[1] == "delete":
                            delete(event, eventtype, split)
                        elif split[1] == "active":
                            active(event, eventtype, split)
                        elif split[1] == "edit":
                            edit(event, eventtype, split)
                        elif split[1] == "create":
                            create(event, eventtype, split)
                else: 
                    help(event["channel"])

    # Start the server on port 3000
    slack_events_adapter.start(port=3000)

try:
    print(f"{getTime()}Starting scheduler... ")
    run_continuously()
    print(f"{getTime()}Started scheduler... ")
    Challenge(time="14:36")
    ChallengeManager[0].edit("time", "18:12")
    print(listchallenges())
    slackInterface()
except Exception as e:
    print(f"{getTime()}Exception: {e} ")