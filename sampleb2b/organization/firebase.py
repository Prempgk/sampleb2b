# Firebase db initialization process
import pyrebase

cred = {
    "type": "service_account",
    "apiKey": "AIzaSyCYc59KHvVrA36KRjYXGumK66uv-7oLBug",
    "authDomain": "sampleb2bcourses.firebaseapp.com",
    "projectId": "sampleb2bcourses",
    "storageBucket": "sampleb2bcourses.appspot.com",
    "messagingSenderId": "1053805573938",
    "appId": "1:1053805573938:web:135e905e69e887a173092b",
    "measurementId": "G-7KTG7PHPHE",
    "databaseURL": "https://sampleb2bcourses-default-rtdb.firebaseio.com/"
}

fb = pyrebase.initialize_app(cred)

fb_auth = fb.auth()
fb_db = fb.database()
