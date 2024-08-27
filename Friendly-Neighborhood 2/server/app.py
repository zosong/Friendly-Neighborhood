import pyrebase
import firebase_admin
# from firebase_admin import firestore
from firebase_admin import credentials, firestore
from flask import Flask, request, render_template, redirect, session, jsonify, flash
from collections import OrderedDict
from datetime import datetime
import pandas as pd
import json
import requests
from requests.exceptions import HTTPError
from google.oauth2.credentials import Credentials
from google.cloud.firestore import Client
import re

#From https://docs.kickbox.com/docs/python-validate-an-email-address
def validate_email_syntax(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

cred = {
  'apiKey': "AIzaSyC2MbnAGYrnoE6JsF9RGl1vABa6Mz0Hy0I",
  'authDomain': "friendly-neighborhood-1d11f.firebaseapp.com",
  'databaseURL': "https://friendly-neighborhood-1d11f-default-rtdb.firebaseio.com",
  'projectId': "friendly-neighborhood-1d11f",
  'storageBucket': "friendly-neighborhood-1d11f.appspot.com",
  'messagingSenderId': "691675326636",
  'appId': "1:691675326636:web:7f811d2c78b97e13e91709",
  'measurementId': "G-635ZSVHC91"
}
cred2 = credentials.Certificate("friendly-neighborhood-1d11f-firebase-adminsdk-uo1ly-9cc21e303c.json")
app = firebase_admin.initialize_app(cred2)
db = firestore.client()

firebase = pyrebase.initialize_app(cred)
auth = firebase.auth()

app = Flask(__name__, template_folder="../client/templates", static_folder="../static")
app.config['SECRET_KEY'] = 'your_very_secret_key'
repsonse = []



#From this article https://medium.com/@bobthomas295/client-side-authentication-with-python-firestore-and-firebase-352e484a2634
FIREBASE_REST_API = "https://identitytoolkit.googleapis.com/v1/accounts"

def sign_in_with_email_and_password(api_key, email, password):
    request_url = "%s:signInWithPassword?key=%s" % (FIREBASE_REST_API, api_key)
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    
    resp = requests.post(request_url, headers=headers, data=data)
    # Check for errors
    try:
        resp.raise_for_status()
    except HTTPError as e:
        raise HTTPError(e, resp.text)
        
    return resp.json()


def getRole():
    if 'email' in session:
        user_email = session['email']
        user_ref = db.collection('users').document(user_email)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return user_data.get('role')
    return 'user'

def isBanned():
    if getRole() == 'banned':
        return True
    return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webApp')
def webApp():
    if 'email' not in session:
        return redirect('/login')
    role = getRole()
    return render_template('webApp.html', role = getRole())

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']
        if not validate_email_syntax(email):
            flash("Please enter a valid email")
            return render_template('login.html')
        if not email or not password:
            flash("Please enter a valid email and password")
            return render_template('login.html')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user_id'] = user['localId']
            session['email'] = email
            # https://medium.com/@bobthomas295/client-side-authentication-with-python-firestore-and-firebase-352e484a2634
            global response
            response = sign_in_with_email_and_password("AIzaSyC2MbnAGYrnoE6JsF9RGl1vABa6Mz0Hy0I", email, password)
            print(response)
            creds = Credentials(response['idToken'], response['refreshToken'])
            global db
            db = Client("friendly-neighborhood-1d11f", creds)

            print(f"Logged in as: {session['user_id']}")  # Debugging statement
            print(getRole())
            if getRole() == 'banned':
                return render_template('banned.html')
            return redirect('/webApp')  
        except:
            flash("Invalid email or password")
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    auth.current_user = None
    session.clear()
    return render_template('index.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']
        if not validate_email_syntax(email):
            flash("Please enter a valid email")
            return render_template('signup.html')
        if not email or not password:
            flash("Please enter a valid email and password")
            return render_template('signup.html')
        try:
            user = auth.create_user_with_email_and_password(email,password)
            session['user_id'] = user['localId']
            session['email'] = email
            user_data = {
            'username': session.get('email'),
            'role':'user',
            'blocked_users': []
            }
            db.collection('users').document(session['email']).set(user_data)
            return render_template('login.html')
        except:
            return render_template('index.html')
    else:
        return render_template('signup.html')
    
@app.route('/createPost', methods=['POST', 'GET'])
def createPost():
    if getRole() == 'banned':
        return render_template('banned.html')
    if 'email' not in session:
        return redirect('/login')
    # username = request.form['Username']
    if request.method == 'POST':
        text = request.form['Summary']
        title = request.form['Title']
        zip_code = request.form['ZipCode']
        longitude = request.form['Longitude']
        latitude = request.form['Latitude']
        interested = []

        #Zip code validation. Must be in uszips data frame
        df = pd.read_csv('../static/uszips.csv')
        zip_codes = df["zip"]
        zip_codes = zip_codes.astype(str)
        if not zip_code in zip_codes.values:
            flash("Please enter a valid zip code")
            return render_template('createPost.html', Longitude=-84.3, Latitude=30.45)
        
        else:
            post_data = {
                'username': session.get('email'),
                'text':text,
                'title':title,
                'zip_code':zip_code,
                'interested': interested,
                'last_modified': datetime.now().strftime('%m/%d/%Y %H:%M:%S'), # Zoe added for my post page
                'longitude': longitude,
                'latitude': latitude
            }
            try:

                #New DB
                doc_ref = db.collection('post').document()
                doc_ref.set(post_data)
                # user = db.child("post").push(post_data)

                print("Successfully added the post")
                return redirect('/webApp')
            except:
                return redirect('/webApp')
    return render_template('createPost.html', Longitude=-84.3, Latitude=30.45)

@app.route('/viewPosts', methods=['POST', 'GET'])
def viewPosts():
    if getRole() == 'banned':
        return render_template('banned.html')
    zip_code = request.args.get('zip_code')
    if request.method == 'POST' or not zip_code == None:
        if not zip_code:
            zip_code = request.form['ZipCode']
            # Make sure zip code is an int
        try:
            zip_code = int(zip_code)
            zip_code = str(zip_code)
        except:
            flash("Please enter a valid zip code")
            return render_template("getZipCode.html")   
        # New DB
        posts_ref = db.collection("post")
        posts_by_zip = posts_ref.where("zip_code", "==", zip_code).get()

        df = pd.read_csv('../static/uszips.csv')
        data = df[df['zip'] == int(zip_code)]
        longitude = data.lng.values[0]
        latitude = data.lat.values[0]

        posts_data = []
        for post in posts_by_zip:
            post_data = post.to_dict()
            post_data['id'] = post.id
            posts_data.append(post_data)

        role = getRole()
        print(role)
        mod_ref = db.collection("moderators").where("email", "==", session.get('email')).get()
        if mod_ref:
            mod_data = mod_ref[0].to_dict()  # Access the first document in the snapshot
            mod_zip = mod_data.get('zip_code')
        else:
            mod_zip = None
        return render_template('viewPosts.html', ZipCode=zip_code, posts=posts_data, Longitude=longitude, Latitude=latitude, role=role, mod_zip = mod_zip)
    return render_template("getZipCode.html")

    
@app.route('/myPosts', methods=['GET'])
def myPosts():
    if getRole() == 'banned':
        return render_template('banned.html')
    if 'email' not in session:
        return redirect('/')

    # New DB
    posts_ref = db.collection("post")
    posts_by_user = posts_ref.where("username", "==", session.get('email')).get()
    print("Number of posts: " , len(posts_by_user))
    posts_data = []
    interested = []

    for post in posts_by_user:
        post_data = post.to_dict()
        post_data['id'] = post.id  # Store Firestore document ID to identify the post later for edit/delete
        posts_data.append(post_data)

    for post in posts_by_user:
        for email in post.to_dict().get('interested', []):
            # Append each email to the corresponding index in the interested array
            interested.append(email)
    print(interested)
    
    
    return render_template('myPosts.html', posts=posts_data, interested_list=interested)

@app.route('/adminTools', methods=['GET', 'POST'])
def adminTools():
    if 'email' not in session:
        return redirect('/login')
    if getRole() != 'admin':
        return "Unauthorized", 403
    
    #For moderators
    mod_ref = db.collection("moderators")
    mod_list = mod_ref.get()
    mods_data = []
    for mod in mod_list:
        mod_data = mod.to_dict()
        mod_data['id'] = mod.id  # Store Firestore document ID to identify the post later for edit/delete
        mods_data.append(mod_data)
    
    #For banned users
    banned_ref = db.collection("banned_users")
    ban_list = banned_ref.get()
    bans_data = []
    for ban in ban_list:
        ban_data = ban.to_dict()
        ban_data['id'] = ban.id  # Store Firestore document ID to identify the post later for edit/delete
        bans_data.append(ban_data)

    if request.method == 'POST':
        zip = request.form['ZipCode']
        email = request.form['Email']
        if not email or not zip:
            flash("Please enter a valid email and zip code")
            return render_template('adminTools.html', moderators=mods_data)
        try:
            zip = int(zip)
            zip = str(zip)
        except:
            flash("Please enter a valid zip code")
            return render_template('adminTools.html', moderators=mods_data)
        if (not validate_email_syntax(email)):
            flash("Please enter a valid email")
            return render_template('adminTools.html', moderators=mods_data)
        user_ref = db.collection('users').document(email)
        user_doc = user_ref.get()
        if user_doc.exists:
            # If they're already a mod
            if user_doc.to_dict().get('role') == 'moderator':
                flash(email + " is already a moderator")
                return render_template('adminTools.html' , moderators=mods_data, banned_users=bans_data)
            else:
                user_ref.update({'role': 'moderator'})
                moderators_ref = db.collection('moderators')
                moderators_ref.add({
                    'email': email,
                    'zip_code': zip
                })
                mods_data.append({'email': email, 'zip_code': zip})
        else:
            flash("User does not exist")
    return render_template('adminTools.html', moderators=mods_data, banned_users=bans_data)

@app.route('/banUser', methods=['GET', 'POST'])
def banUser():
    if 'email' not in session:
        return redirect('/login')
    if getRole() != 'admin':
        return "Unauthorized", 403
    elif request.method == 'POST':
        ban_email = request.form['Email']
        user_ref = db.collection('users').document(ban_email)
        if validate_email_syntax(ban_email) == False:
            flash("Please enter a valid email")
            return redirect('/adminTools')
        elif not user_ref.get().exists:
            flash("User does not exist")
            return redirect('/adminTools')
        user_doc = user_ref.get()
        if user_doc.to_dict().get('role') == 'banned':
            flash(ban_email + " is already banned", 'error')
        elif ban_email == session.get('email'):
            flash("You cannot ban yourself", 'error')
        elif user_doc.to_dict().get('role') == 'admin':
            flash("You may not ban another admin", 'error')
        else:
            user_ref = db.collection('users').document(ban_email)
            user_ref.update({'role': 'banned'})
            banned_user_ref = db.collection('banned_users')
            banned_user_ref.add({
                'email': ban_email
            })

    return redirect('/adminTools')

@app.route('/unbanUser', methods=['GET', 'POST'])
def unbanUser():
    if 'email' not in session:
        return redirect('/login')
    elif getRole() != 'admin':
        return "Unauthorized", 403
    elif request.method == 'POST':
        ban_email = request.form['Email']
        ban_id = request.form['Banned_Id']
        user_ref = db.collection('users').document(ban_email)
        user_ref.update({'role': 'user'})

        banned_user_ref = db.collection('banned_users').document(ban_id)
        banned_user_ref.delete()
    return redirect('/adminTools')

@app.route('/deleteModerator', methods=['GET', 'POST'])
def deleteModerator():
    if 'email' not in session:
        return redirect('/login')
    if getRole() != 'admin':
        return "Unauthorized", 403
    mod_id = request.form['mod_id']
    mod_email = request.form['email']
    mod_ref = db.collection("moderators").document(mod_id)
    mod_ref.delete()
    user_ref = db.collection('users').document(mod_email)
    user_ref.update({'role': 'user'})
    return redirect('/adminTools')

@app.route('/viewPostDetail', methods=['GET', 'POST'])
def viewPostDetail():
    if getRole() == 'banned':
        return render_template('banned.html')
    postId = request.args.get("postId")
    print("postId:", postId)  # Debug print
    post_doc_ref = db.collection("post").document(postId)
    post_data = post_doc_ref.get().to_dict()

    if 'email' in session and is_user_blocked(session['email'], post_data['username']):
        return jsonify({'error': 'You are blocked'}), 403

    comments_data = []
    comments_ref = post_doc_ref.collection("comments").get()
    for comment in comments_ref:
        comments_data.append(comment.to_dict())

    # If they click the link from the viewPosts page
    if request.method == 'GET':
        return render_template('viewPostDetail.html', post=post_data, comments=comments_data, postId=postId)

    # If they comment under the post, or can help
    if request.method == 'POST':
        comment_selected = request.form.get('comment')
        interest_selected = request.form.get('interest')

        if comment_selected:
            comment = request.form['comment']
            comment_data = {
                'username': session.get('email'),
                'text': comment
            }
            try:
                print("id: ", postId)
                post_doc_ref.collection("comments").add(comment_data)
                print("Successfully added the comment")
                return redirect('/viewPostDetail?postId=' + postId)
            except:
                return redirect('/viewPostDetail?postId=' + postId)
    if request.method == 'POST':
        if request.form.get('interest'):
            # Add user's email to the interested list using ArrayUnion
            try:
                post_doc_ref.update({
                    'interested': firestore.ArrayUnion([session['email']])
                })
                flash("Thank you for your interest!", 'success')
            except Exception as e:
                flash("Failed to express interest.", 'error')
                print(e)  # Log the error for debugging
        return redirect(f'/viewPostDetail?postId={postId}')
        
@app.route('/deletePost', methods=['POST'])
def deletePost():
    if 'email' not in session:
        return redirect('/login')  
    post_id = request.form['postId']  # Get the post ID 
    deleteFromViewPosts = request.form.get('deleteFromViewPosts') # If the admin is deleting it
    post_doc_ref = db.collection("post").document(post_id)
    post_data = post_doc_ref.get().to_dict()
    moderator_zip = -1
    if getRole() == 'moderator':
        moderator_doc = db.collection('moderators').where('email', '==', session.get('email')).limit(1).get()
        if moderator_doc:
            moderator_zip = moderator_doc[0].to_dict().get('zip_code')
        else:
            moderator_zip = None
    if post_data and (post_data.get('username') == session.get('email') or getRole() == 'admin' or 
                      (getRole() == 'moderator' and moderator_zip == post_data.get('zip_code'))):
        post_doc_ref.delete()
        # If the admin/mod is deleting it from the viewPosts page, redirect to viewPosts
        if deleteFromViewPosts:
            print(deleteFromViewPosts)
            return redirect(f'/viewPosts?zip_code={deleteFromViewPosts}')
        return redirect('/myPosts') 
    else:
        return "Unauthorized", 403

@app.route('/editPostForm', methods=['GET'])
def editPostForm():
    if 'email' not in session:
        return redirect('/login')
    postId = request.args.get('postId')
    post_doc_ref = db.collection("post").document(postId)
    post_data = post_doc_ref.get().to_dict()
    if post_data and post_data.get('username') == session.get('email'):
        return render_template('editPost.html', post=post_data, postId=postId)
    else:
        return "Unauthorized", 403


@app.route('/submitEditPost', methods=['POST'])
def submitEditPost():
    if 'email' not in session:
        return redirect('/login')
    postId = request.form['postId']
    new_text = request.form['text']

    # Update the last modified time to the current time
    last_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    post_doc_ref = db.collection("post").document(postId)
    post_doc_ref.update({
        'text': new_text,
        'last_modified': last_modified  # Update the last modified time in the database
    })
    return redirect(f'/viewPostDetail?postId={postId}')

@app.route('/search', methods=['POST'])
def searchZipCode():
    zipcode = request.form['zipCode']
    longitude = -84.3
    latitude = 30.45
    if zipcode.isdigit() or (zipcode[0] == "-" and zipcode[1:-1].isdigit()):
        df = pd.read_csv('../static/uszips.csv')
        data = df[df['zip'] == int(zipcode)]
        longitude = data.lng.values[0]
        latitude = data.lat.values[0]
    return render_template('createPost.html', Longitude=longitude, Latitude=latitude)


@app.route('/blockUser', methods=['POST'])
def blockUser():
    if 'email' not in session or 'user_id' not in session:
        print("No user logged in.")
        return redirect('/login')  

    user_to_block = request.form['userToBlock']
    current_user_id = session['email']

    print(f"Current user ID: {current_user_id}")  # Debugging statement

    user_ref = db.collection('users').document(current_user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        print("User document does not exist.")
        return "User document not found", 404  

    user = user_doc.to_dict()

    if user_to_block not in user.get('blocked_users', []):
        user['blocked_users'].append(user_to_block)
        user_ref.update({'blocked_users': user['blocked_users']})
        print(f"User {user_to_block} blocked.")
        return redirect('/myPosts')
    else:
        return "User already blocked", 403

def is_user_blocked(blocked_user, blocking_user):
    blocking_user_ref = db.collection('users').document(blocking_user)
    blocking_user_doc = blocking_user_ref.get()
    if blocking_user_doc.exists:
        blocking_user_data = blocking_user_doc.to_dict()
        blocked_users = blocking_user_data.get('blocked_users', [])
        return blocked_user in blocked_users
    return False

@app.route('/blockList')
def blockList():
    if 'email' not in session:
        return redirect('/login')  
    
    current_user_id = session['email']
    user_ref = db.collection('users').document(current_user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return "User document not found", 404  # Handle missing user document
    
    user_data = user_doc.to_dict()
    blocked_users = user_data.get('blocked_users', [])

    return render_template('blockList.html', blocked_users=blocked_users)

@app.route('/unblockUser', methods=['POST'])
def unblockUser():
    if 'email' not in session:
        return redirect('/login')

    user_to_unblock = request.form['userToUnblock']
    current_user_id = session['email']

    # Fetch the current user's document
    user_ref = db.collection('users').document(current_user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        blocked_users = user_data.get('blocked_users', [])
        if user_to_unblock in blocked_users:
            blocked_users.remove(user_to_unblock)
            user_ref.update({'blocked_users': blocked_users})
            flash(f"User {user_to_unblock} unblocked successfully.", 'success')
        else:
            flash("User not found in blocked list.", 'error')
    else:
        flash("Current user document not found.", 'error')

    return redirect('/blockList')



def format_date(value, format_string='%Y-%m-%d'):
    if isinstance(value, datetime):
        return value.strftime(format_string)
    return value 

app.jinja_env.filters['dateformat'] = format_date

@app.route('/profile', methods=['GET'])
def profile():
    if 'email' not in session:
        return redirect('/login')
    
    user_ref = db.collection('users').document(session['email'])
    user_doc = user_ref.get()
    profile = user_doc.to_dict() if user_doc.exists else {}
    if profile and 'birthday' in profile and isinstance(profile['birthday'], datetime):
        profile['birthday'] = profile['birthday'].strftime('%Y-%m-%d')
    
    return render_template('profile.html', profile=profile)


@app.route('/updateProfile', methods=['GET', 'POST'])
def updateProfile():
    if 'email' not in session:
        return redirect('/login')
    
    user_ref = db.collection('users').document(session['email'])
    
    if request.method == 'POST':

        birthday = datetime.strptime(request.form['birthday'], '%Y-%m-%d')
        user_ref.update({
            'location': request.form['location'],
            'birthday': birthday,  # Save as a datetime object
            'pronouns': request.form['pronouns']
        })
        flash('Profile updated successfully!', 'success')
        return redirect('/profile')
    
    user_doc = user_ref.get()
    profile = user_doc.to_dict() if user_doc.exists else {}
    if profile and 'birthday' in profile and isinstance(profile['birthday'], datetime):
        profile['birthday'] = profile['birthday'].strftime('%Y-%m-%d')
    
    return render_template('updateProfile.html', profile=profile)

@app.route('/viewProfile', methods=['GET'])
def viewProfile():
    user_id = request.args.get('userId')
    print("Attempting to view profile for user ID:", user_id)  # Debug print

    if 'email' not in session:
        flash("Please log in to view profiles.", 'error')
        print("Redirecting to login, no email in session.")  # Debug print
        return redirect('/login')

    if not user_id:
        flash("No user ID provided.", 'error')
        return redirect('/webApp')

    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        flash('User profile not found.', 'error')
        return redirect('/webApp')

    profile = user_doc.to_dict()
    if is_user_blocked(session['email'], user_id):
        flash('You are blocked from viewing this profile.', 'error')
        return jsonify({'error': 'You are blocked'}), 403

    posts_ref = db.collection('post').where('username', '==', user_id).get()
    posts = [post.to_dict() for post in posts_ref if not is_user_blocked(session['email'], post.to_dict()['username'])]

    return render_template('viewProfile.html', profile=profile, posts=posts)


if __name__ == '__main__':
   app.run(debug=True)
