# Firebase Setup for SteamSeek

Follow these steps to set up Firebase for user authentication and saved lists:

## 1. Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click on "Add project"
3. Enter a project name (e.g., "SteamSeek")
4. Enable Google Analytics if desired (recommended)
5. Select your Google Analytics account or create a new one
6. Click "Create project"

## 2. Set Up Authentication

1. In your Firebase project, click on "Authentication" in the left sidebar
2. Click on "Get started"
3. Under "Sign-in method", click on "Google"
4. Enable Google authentication by toggling the switch to "Enabled"
5. Add your Project support email (your email address)
6. Click "Save"

## 3. Create Firestore Database

1. In the left sidebar, click on "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" (we'll set up proper security rules later)
4. Select a location closest to your users
5. Click "Enable"

## 4. Register Your Web App

1. Go to Project Overview
2. Click on the web icon (</>) to add a web app
3. Register your app with a nickname (e.g., "steamseek-web")
4. Check "Also set up Firebase Hosting" if you plan to use it (optional)
5. Click "Register app"
6. Copy the Firebase configuration code that looks like this:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyA_YOUR_API_KEY_HERE",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abc123def456",
  measurementId: "G-MEASUREMENT_ID"
};
```

7. Save this configuration - you'll need it for the app

## 5. Create a Service Account for Server-Side Access

1. Go to Project Settings (gear icon in the top left)
2. Go to the "Service accounts" tab
3. Click "Generate new private key"
4. Download the JSON file
5. Keep this file secure - it contains sensitive credentials

## 6. Set Up Security Rules

1. Go to Firestore Database
2. Click on the "Rules" tab
3. Update the rules to:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      // Lists
      match /lists/{listId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
        
        // Games in lists
        match /games/{gameId} {
          allow read, write: if request.auth != null && request.auth.uid == userId;
        }
      }
    }
  }
}
```

4. Click "Publish"

Once you have completed these steps, you'll have the Firebase configuration needed for the app. We'll use both the web config and the service account JSON in our Flask application. 