# Deploying SteamSeek to Render.com

This guide will walk you through deploying SteamSeek to [Render.com](https://render.com), including setting up Firebase authentication and database.

## Prerequisites

1. Complete the Firebase setup as outlined in `firebase_setup.md`
2. Have your Firebase configuration information ready:
   - Firebase Web SDK configuration (from Firebase Console)
   - Firebase Service Account key (downloaded JSON file)
3. A [Render.com](https://render.com) account

## Step 1: Prepare Your Environment Variables

When deploying to Render, you'll need to set up environment variables instead of using the .env file:

1. Firebase configuration
2. OpenRouter API keys
3. Other service credentials

## Step 2: Create a Render Web Service

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click on "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure your web service:
   - **Name**: SteamSeek (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Select Free (for testing) or paid plan for production

## Step 3: Set Environment Variables

In your Render web service settings, add these environment variables:

### Firebase Configuration
```
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
FIREBASE_APP_ID=your-app-id
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
```

### Firebase Service Account
Instead of uploading the JSON file, copy its contents and set as:
```
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"your-project-id",...}
```

### Google OAuth Configuration
```
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### OpenRouter API Configuration
```
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```

### Flask Configuration
```
FLASK_SECRET_KEY=your-secure-random-key
```

## Step 4: Configure Google OAuth Callback URL

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to "APIs & Services" > "Credentials"
3. Edit your OAuth 2.0 Client ID
4. Add your Render.com domain to the "Authorized JavaScript origins":
   ```
   https://your-app-name.onrender.com
   ```
5. Add your callback URL to "Authorized redirect URIs":
   ```
   https://your-app-name.onrender.com/auth/google/callback
   ```

## Step 5: Deploy Your Application

1. Click "Create Web Service" on Render
2. Wait for the build and deployment process to complete
3. Once deployed, your app will be available at `https://your-app-name.onrender.com`

## Step 6: Verify Authentication Works

1. Visit your deployed application
2. Test the login functionality
3. Create and manage game lists to verify Firebase database connections

## Troubleshooting

If you encounter issues:

1. Check the Render logs for errors
2. Verify all environment variables are set correctly
3. Ensure Firebase security rules allow the necessary operations
4. Check that your Google OAuth configuration is correct and the callback URL is authorized

## Production Considerations

For a production deployment:

1. Set up auto-scaling based on your expected traffic
2. Configure a custom domain if desired
3. Set up monitoring and alerts
4. Consider upgrading to a paid plan for better performance
5. Implement proper Firebase security rules for production use 