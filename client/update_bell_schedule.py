import pyrebase

# Setup firebase
config = {
  "apiKey": "AIzaSyDp1Ho37--UuuQcrMeqKJ9E9HtckQ_QpS4",
  "authDomain": "facialrec-bba5d.firebaseapp.com",
  "databaseURL": "https://facialrec-bba5d.firebaseio.com",
  "storageBucket": "facialrec-bba5d.appspot.com",
  "serviceAccount" : "../serviceAccountCredentials.json"
}

firebase = pyrebase.initialize_app(config)

bell_schedule = {
    "Period 0" : {
        "Class Start" : "7:00 AM",
        "Class End" : "7:50 AM"
    },
    "Period 7" : {
        "Class Start" : "2:25 PM",
        "Class End" : "3:25 PM"
    },
    "A Day" : { # Even number date
        "Period 1" : {
            "Class Start" : "8:00 AM",
            "Class End" : "9:35 AM"
        },
        "Period 2" : {
            "Class Start" : "10:25 AM",
            "Class End" : "12:00 PM"
        },
        "Period 3" : {
            "Class Start" : "12:40 PM",
            "Class End" : "2:15 PM"
        }
    },
    "B Day" : { # Odd number date
        "Period 4" : {
            "Class Start" : "8:00 AM",
            "Class End" : "9:35 AM"
        },
        "Period 5" : {
            "Class Start" : "10:25 AM",
            "Class End" : "12:00 PM"
        },
        "Period 6" : {
            "Class Start" : "12:40 PM",
            "Class End" : "2:15 PM"
        }
    },
    "Test" : {
        "Class Start" : "",
        "Class End" : ""
    }
}

bell_schedule_ref = firebase.database().child("Bell Schedule")
bell_schedule_ref.set(bell_schedule)
