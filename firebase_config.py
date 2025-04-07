import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask_login import UserMixin
import pyrebase

# Path to the Firebase service account key JSON file
# You'll need to download this from Firebase console
SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'path/to/serviceAccountKey.json')

# Firebase web app configuration
# Replace these with your actual Firebase project configuration
FIREBASE_CONFIG = {
    "apiKey": os.environ.get('FIREBASE_API_KEY', "YOUR_API_KEY"),
    "authDomain": os.environ.get('FIREBASE_AUTH_DOMAIN', "your-project-id.firebaseapp.com"),
    "projectId": os.environ.get('FIREBASE_PROJECT_ID', "your-project-id"),
    "storageBucket": os.environ.get('FIREBASE_STORAGE_BUCKET', "your-project-id.appspot.com"),
    "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID', "your-messaging-sender-id"),
    "appId": os.environ.get('FIREBASE_APP_ID', "your-app-id"),
    "databaseURL": os.environ.get('FIREBASE_DATABASE_URL', "")
}

# Initialize Firebase Admin SDK (for server-side operations)
try:
    # Check if already initialized
    firebase_admin.get_app()
except ValueError:
    # Not initialized, so initialize
    try:
        if os.path.exists(SERVICE_ACCOUNT_PATH):
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        else:
            # For development or if the path isn't set
            service_account_info = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT', '{}'))
            if service_account_info:
                cred = credentials.Certificate(service_account_info)
            else:
                # For render.com, you would set this as an environment variable
                print("WARNING: No Firebase service account credentials found.")
                cred = None
        
        if cred:
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully")
        else:
            print("Firebase Admin initialization skipped - no credentials")
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")

# Initialize Pyrebase (for client-side operations like auth)
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
firebase_auth = firebase.auth()
firebase_db = firebase.database()

# Get a reference to the Firestore database
try:
    db = firestore.client()
    print("Firestore database connected successfully")
except Exception as e:
    print(f"Error connecting to Firestore: {e}")
    db = None

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, uid, email, display_name=None, photo_url=None):
        self.id = uid
        self.email = email
        self.display_name = display_name
        self.photo_url = photo_url
        
    @staticmethod
    def get(user_id):
        """Retrieve user from Firestore by user ID"""
        try:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return User(
                    uid=user_id,
                    email=user_data.get('email'),
                    display_name=user_data.get('display_name'),
                    photo_url=user_data.get('photo_url')
                )
        except Exception as e:
            print(f"Error getting user: {e}")
        return None
        
    def create_or_update(self):
        """Create or update user in Firestore"""
        try:
            user_ref = db.collection('users').document(self.id)
            user_data = {
                'email': self.email,
                'last_login': firestore.SERVER_TIMESTAMP
            }
            
            if self.display_name:
                user_data['display_name'] = self.display_name
                
            if self.photo_url:
                user_data['photo_url'] = self.photo_url
                
            user_ref.set(user_data, merge=True)
            return True
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return False
    
    def get_lists(self):
        """Get all game lists for this user"""
        try:
            lists_ref = db.collection('users').document(self.id).collection('lists')
            lists = lists_ref.get()
            return [{'id': doc.id, **doc.to_dict()} for doc in lists]
        except Exception as e:
            print(f"Error getting user lists: {e}")
            return []
    
    def create_list(self, list_name):
        """Create a new game list for this user"""
        try:
            lists_ref = db.collection('users').document(self.id).collection('lists')
            new_list = {
                'name': list_name,
                'description': '',  # Empty description by default
                'notes': '',  # Empty notes by default
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            new_list_ref = lists_ref.add(new_list)
            return new_list_ref[1].id  # Return the ID of the new list
        except Exception as e:
            print(f"Error creating list: {e}")
            return None
    
    def delete_list(self, list_id):
        """Delete a game list"""
        try:
            # First delete all games in the list
            games_ref = db.collection('users').document(self.id).collection('lists').document(list_id).collection('games')
            self._delete_collection(games_ref, 50)
            
            # Then delete the list itself
            list_ref = db.collection('users').document(self.id).collection('lists').document(list_id)
            list_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting list: {e}")
            return False
    
    def _delete_collection(self, collection_ref, batch_size):
        """Helper method to delete a collection"""
        docs = collection_ref.limit(batch_size).get()
        deleted = 0
        for doc in docs:
            doc.reference.delete()
            deleted += 1
        
        if deleted >= batch_size:
            return self._delete_collection(collection_ref, batch_size)
    
    def add_game_to_list(self, list_id, game_data):
        """Add a game to a list"""
        try:
            # Verify the list exists
            list_ref = db.collection('users').document(self.id).collection('lists').document(list_id)
            if not list_ref.get().exists:
                return False
            
            # Add a timestamp for client-side sorting (Firestore SERVER_TIMESTAMP can't be read directly)
            game_data['timestamp'] = int(time.time())
            
            # Add the game to the list
            game_ref = list_ref.collection('games').document(str(game_data['appid']))
            game_data['added_at'] = firestore.SERVER_TIMESTAMP
            game_ref.set(game_data)
            
            # Update the list's updated_at timestamp
            list_ref.update({'updated_at': firestore.SERVER_TIMESTAMP})
            return True
        except Exception as e:
            print(f"Error adding game to list: {e}")
            return False
    
    def remove_game_from_list(self, list_id, appid):
        """Remove a game from a list"""
        try:
            game_ref = db.collection('users').document(self.id).collection('lists').document(list_id).collection('games').document(str(appid))
            game_ref.delete()
            
            # Update the list's updated_at timestamp
            list_ref = db.collection('users').document(self.id).collection('lists').document(list_id)
            list_ref.update({'updated_at': firestore.SERVER_TIMESTAMP})
            return True
        except Exception as e:
            print(f"Error removing game from list: {e}")
            return False
    
    def get_games_in_list(self, list_id):
        """Get all games in a list"""
        try:
            games_ref = db.collection('users').document(self.id).collection('lists').document(list_id).collection('games')
            games = games_ref.get()
            return [doc.to_dict() for doc in games]
        except Exception as e:
            print(f"Error getting games in list: {e}")
            return []
    
    def is_game_in_list(self, list_id, appid):
        """Check if a game is in a list"""
        try:
            game_ref = db.collection('users').document(self.id).collection('lists').document(list_id).collection('games').document(str(appid))
            return game_ref.get().exists
        except Exception as e:
            print(f"Error checking if game is in list: {e}")
            return False
    
    def get_game_lists(self, appid):
        """Get all lists that contain a specific game"""
        try:
            lists = self.get_lists()
            result = []
            for list_info in lists:
                list_id = list_info['id']
                if self.is_game_in_list(list_id, appid):
                    result.append(list_info)
            return result
        except Exception as e:
            print(f"Error getting game lists: {e}")
            return []
            
    def update_list_metadata(self, list_id, field, value):
        """Update list metadata (name, description, notes)"""
        try:
            # Verify the list exists and belongs to this user
            list_ref = db.collection('users').document(self.id).collection('lists').document(list_id)
            if not list_ref.get().exists:
                print(f"List {list_id} not found for user {self.id}")
                return False
                
            # Only allow certain fields to be updated
            if field not in ['name', 'description', 'notes']:
                print(f"Invalid field: {field}")
                return False
                
            # Update the specified field
            update_data = {
                field: value,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            list_ref.update(update_data)
            
            print(f"Successfully updated {field} for list {list_id}")
            return True
        except Exception as e:
            print(f"Error updating list metadata: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def save_game_note(self, appid, note_text):
        """Save or update a note for a specific game"""
        try:
            # Create a document in the user's game_notes collection
            notes_ref = db.collection('users').document(self.id).collection('game_notes').document(str(appid))
            
            notes_data = {
                'appid': str(appid),
                'note': note_text,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # If this is a new note, add created_at
            note_doc = notes_ref.get()
            if not note_doc.exists:
                notes_data['created_at'] = firestore.SERVER_TIMESTAMP
                
            # Save the note
            notes_ref.set(notes_data, merge=True)
            
            print(f"Successfully saved note for game {appid}")
            return True
        except Exception as e:
            print(f"Error saving game note: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def get_game_note(self, appid):
        """Get a user's note for a specific game"""
        try:
            note_ref = db.collection('users').document(self.id).collection('game_notes').document(str(appid))
            note_doc = note_ref.get()
            
            if note_doc.exists:
                note_data = note_doc.to_dict()
                return note_data.get('note', '')
            else:
                return ''
        except Exception as e:
            print(f"Error retrieving game note: {e}")
            return ''
            
    def delete_game_note(self, appid):
        """Delete a note for a specific game"""
        try:
            note_ref = db.collection('users').document(self.id).collection('game_notes').document(str(appid))
            note_doc = note_ref.get()
            
            if note_doc.exists:
                note_ref.delete()
                print(f"Successfully deleted note for game {appid}")
                return True
            else:
                print(f"No note found for game {appid}")
                return False
        except Exception as e:
            print(f"Error deleting game note: {e}")
            return False 