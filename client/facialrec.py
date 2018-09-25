import cv2
import face_recognition
import pyrebase
import pickle
import codecs
import shutil
import os
import sys
from datetime import datetime
from pytz import timezone
from multiprocessing import Process
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
storage = firebase.storage()
database = firebase.database()

known_student_names = []
known_student_encodings = []
known_student_periods = {}

temp_dir = os.path.join(os.getcwd(), 'students_cache')

if "--no-recache" in sys.argv:
    print("WARNING: Using local cache can be inaccurate. \nUse this flag only if you are sure that the data is correct.")
    for file in os.listdir(temp_dir):
        if file == "studentData.pkl":
            with open(os.path.join(temp_dir, "studentData.pkl"), "rb") as f:
                known_student_names, known_student_encodings, known_student_periods = pickle.loads(codecs.decode(f.read(), "base64"))

else:
    print("Gathering data from backend...")

    students = database.child("Students").get().val()

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    for student in students:
        student_data = students[student]
        storage_encoding_path = student_data["encoding"]
        student_encoding_file = os.path.split(storage_encoding_path)[1]
        storage.child(storage_encoding_path).download(os.path.join(temp_dir, student_encoding_file))
        with open(os.path.join(temp_dir, student_encoding_file), 'rb') as f:
             known_student_encodings.append(pickle.loads(codecs.decode(f.read(), "base64")))
        os.remove(os.path.join(temp_dir, student_encoding_file))
        known_student_names.append(student)
        known_student_periods[student] = student_data["periods"]
    with open(os.path.join(temp_dir, "studentData.pkl"), 'wb+') as f:
        f.write(codecs.encode(pickle.dumps([known_student_names, known_student_encodings, known_student_periods]), "base64"))

# Verify that the encodings were successfully matched to names
if not len(known_student_names) == len(known_student_encodings):
    print("There was an error getting the encodings matched to names, please try again")
    exit(0)
# Flush temp directory for encodings
# print("Flushing cache directory...")
# shutil.rmtree(temp_dir)

#get bell schedule
bell_schedule = dict(database.child("Bell Schedule").get().val())
# Get data for the day
def now_data():
    pst_tz = timezone('US/Pacific')
    today = datetime.now(tz=pst_tz)
    day_string = ""
    if today.day % 2 == 0:
        # Even day is A Day
        day_string = "A Day"
    else:
        # Odd day is B Day
        day_string = "B Day"
    ymd_string = today.strftime("%Y-%m-%d")
    return (day_string, ymd_string, today)

process_this_frame = True
#bgr colors
green_color = (0, 255, 0)
blue_color = (255, 0, 0)
red_color = (0, 0, 255)
#stroke for rects
stroke = 2

min_recognition_length = 30 # num of processed frames that the person has to be recognized for
recognized_people = [] # Holds names of verified students
people_num_frames = {} # holds name until min_recognition_length is completed

def checkin_student(name):
    print("Checking in: " + name)
    def _datetime_to_timestamp(dt):
        return time.mktime(dt.timetuple())
    def _period_for_time(time, periods):
        #assemble period times in timestamp format
        period_times = {}
        for key in periods.keys():
            period_time_dict = {}
            for id in periods[key].keys():
                id_str_time = periods[key][id]
                id_meridian_designation = id_str_time.split(" ")[-1]
                id_hours = int(id_str_time.split(":")[0])
                if id_meridian_designation == "AM" and id_hours == 12:
                    id_hours = 0
                elif id_meridian_designation == "PM" and not id_hours == 12:
                    id_hours = id_hours + 12
                id_minutes = int(id_str_time.split(":")[1].split(" ")[0])
                id_time = time.replace(minute=id_minutes, hour=id_hours, second=0)
                period_time_dict[id] = _datetime_to_timestamp(id_time)
            period_times[key] = period_time_dict

        sorted_periods = sorted(period_times.keys())
        now_timestamp = _datetime_to_timestamp(time)
        for period_name in sorted_periods:
            end_timestamp = period_times[period_name]["Class End"]
            if now_timestamp < end_timestamp:
                return period_name
        return "Error" # return is error if after last class ()

    day_string, ymd_string, now = now_data()
    periods = {}
    for key in bell_schedule.keys():
        if key == day_string:
            for period in bell_schedule[key]:
                periods[period] = bell_schedule[key][period]
        elif "Period" in key:
            periods[key] = bell_schedule[key]
        elif "Test" in key:
            periods[key] = bell_schedule[key]
    checkin_period = _period_for_time(now, periods)
    if checkin_period == "Error":
        return # dont checkin if can't find period
    if not checkin_period in known_student_periods[name]:
        return # dont checkin student if they don't have that period

    checkin_json = {
        "time" : _datetime_to_timestamp(now)
    }

    database.child("Attendance").child(ymd_string).child(checkin_period).child(name).update(checkin_json)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if ret == False:
        print("An error occured capturing the webcam. Make sure it is plugged in and try again!")
        exit(1)

    #begin matching face to encoding
    #convert to smaller image for faster face matching
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25) # make frame 1/4 size
    rgb_small_frame = small_frame[:, :, ::-1] # convert from bgr to rgb

    if process_this_frame: # calc for every other frame for speed
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_student_encodings, face_encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = known_student_names[first_match_index]
            face_names.append(name)

            if not name in recognized_people:
                if not name in people_num_frames.keys():
                    if not name == "Unknown": people_num_frames[name] = 1
                else:
                    people_num_frames[name] = people_num_frames[name] + 1

            for person in list(people_num_frames.keys()):
                num_frames = people_num_frames[person]
                if num_frames >= min_recognition_length:
                    del people_num_frames[person]
                    if not person in recognized_people:
                        checkin_student(person)
                        recognized_people.append(person)

    for person in set(people_num_frames.keys()).difference(face_names):
        del people_num_frames[person]

    process_this_frame = not process_this_frame # invert

    # display onscreen
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        #scale coords
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        box_color = ()
        if name == "Unknown":
            box_color = red_color
        elif name in recognized_people:
            box_color = green_color
        else:
            box_color = blue_color

        #box around face
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, stroke)

        # Draw label below face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


    cv2.imshow("Webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
