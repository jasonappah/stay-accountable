import schedule
import time
import os
import jsonpickle
from datetime import datetime
from slack import WebClient
from slack.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
import threading
from s1db import S1
from dotenv import load_dotenv
load_dotenv(verbose=True)
SLACK_BOT_ID = os.environ["SLACK_BOT_ID"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, endpoint="/slack/events")
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
api = S1(os.environ["S1_TOKEN"])

# This program assumes it is being run on a server in UTC time zone.

class StrAtt(str):
    pass

class IntAtt(int):
    pass

lastBackup = "No backup has been taken yet."

def getTime():
    return (datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ": ")

def backup():
    print(f"{getTime()}Beginning backup to S1...")
    print(f"{getTime()}Deleting keys currently in S1...")
    for i in api.get_keys():
        api.delete(i)
    print(f"{getTime()}Deleted keys currently in S1.")
    print(f"{getTime()}Sending contents of ChallengeManager to S1...")
    for i in ChallengeManager:
        api.set(str(i.id), i.toJSON())
    api.set("admins", jsonpickle.encode(admins))
    lastBackup = getTime()
    print(f"{lastBackup}Backup complete!")

def restore():
    print(f"{getTime()}Ensuring that ChallengeManager is empty...")
    for i in ChallengeManager:
        ChallengeManager.pop(0)
    print(f"{getTime()}Beginning restore from S1...")
    for i in api.get_keys():
        if i != "admins"
            jsonpickle.decode(api.get_raw(i))
        else:
            admins = jsonpickle.decode(api.get_raw(i))
    print(f"{getTime()}Restored from S1!")

actions = ["help", "create", "delete", "active", "edit", "admin"]
ChallengeManager = []
admins = ["UN6C43287"]
def listchallenges(list=ChallengeManager, user=["nonefornow"]):
    tmp = []
    for idx in list:
        if idx.user == user:
            tmp.append({idx.id, idx.question})
    return tmp

def sendSlackMsg(channel="#bot-spam", txt="", emoji="rocket", botname="Challenger", thread_ts="none"):
    if not txt == "":
        try:
            if thread_ts != "none":
                print("sending threaded message")
                print(f"Thread ts: {thread_ts}")
                response = client.chat_postMessage(
                    channel=channel,
                    text=txt, icon_emoji=emoji, username=botname, thread_ts=thread_ts)
                assert response["message"]["text"] == txt
            else:
                print("sending normal message")
                print(f"Thread ts: {thread_ts}")
                response = client.chat_postMessage(
                    channel=channel,
                    text=txt, icon_emoji=emoji, username=botname)
                assert response["message"]["text"] == txt
                
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["ok"] is False
            assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
            print(f"{getTime()}Got an error: {e.response['error']}")
    else: 
        print(f"{getTime()} Attempted to send a message but there was no text passed in.")

class Challenge:
    def __init__(self, user = "testuser", UTCTime = "12:00", question="Enter your question here.", cta="React with :upvote: for yes, :downvote: for no.", startday=1, endday=100, currentday=1,endmsg="This is the final day.", channel="#bot-spam", emoji=":rocket:", botname="Challenger"):
        # remind user to enter time in UTC
        self.user = StrAtt(user)
        self.user.desc ="*User*: _The user that can edit this challenge. (String)_"
        self.UTCTime = StrAtt(UTCTime)
        self.UTCTime.desc = "*Time*: _The time that the message should be sent in UTC timezone in a 24hr format. Ex: 12pm = 12:00, 4pm = 16:00, 12am = 00:00, 3am = 03:00. (String)_"
        self.question = StrAtt(question)
        self.question.desc = "*Question:* The question that will be sent to the channel daily at the time defined in UTCTime. (String)"
        self.cta = StrAtt(cta)
        self.cta.desc = "*CTA/Call to Action:* _Extra message appended to question, usually encouraging the user to do something. Ex: Telling user to react to a message to indicate an answer. (String)_"

        #see ln 66 for more info
        self.startday=IntAtt(startday)
        self.startday.desc="*Start Day:* _The day number that the challenge will actually start on. Most people will leave this at 1._"

        self.endday=IntAtt(endday)
        self.endday.desc="*End Day:* _Number representing how many days the challenge should be. (Integer)_"
        self.currentday=IntAtt(currentday)
        self.currentday.desc="*Current Day:* _Number indicating the current day you are on in the challenge. This can be set to a negative integer so that, for example, if you want to start a challenge in 7 days, you can set current day to -6, and I won't send any messages until those 7 days are elapsed, or can also be used if a challenge has already begun without using Challenger._"

        self.endmsg = StrAtt(endmsg)
        self.endmsg.desc="*End Message:* _Message that will prepend your question and CTA on the final day of your challenge. (String)_"
        self.isActive = True
        self.channel=StrAtt(channel)
        self.channel.desc="*Channel:* _The channel that you would like the challenge to be posted in. (String)_"
        self.emoji=StrAtt(emoji)
        self.emoji.desc = "*Emoji:* _The emoji to use as the profile picture of the bot posting the challenge. (String)_"
        self.botname=StrAtt(botname)
        self.botname.desc = "*Bot Name:* _The name the bot will use when posting the challenge. (String)_"
        self.id = IntAtt(len(ChallengeManager))
        self.id.desc = "*ID:* _A unique number referring to this challenge. *Do not modify this.* (Integer)_"
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
            print(f"{getTime()}User {self.user} scheduled challenge id {self.id} with time {self.UTCTime}.")
        else:
            print(f"{getTime()}User {self.user} rescheduled challenge id {self.id} with time {self.UTCTime}.")

    def edit(self, param, val):
        object = getattr(self, param)
        newdesc = getattr(object, "desc", "skip")
        print(newdesc)
        if type(object) == IntAtt:
            self.__setattr__(param, IntAtt(val))
        else:
            self.__setattr__(param, StrAtt(val))
        
        self.__dict__[param].desc = newdesc

        if (self.__getattribute__(param) == val):
            print(f"{getTime()}User {self.user} set param {param} of challenge id {self.id} to {val}.")
            status = True
        else: 
            print(f"{getTime()}User {self.user} tried to set param {param} of challenge id {self.id} to {val} but was unsuccessful.")
            status = False
        if param == "UTCTime":
            schedule.cancel_job(self.scheduleditem)
            self.schedule(True)
        return status

    def delete(self):
        self.isActive = False
        schedule.cancel_job(self.scheduleditem)
    
    def toJSON(self):
        return jsonpickle.encode(self)

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

def main(port):
    restore()
    print(f"{getTime()}Starting Slack interface... ")

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
        help = f"Mention *<@{SLACK_BOT_ID}>* with the options *create*, *active*, *edit [challengeid:int] [`param` :str] [newparamval:str|int]*, *delete [challengeid]*, *admin [add/delete] [user:str]* or *<@{SLACK_BOT_ID}> admin [view/runbackup/lastbackup]*."
        sendSlackMsg(channel=msgdest,txt=help)

    def create(event, eventtype, split):
        ts = ""
        msgdest=event["channel"]
        if eventtype == "app_mention":
            ts = event["ts"]
        user=event["user"]
        errmsg=f"That's not the correct usage of create. Usage: *<@{SLACK_BOT_ID}> create*. DM <@UN6C43287> if this seems wrong."
        try:
            if len(split) == 2:
                id = Challenge(user=user)
                sendSlackMsg(channel=msgdest, txt=f"Successfully created a new challenge! To set it up, use the ID {id.getId()} with the edit command: *<@{SLACK_BOT_ID}> edit {id.getId()} [`param` :str] [val:str|int]*", thread_ts=ts)
                active(event, eventtype, split, id.getId())
            else:
                sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)
        except:
            sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)

    def active(event={}, eventtype="", split=[],id=-10):
        def prettyprint(id):
            print(f"{getTime()}Running prettyprint for challenge ID {str(id)}, requested by user {user}, in {eventtype} {msgdest}")
            tmp=""
            id = int(id)
            for i in ChallengeManager[id].__dict__.keys():
                try:
                    val=ChallengeManager[id].__dict__[i]
                    object = getattr(ChallengeManager[id], i)
                    desc = getattr(object, "desc", "skip")
                    name = i

                    if desc != "skip":
                        tmp = tmp + f"{desc}\n\t`{name}`: {val}\n"
                except Exception as e:
                    print(e)

            return tmp

        msgdest=event["channel"]
        ts = ""
        if eventtype == "app_mention":
            ts = event["ts"]
        user=event["user"]
        errmsg=f"That's not the correct usage of active. Usage: *<@{SLACK_BOT_ID}> active*. DM <@UN6C43287> if this seems wrong."
        if id == -10:
            tmp = []
            try:
                if len(split) == 2:
                    for c in ChallengeManager:
                        if c.user == user or user in admins:
                            if c.isActive:
                                tmp.append(c.id)
                else:
                    sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)
                
                if len(tmp) > 0:
                    for i in tmp:
                        sendSlackMsg(channel=msgdest, txt=prettyprint(i), thread_ts=ts)
                else:
                    sendSlackMsg(channel=msgdest, txt=f"You don't have any active challenges. Create one using *<@{SLACK_BOT_ID}> create*. DM <@UN6C43287> if this seems wrong.", thread_ts=ts)
            except Exception as e:
                print(e)
                sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)
        else:
            sendSlackMsg(channel=msgdest, txt=prettyprint(id), thread_ts=ts)

    def admin(event, eventtype, split):
        ts = ""
        errmsg=f"That's not the correct usage of admin. Usage: *<@{SLACK_BOT_ID}> admin [add/delete] [user:str]* or  *<@{SLACK_BOT_ID}> admin [view/runbackup/lastbackup]*. You must be authorized as an admin. DM <@UN6C43287> if this seems wrong."
        msgdest=event["channel"]
        if eventtype == "app_mention":
            ts = event["ts"]
        user=event["user"]
        if user in admins:
            try:
                if len(split) == 4:
                    if split[2] == "add":
                        try:
                            admins.index(split[3])
                            sendSlackMsg(channel=msgdest, txt=f"User {split[3]} is already an admin. DM <@UN6C43287> if this seems wrong.", thread_ts=ts)
                        except ValueError:
                            admins.append(split[3])
                            sendSlackMsg(channel=msgdest, txt=f"Elevated user {split[3]} to admin.", thread_ts=ts)
                    elif split[2] == "delete":
                        try:
                            admins.remove(split[3])
                            sendSlackMsg(channel=msgdest, txt=f"Removed admin permissions of user {split[3]}.", thread_ts=ts)
                        except:
                            sendSlackMsg(channel=msgdest, txt=f"User {split[3]} is not an admin. DM <@UN6C43287> if this seems wrong.", thread_ts=ts)
                elif len(split) == 3:
                    if split[2] == "view":
                        sendSlackMsg(channel=msgdest, txt=f"Admins: *{admins}*", thread_ts=ts)
                    elif split[2] == "lastbackup":
                        sendSlackMsg(channel=msgdest, txt=f"Last Backup: *{lastBackup}*", thread_ts=ts)
                    elif split[2] == "runbackup":
                        backup()
                        sendSlackMsg(channel=msgdest, txt=f"Ran backup to S1! Last Backup: *{lastBackup}*", thread_ts=ts)
                else: 
                    sendSlackMsg(channel=msgdest, txt=f"{errmsg} You are authorized to modify admins.", thread_ts=ts)
            except:
                sendSlackMsg(channel=msgdest, txt=f"{errmsg} You are authorized to modify admins.", thread_ts=ts)
        else: 
            sendSlackMsg(channel=msgdest, txt=f"You can't run admin as you are not authorized to do so. DM <@UN6C43287> if this seems wrong.", thread_ts=ts)

    def edit(event, eventtype, split):
        ts = ""
        msgdest=event["channel"]
        if eventtype == "app_mention":
            ts = event["ts"]
        user=event["user"]
        errmsg=f"That's not the correct usage of edit. Usage: *<@{SLACK_BOT_ID}> edit [challengeid:int] [`param`:str] [val:str|int]*. You can get a list of parameters that can be edited by running *<@{SLACK_BOT_ID}> active*. DM <@UN6C43287> if this seems wrong."
        try:
            id=split[2]
            id=int(id)
            if len(split) >= 5:
                if ChallengeManager[id].isActive:
                    if ChallengeManager[id].user in user or user in admins:
                        if not ((split[3] == "isActive") or (split[3] == "id") or (split[3] == "scheduleditem") or not(split[3] in ChallengeManager[id].__dict__.keys())):
                            tmp=split[:]
                            tmp2=0
                            finalval=""
                            tmp.pop(0)
                            tmp.pop(0)
                            tmp.pop(0)
                            tmp.pop(0)
                            if len(tmp)>1:
                                for i in tmp:
                                    tmp2+=1
                                    if tmp2 == len((tmp)):
                                        finalval = finalval + i
                                    else:
                                        finalval = finalval + i + " "
                            else:
                                finalval = i
                            status = ChallengeManager[id].edit(split[3],finalval)
                            if status == True:
                                sendSlackMsg(msgdest, f"Successfully set parameter {split[3]} of challenge ID {id} to {finalval}. DM <@UN6C43287> if this seems wrong.")
                            else:
                                sendSlackMsg(msgdest, f"Unsuccessfully attempted to set parameter {split[3]} of challenge ID {id} to \"{finalval}\". DM <@UN6C43287> if this seems wrong.")
                        else:
                            sendSlackMsg(msgdest, f"You can't edit the {split[3]} parameter of challenge ID {id}. To stop or remove a challenge, use *<@{SLACK_BOT_ID}> delete [challengeid:int]*. DM <@UN6C43287> if this seems wrong.")
                    else:
                        sendSlackMsg(msgdest, f"You can't edit challenge ID {id} as you did not create it. DM <@UN6C43287> if this seems wrong.")
            else:
                sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)
        except Exception as e:
            print(e)
            sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)

    def delete(event, eventtype, split):
        ts = ""
        msgdest=event["channel"]
        if eventtype == "app_mention":
            ts = event["ts"]
        user=event["user"]
        errmsg=f"That's not the correct usage of delete. Usage: *<@{SLACK_BOT_ID}> delete [challengeid:int]*. You can get the ID of an existing challenge by using *<@{SLACK_BOT_ID}> active*, or create a new challenge by using *<@{SLACK_BOT_ID}> create*. DM <@UN6C43287> if this seems wrong."
        try:
            id=split[2]
            id=int(id)
            if len(split) == 3:
                if ChallengeManager[id].isActive:
                    if ChallengeManager[id].user == user or user in admins:
                        ChallengeManager[id].delete()
                        sendSlackMsg(channel=msgdest, txt=f"Successfully deleted challenge ID {id}.", thread_ts=ts)
                    else:
                        sendSlackMsg(channel=msgdest, txt=f"You can't delete challenge ID {id} as you did not create it. DM <@UN6C43287> if this seems wrong.", thread_ts=ts)
            else:
                sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)
        except:
            sendSlackMsg(channel=msgdest, txt=errmsg, thread_ts=ts)

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
                    split[1] = split[1].lower()
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
                        elif split[1] == "admin":
                            admin(event, eventtype, split)
                else: 
                    help(event["channel"])

    # Start the server on port 3000
    slack_events_adapter.start(port=port)

try:
    print(f"{getTime()}Starting scheduler... ")
    run_continuously()
    print(f"{getTime()}Started scheduler... ")
    schedule.every(5).minutes.do(backup)
    main(os.environ["PORT"])
except Exception as e:
    print(f"{getTime()}Exception: {e}")