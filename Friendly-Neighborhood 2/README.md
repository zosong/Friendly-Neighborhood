# Friendly-Neighborhood
COP4521 - A web app to facilitate helping those nearby in need. We seek to bring communities together by allowing users to request help and connect with other people who are willing to help. To keep the forums safe, we have implemented moderation techniques to ensure that malicious posts can be removed. 

# Libraries
Pyrebase - For authentication to our database

Firebase_admin - To make our queries to our database

Flask - For our page routing and navigation

Requests - To connect to our database as a client

google.oauth2.credentials - To connect to our database as a client

google.cloud.firestore - To connect to our database as a client

pandas - To make sure the zip code is valid

re - To make sure email is valid

json - To save the response from our database when we log in as a client

collections - To store our responses from our database

# Other resources
https://docs.kickbox.com/docs/python-validate-an-email-address - To ensure that emails are formatted correctly

https://medium.com/@bobthomas295/client-side-authentication-with-python-firestore-and-firebase-352e484a2634 - Showed how to connect to a database as a client

Firebase - We used firebase for our database, and used their firestore service.

Mapbox - We used the mapbox API to display our posts on the map you see on the "create a post" and "view posts" pages

Zip Code CSV - We used this to shift the map to the corresponding longitude and latitiude values based on the given zip code

# Extra features
  - Block users
  - Admin global block users
  - Map marks location for posts' zipcode
  - Users' profile views  

# Separation of work
Albert Martinez 
  - Implemented Rules for RBAC
  - User validations
  - Zip code input validation
  - Bugs
  - Like button for posts(Incomplete, as I had hoped to push a list of those interested to the person who made a post). This list only appears in the database
  
  
John Whiddon - 
  - Implemented connecting to the DB as a client, to ensure that backend rules apply
  - Set up initial firebase database. Switched the database from Realtime database to Firestore midway through the project
  - Admin tools page
  - Admin functionality in flask
      - Ability to assign and remove moderators from a selected zip code
      - Ability to ban and unban users
      - Ability to delete posts from any zip code
  - Moderator functionality in flask
      - Ability to delete any post within their zip code
  - Banned user functionality in flask
      - Implement various checks to ensure banned users cannot do anything
  - Implemented ability to create a post
  - Added comment functionality on posts
  - Added ability to search posts by zip code
  - Added ability to view the details of the post by clicking on it
    
Benjamin Payne - 
  - Implemented map box in the create post
    - Search zipcode and it will take map to that zipcode
    - When the post is submitted it adds the latitude and longitude of the center of the map to the post
  - Implement displaying posts in the mapbox
    - When the user displays posts for a zipcode the post for that zipcode show up on the map

Sebastian Blanco -
  - Implemented flask templates to create different webpages for logging in, viewing posts, creating posts, etc
  - Implemented Mapbox api to show where the posts are coming from when viewing posts
  - CSS styling

Rafael Schulze - 
  - Implemented backend RBAC security rules for Firestore database
  - Participated in the Distribution Plan write-up

Zoe Song -
  - Implemented "My posts" page, which includes the users' history post with view detail and delete option.
  - Implemented session key to improve security
  - Block user functionality in flask
    - Ability to allow users block each other
    - Whoever was blocked, can't view the blocking users' posts or profile
  - Unblock user functionality in flask
    - Ability to allow users to remove someone from the block list
  - Implemented dropdown bar for all pages to guide user to other pages.
  - Implemented "Profile" "View Profile" and "Update Profile" pages.
    - Ability to allow users to update personal information and view others' information
    - Associate with block function
