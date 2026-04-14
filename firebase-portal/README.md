# 🔐 Galt Security - Distribution Portal

A secure, Firebase-hosted web portal for distributing the Galt security software to alpha testers.

## 🎯 Features

- **🔒 Firebase Authentication** - Email/Password login
- **📦 Secure Downloads** - Protected access to Galt releases via Firebase Storage
- **📊 Analytics** - Download tracking with Firestore
- **🎨 Modern UI** - Dark mode design with Tailwind CSS
- **📱 Responsive** - Works on desktop and mobile
- **⚡ Fast** - Static hosting with CDN delivery

## 🏗️ Architecture

```
firebase-portal/
├── public/
│   ├── index.html              # Login page
│   ├── dashboard.html          # Protected download page
│   ├── css/
│   │   └── styles.css          # Custom styles
│   └── js/
│       ├── config.js           # Firebase configuration
│       ├── auth.js             # Authentication logic
│       └── dashboard.js        # Download & analytics
├── firebase.json               # Firebase hosting config
├── firestore.rules             # Database security rules
├── storage.rules               # Storage security rules
├── DEPLOYMENT.md               # Deployment guide
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Node.js 14+
- Firebase CLI: `npm install -g firebase-tools`
- Firebase account (free tier works)

### 2. Configure

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Authentication (Email/Password), Firestore, and Storage
3. Copy your Firebase config to `public/js/config.js`
4. Upload your Galt release to Storage at `releases/galt_latest.zip`

### 3. Deploy

```bash
# Login to Firebase
firebase login

# Initialize project
firebase init

# Deploy
firebase deploy
```

**📘 See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step instructions.**

## 🔧 Tech Stack

- **Frontend:** HTML5, Tailwind CSS (CDN), Vanilla JavaScript (ES6+)
- **Backend:** Firebase (Hosting, Auth, Firestore, Storage)
- **SDK:** Firebase v9 Modular SDK
- **Styling:** Tailwind CSS + Custom CSS
- **Icons:** Heroicons (SVG)

## 🎨 Design

- **Theme:** Dark mode with Slate/Blue/Gold palette
- **Style:** Modern, premium, glassmorphism effects
- **Typography:** System fonts with clean hierarchy
- **Animations:** Smooth transitions and micro-interactions

## 📋 User Flow

1. User opens portal → Login page (`index.html`)
2. Enter email/password → Firebase Auth validates
3. Redirect to dashboard (`dashboard.html`)
4. Click download button → Firebase Storage serves `galt_latest.zip`
5. Download event logged to Firestore `downloads` collection

## 🔐 Security

- **Authentication required** for all downloads
- **Firestore rules** enforce authenticated access
- **Storage rules** restrict downloads to authenticated users only
- **No public signup** - Admin creates users via Firebase Console
- **Security rules deployed** server-side (cannot be bypassed)

## 📊 Analytics

All downloads are logged to Firestore with:
- User ID & Email
- Timestamp
- File name
- Download URL
- User Agent & Platform

View in Firebase Console → Firestore → `downloads` collection.

## 🛠️ Customization

### Update Galt Version

1. Upload new file to Storage: `releases/galt_latest.zip`
2. Update version text in `dashboard.html` (search for "v0.1")

### Change Branding

- **Colors:** Edit Tailwind config in HTML `<script>` tags
- **Logo:** Replace SVG icons in HTML files
- **Text:** Update Spanish text directly in HTML

### Add Features

- **Email Verification:** Use Firebase Auth email verification
- **Password Reset:** Add password reset flow
- **Admin Panel:** Create Cloud Functions for user management
- **Version History:** Expand Storage to multiple releases

## 📦 File Upload Instructions

To add the Galt software:

1. Firebase Console → Storage
2. Create folder: `releases/`
3. Upload file: `galt_latest.zip` (your packaged Galt software)
4. Verify path: `releases/galt_latest.zip`

## 👥 User Management

### Add User (Alpha Tester)

1. Firebase Console → Authentication → Users
2. Click "Add user"
3. Enter email and password
4. Send credentials securely to user

### Remove User

1. Firebase Console → Authentication → Users
2. Select user → Delete

## 🐛 Troubleshooting

**Login fails:**
- Check Email/Password provider is enabled
- Verify user exists in Authentication
- Check browser console for errors

**Download button error:**
- Verify file exists at `releases/galt_latest.zip` in Storage
- Check Storage rules allow authenticated read
- Confirm user is logged in

**Config errors:**
- Ensure `public/js/config.js` has correct Firebase credentials
- Verify project ID matches your Firebase project

## 📈 Scaling

Current limits (Free Tier):
- **Hosting:** 10 GB storage, 360 MB/day bandwidth
- **Firestore:** 1 GB storage, 50K reads/day
- **Storage:** 5 GB storage, 1 GB/day bandwidth
- **Authentication:** Unlimited users

For production, upgrade to **Blaze Plan** (pay-as-you-go).

## 🔄 Updates

To update portal code:

```bash
# Make changes to files in public/
# Then redeploy
firebase deploy --only hosting
```

To update security rules:

```bash
# Edit firestore.rules or storage.rules
# Then deploy
firebase deploy --only firestore:rules,storage:rules
```

## 📝 License

Internal use only - Galt Security Alpha Program

## 🤝 Support

For technical issues during Alpha:
- Check DEPLOYMENT.md for solutions
- Contact the project administrator
- Report bugs to dev team

---

**Built with ❤️ for Galt Security Alpha Testers**
