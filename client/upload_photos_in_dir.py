import pyrebase
import sys
import os
import face_recognition as fr
import pickle
import codecs
import shutil

# Setup firebase
config = {
  "apiKey": "AIzaSyDp1Ho37--UuuQcrMeqKJ9E9HtckQ_QpS4",
  "authDomain": "facialrec-bba5d.firebaseapp.com",
  "databaseURL": "https://facialrec-bba5d.firebaseio.com",
  "storageBucket": "facialrec-bba5d.appspot.com",
  "serviceAccount" : "../serviceAccountCredentials.json"
}

firebase = pyrebase.initialize_app(config)
database = firebase.database()
storage = firebase.storage()

if not len(sys.argv) > 1:
    print("Please specify photos directory in command line argument:\npython3 upload_photos_in_dir.py [directory_where_photos_are]")
    exit(1)

photos_dir = sys.argv[1]

photo_extensions = (".png", ".jpg", ".jpeg")

temp_dir = os.path.join(os.getcwd(), 'temp_upload')

if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

for photo in os.listdir(photos_dir):
    photo_path = os.path.join(photos_dir, photo)
    #verify the file is an image of acceptible format
    if not photo.lower().endswith(photo_extensions):
        print("Skipping: \"" + photo + "\" as it is not an image file with an acceptable format")
        continue

    #verify the photo name meets our format
    if len(photo.split("-")) == 2 and (not " " in photo):
        pass
    else:
        print("Skipping: \"" + photo + "\" as it does not meet the name requirements.\nMake sure the file is named \'firstname-lastname\'.png/jpg/jpeg")
        continue

    photo_image = fr.load_image_file(photo_path)

    photo_encodings = fr.face_encodings(photo_image)

    # check if photo has exactly 1 face
    if not len(photo_encodings) == 1:
        print("Skipping: \"" + photo + "\" as it does not contain exactly 1 face")
        continue

    photo_encoding = photo_encodings[0]

    photo_full_name = photo.lower().split(".")[0].replace("-", " ").title()
    b64_photo_encoding = codecs.encode(pickle.dumps(photo_encoding), "base64")

    formatted_photo_name = photo.split(".")[0].lower() + "." + photo.split(".")[1].lower()

    updated_student = {
        "encoding" : "encodings/" + str(photo.lower().split(".")[0] + ".enc"),
        "photo" : "photos/" + formatted_photo_name,
        "periods" : ["Period 0", "Period 1", "Period 2", "Period 3", "Period 4", "Period 5", "Period 6", "Period 7", "Period 8"] # default to all periods
    }

    print("Updating student: " + photo_full_name)

    database.child("Students").child(photo_full_name).set(updated_student)

    shutil.copyfile(photo_path, "temp_upload/" + formatted_photo_name)

    encoding_file_path = os.path.join(temp_dir, formatted_photo_name.split(".")[0] + ".enc")

    with open(os.path.join(temp_dir, formatted_photo_name.split(".")[0] + ".enc"), 'wb+') as f:
        f.write(b64_photo_encoding)

    storage.child("photos/" + formatted_photo_name).put("temp_upload/" + formatted_photo_name)
    storage.child("encodings/" + formatted_photo_name.split(".")[0] + ".enc").put(encoding_file_path)

print("Flushing temp directory...")
shutil.rmtree(temp_dir)
