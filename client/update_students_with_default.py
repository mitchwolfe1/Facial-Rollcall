import pyrebase
import time
# Setup firebase
config = {
  "apiKey": "AIzaSyDp1Ho37--UuuQcrMeqKJ9E9HtckQ_QpS4",
  "authDomain": "facialrec-bba5d.firebaseapp.com",
  "databaseURL": "https://facialrec-bba5d.firebaseio.com",
  "storageBucket": "facialrec-bba5d.appspot.com",
  "serviceAccount" : "../serviceAccountCredentials.json"
}
firebase = pyrebase.initialize_app(config)
now = int(time.time())
students_default = {
    "Students" : {
        "Firstname Lastname" : {
            "photo" : "photos/firstname-lastname.jpg", # must be photos/first-last.extension
            "encoding" : "encodings/firstname-lastname.enc", # must be encodings/first-last.enc
            "periods" : ["Test"] # list of periods ie Period 0, Period 3, Test, etc
        }
    }
}

students_ref = firebase.database()
students_ref.update(students_default)
