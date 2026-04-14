# 🚀 Firebase Portal - Deployment Guide

Complete step-by-step guide to deploy the Galt Distribution Portal to Firebase Hosting.

## Prerequisites

- [ ] Node.js 14+ installed
- [ ] Firebase CLI installed (`npm install -g firebase-tools`)
- [ ] Firebase account (free tier is sufficient)
- [ ] Galt software package ready to upload

---

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"**
3. Enter project name: `galt-portal` (or your choice)
4. Disable Google Analytics (optional for Alpha)
5. Click **"Create project"**

---

## Step 2: Enable Firebase Services

### 2.1 Enable Authentication

1. In Firebase Console, go to **Build** → **Authentication**
2. Click **"Get started"**
3. Go to **Sign-in method** tab
4. Enable **Email/Password** provider
5. Click **Save**

### 2.2 Enable Firestore Database

1. Go to **Build** → **Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in production mode"**
4. Select your preferred region (e.g., `us-central1`)
5. Click **Enable**

### 2.3 Enable Storage

1. Go to **Build** → **Storage**
2. Click **"Get started"**
3. Choose **"Start in production mode"**
4. Select the same region as Firestore
5. Click **Done**

---

## Step 3: Configure the Portal

### 3.1 Get Firebase Configuration

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Scroll to **"Your apps"** section
3. Click the **Web** icon (`</>`)
4. Register app with nickname: `Galt Portal`
5. **Copy** the `firebaseConfig` object

### 3.2 Update config.js

Open `public/js/config.js` and replace the placeholder values:

```javascript
export const firebaseConfig = {
  apiKey: "AIzaSy...",                    // Your API Key
  authDomain: "galt-portal.firebaseapp.com",
  projectId: "galt-portal",
  storageBucket: "galt-portal.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

---

## Step 4: Upload Galt Software to Storage

1. In Firebase Console, go to **Storage**
2. Click **"Upload file"** or **"Create folder"**
3. Create folder structure: `releases/`
4. Upload your Galt package as: `releases/galt_latest.zip`
5. Make sure the file is uploaded successfully

> **Note:** The download button is configured to look for `releases/galt_latest.zip`. If you use a different path, update `dashboard.js`.

---

## Step 5: Deploy Security Rules

### 5.1 Initialize Firebase Project

Open terminal in the `firebase-portal` directory:

```powershell
# Login to Firebase
firebase login

# Initialize Firebase project
firebase init
```

When prompted:
- **Which Firebase features?** Select:
  - ✅ Firestore
  - ✅ Hosting  - ✅ Storage
- **Use existing project?** Yes, select `galt-portal`
- **Firestore rules file?** `firestore.rules` (default)
- **Firestore indexes file?** `firestore.indexes.json` (default)
- **Public directory?** `public` (default)
- **Configure as SPA?** **No**
- **Set up automatic builds?** No
- **Storage rules file?** `storage.rules` (default)

### 5.2 Deploy Rules

```powershell
# Deploy Firestore and Storage rules
firebase deploy --only firestore:rules,storage:rules
```

---

## Step 6: Deploy Hosting

```powershell
# Deploy the web portal
firebase deploy --only hosting
```

You'll receive a hosting URL like:
```
https://galt-portal.web.app
```

---

## Step 7: Create Admin User

Since we're not using Cloud Functions, create users manually via Firebase Console:

1. Go to **Authentication** → **Users**
2. Click **"Add user"**
3. Enter:
   - **Email:** `admin@example.com` (your admin email)
   - **Password:** Create a strong password
4. Click **"Add user"**
5. **Copy the password** and share it securely with the user

> **Security Note:** For production, consider implementing email verification and password reset flows.

---

## Step 8: Test the Portal

1. Open your hosting URL: `https://galt-portal.web.app`
2. Login with the admin credentials
3. Verify you can access the dashboard
4. Click **"Descargar Galt v0.1"**
5. Confirm the download initiates

---

## Step 9: Create Additional Alpha Users

Repeat Step 7 for each alpha tester:

1. Create user in Firebase Console
2. Generate strong password
3. Send credentials securely (email, password manager, etc.)
4. Ask them to change password on first login (future feature)

---

## Ongoing Maintenance

### Update Galt Software

1. Go to **Storage** → `releases/`
2. Delete old `galt_latest.zip`
3. Upload new version with same name
4. No code changes needed!

### Monitor Downloads

1. Go to **Firestore Database**
2. Open `downloads` collection
3. View all download events with:
   - User email
   - Timestamp
   - Platform info

### Add/Remove Users

**Add:** Authentication → Users → Add user

**Remove:** Authentication → Users → Select user → Delete user

### View Logs

```powershell
firebase functions:log  # If you add Cloud Functions later
firebase hosting:channel:list  # View hosting channels
```

---

## Troubleshooting

### "Firebase not configured" error

**Solution:** Check that `public/js/config.js` has correct values from your Firebase project.

### Download button shows error

**Solution:** 
1. Verify file exists at `Storage` → `releases/galt_latest.zip`
2. Check Storage rules allow authenticated read
3. Check browser console for specific error

### Cannot login

**Solution:**
1. Verify Email/Password provider is enabled in Authentication
2. Check that user exists in Authentication → Users
3. Verify password is correct

### CORS errors

**Solution:** Storage and Firestore should work out-of-the-box. If issues persist:
1. Check Firebase security rules
2. Ensure using Firebase SDK v9 (modular)

---

## Security Best Practices

1. **Never commit `config.js` with real credentials to public repos**
   - Add `public/js/config.js` to `.gitignore`
   - Or use environment variables with build tools

2. **Firestore and Storage Rules are CRITICAL**
   - Only authenticated users can download
   - Only authenticated users can log downloads
   - Rules are enforced server-side

3. **User Management**
   - Use strong passwords (12+ characters)
   - Rotate credentials periodically
   - Delete users when they leave the Alpha program

4. **Monitor Usage**
   - Check Firestore quotas (50K reads/day on free tier)
   - Check Storage bandwidth (1GB/day on free tier)
   - Upgrade to Blaze plan if needed

---

## Next Steps (Post-Alpha)

- [ ] Implement email verification
- [ ] Add password reset flow
- [ ] Create admin panel with Cloud Functions for user management
- [ ] Add download analytics dashboard
- [ ] Implement version history (multiple releases)
- [ ] Set up custom domain
- [ ] Add beta/production environments

---

## Quick Reference Commands

```powershell
# Deploy everything
firebase deploy

# Deploy only hosting
firebase deploy --only hosting

# Deploy only rules
firebase deploy --only firestore:rules,storage:rules

# Open hosting in browser
firebase open hosting:site

# View project info
firebase projects:list
```

---

## Support

For Firebase-specific issues, consult:
- [Firebase Documentation](https://firebase.google.com/docs)
- [Firebase Console](https://console.firebase.google.com/)
- [StackOverflow - Firebase Tag](https://stackoverflow.com/questions/tagged/firebase)

---

**🎉 Your Galt Distribution Portal is now live!**
