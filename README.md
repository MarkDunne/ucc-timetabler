UCC Timetabler
==============

This is a web application made to take timetables from University College Cork and put them automatically into your Google Calander. It is built to run on a Google AppEngine server

Why?
----

If you are a student at UCC you know all too well how awful the timetables are. There is no easy way to access your own timetable and it is not easy to read. You can't even use a link to get at your course timetable and site also goes down a couple of times a week. 

Just look at this crap - [Example](https://github.com/MarkDunne/ucc-timetabler/blob/master/example.html)

Under the hood
------------

(I think there is some cool stuff in here)

* First thing is to ask the user to log into their Google account and ask for permission to use the calander. This is done using OAuth2. I decided to implement OAuth2 myself and not use Google's libraries because I feel I learnt more this way and I had some trouble dealing with the AppEngine enviroment too.

* Then the application serves a standard HTML page that lets the user pick which programme/course they want in their calander.

* After this point, everything is 'ajax-ified' so that the user is never looking at a blank screen asking wtf is happening

* Once a programme has been selected, the code is sent to the server which downloads timetable from the UCC site.

* This is then parsed and added to a database (or datastore) so that no one course needs to be parsed twice by the server

* Once this is done, the server returns a list of modules contained within the course and asks the user to pick which ones they want to send to the calander.

* This list is sent back, a new Calander is created in the users Account then is populated with the correct modules from the database

* All done
