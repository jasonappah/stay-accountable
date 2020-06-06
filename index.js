require('dotenv').config()
var schedule = require('node-schedule');

// we need:
// question to send - got it
// cta to append to question to formulate message
// day number to start number of days to go
// time to send message

// enter the time in 24hr time. ex: 12:00pm = 12:00, 12:00am = 0:00, 11:00pm = 23:00. Defaults to 12pm if there is no value set in .env file
var time = process.env.SATIME || "12:00"
const question = process.env.SAQ || "Did you code today?"
const cta = process.env.SACTA || "React with :upvote: for yes, :downvote: for no."
const startday = process.env.SASTARTDAY || "1"
const endday = process.env.SAENDDAY || "100"
var currentday = startday


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
console.log(hr)

try {
    min = parseInt(newtime[1])
} catch (e) {
    throw ("The minute value is invalid. Please enter the time in 24hr format with a colon between the hour and minute (HH:MM).")
}
console.log(min)

var rule = new schedule.RecurrenceRule();
rule.hour = hr;
rule.minute = min;

var j = schedule.scheduleJob(rule, function() {
    currentday = currentday + 1
    console.log(`Day ${currentday}: ${question} $${cta}`)
    if (currentday >= endday) {
        console.log("This is the end.")
        j.cancel(false)
    }

});