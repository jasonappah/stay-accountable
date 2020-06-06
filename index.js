require('dotenv').config()
const request = require('request');
// I know it's deprecated, but it still works ¯\_(ツ)_/¯
var schedule = require('node-schedule');

// enter the time in 24hr time. ex: 12:00pm = 12:00, 12:00am = 0:00, 11:00pm = 23:00. Defaults to 12pm if there is no value set in .env file
var time = process.env.SATIME || "12:00"
const question = process.env.SAQ || "Did you code today?"
const cta = process.env.SACTA || "React with :upvote: for yes, :downvote: for no."
var startday = process.env.SASTARTDAY || "1"
var endday = process.env.SAENDDAY || "100"
const botname = process.env.SABOTNAME || "AccountabilityBot"
var currentday = process.env.SACURRENTDAY || startday
const endmsg = "This is the final day."

const app = new Object({
    token: process.env.SLACK_BOT_TOKEN,
    signingSecret: process.env.SLACK_SIGNING_SECRET
});

if (time.length != 5) {
    throw ("The time value is invalid. Please enter the time in 24hr format with a colon between the hour and minute (HH:MM).")
}

var hr, min;

var newtime = time.split(":")
console.log(newtime)
try {
    hr = parseInt(newtime[0])
} catch (e) {
    throw ("The hour value is invalid. Please enter the time in 24hr format with a colon between the hour and minute (HH:MM).")
}

try {
    min = parseInt(newtime[1])
} catch (e) {
    throw ("The minute value is invalid. Please enter the time in 24hr format with a colon between the hour and minute (HH:MM).")
}

try {
    startday = parseInt(startday)
} catch (e) {
    throw ("The startday value is invalid. Please enter an integer.")
}

try {
    endday = parseInt(endday)
} catch (e) {
    throw ("The endday value is invalid. Please enter an integer.")
}

try {
    currentday = parseInt(currentday)
} catch (e) {
    throw ("The currentday value is invalid. Please enter an integer.")
}


var rule = new schedule.RecurrenceRule();
rule.hour = hr;
rule.minute = min;

console.log("Creating job")
    // var j = schedule.scheduleJob({ hour: hr, minute: min}, function() {
var j = schedule.scheduleJob({ second: 1 }, function() {
    if (currentday >= endday) {
        console.log(`${endmsg} Day ${currentday}: ${question} ${cta}`)
        this.cancel(false)
    } else {
        console.log(`Day ${currentday}: ${question} ${cta}`)
    }
    currentday = currentday + 1
});
console.log("Created job")
console.log(j.nextInvocation())