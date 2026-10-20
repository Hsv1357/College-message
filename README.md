# CampusConnect — College Web Application (Phase 1)

CampusConnect is a modular, secure, full-stack college web application built with **Python**, **Flask**, **Firebase Authentication**, and **Google Cloud Firestore**.

Phase 1 establishes the core identity, role-based authorization, and user management foundations for students, staff, parents, and college administrators.

---

## 1. Features Implemented in Phase 1

- **Custom User ID Authentication**: Log in using human-friendly college identifiers (e.g., `Admin-2004`, `STU-1001`, `STF-201`, `PAR-301`) backed by Firebase Authentication without exposing internal emails.
- **Role-Based Access Control (RBAC)**: Backend verification for four distinct roles:
  - `admin`: Full administrative access to management directories and account provisioning.
  - `student`: Access to personal profile overview.
  - `staff`: Access to faculty profile overview.
  - `parent`: Access to verified parent-student relationships and profile.
- **Administrator Dashboard**: Real-time metrics calculated from Firestore:
  - Total Students, Total Staff, Total Parents
  - Operational active accounts vs. deactivated accounts
  - Zero-data graceful empty states
- **Student Account Management**:
  - Search by User ID or Name
  - Filter by Department and Account Status
  - In-place profile modal editing
  - Account deactivation/activation with token revocation
- **Staff Account Management**:
  - Directory search and department filtering
  - Faculty profile updates and status controls
- **Parent Account Management**:
  - Directory search and status controls
  - Management of verified linked student User IDs
- **Account Provisioning**:
  - Admin-only account creation form with dynamic role-specific fields
  - Automatic collision-safe mapping and atomic compensation rollback if database writes fail
- **Default Administrator Provisioning**:
  - Secure, idempotent initialization script (`scripts/initialize_admin.py`)
  - User ID: `Admin-2004`, Role: `admin`
- **Application Security**:
  - Server-side authorization decorators (`@login_required`, `@role_required`)
  - CSRF protection across state-changing requests (`Flask-WTF`)
  - HttpOnly and SameSite cookie configurations
  - Passwords never stored as plaintext in Firestore
  - Security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`)
- **Automated Test Suite**:
  - 22 comprehensive automated tests covering authentication, route authorization, account creation, data filtering, and edge cases.

---

## 2. Technology Stack & Prerequisites

- **Python**: 3.12+ (tested on Python 3.12.10)
- **Web Framework**: Flask 3.1+
- **Database & Identity**: Firebase Admin SDK (`firebase-admin`), Google Cloud Firestore, Firebase Authentication
- **Security**: Flask-WTF (CSRF), Requests
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons
- **Testing**: Pytest

---

## 3. Windows PowerShell Setup & Installation

### Step 3.1: Navigate to Workspace and Create Virtual Environment

Open Windows PowerShell in the project directory:

```powershell
# Verify Python version
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

> **Note on PowerShell Execution Policy**: If you receive an execution policy error when activating the virtual environment, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\venv\Scripts\Activate.ps1
> ```

### Step 3.2: Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Firebase Configuration

The application is pre-configured for Firebase project: **`message-app-80729`**.

### Step 4.1: Enable Firebase Authentication

1. Open the [Firebase Console](https://console.firebase.google.com/).
2. Select your project: **`message-app-80729`**.
3. In the left sidebar, navigate to **Build** &rarr; **Authentication**.
4. Click **Get Started** (if not already enabled).
5. Under the **Sign-in method** tab, click **Email/Password**.
6. Toggle **Enable** for Email/Password and click **Save**.

### Step 4.2: Create Cloud Firestore Database

1. In the Firebase Console sidebar, navigate to **Build** &rarr; **Firestore Database**.
2. Click **Create database**.
3. Choose a location closest to your users.
4. Select **Start in production mode** (or test mode for immediate testing).
5. Click **Create**.

### Step 4.3: Deploy Firestore Security Rules

1. In Firestore Database, open the **Rules** tab.
2. Copy the contents of [`firestore.rules`](file:///d:/3-1/message-app/firestore.rules) into the editor:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       function isAuthenticated() { return request.auth != null; }
       function isOwner(userId) { return isAuthenticated() && request.auth.uid == userId; }
       function isAdmin() {
         return isAuthenticated() && (
           request.auth.token.role == 'admin' ||
           get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin'
         );
       }
       match /users/{userId} {
         allow read: if isOwner(userId) || isAdmin();
         allow write: if isAdmin();
       }
       match /user_id_mappings/{mappingId} {
         allow read: if isAdmin();
         allow write: if isAdmin();
       }
       match /{document=**} {
         allow read, write: if false;
       }
     }
   }
   ```
3. Click **Publish**.

### Step 4.4: Obtain Firebase Admin Service Account Key

To enable server-side account provisioning and database management:

1. In the Firebase Console, click the gear icon &rarr; **Project settings**.
2. Navigate to the **Service accounts** tab.
3. Click **Generate new private key** and confirm.
4. Rename the downloaded `.json` file to **`service_account.json`**.
5. Move `service_account.json` into the root directory of this project (`d:\3-1\message-app\service_account.json`).
6. Ensure your `.env` contains:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=service_account.json
   ```

> [!CAUTION]
> Never commit `service_account.json` to GitHub or version control. It is already included in `.gitignore`.

---

## 5. Provision the Default Administrator Account

CampusConnect provides an idempotent provisioning script:

```powershell
python scripts/initialize_admin.py
```

### Credentials Configured:
- **User ID**: `Admin-2004`
- **Initial Password**: `admin@Test123`
- **Role**: `admin`

### Idempotency & Safety:
- The script checks if `Admin-2004` already exists.
- If it already exists, it verifies its state without making destructive changes or overwriting custom passwords.
- If Firebase credentials are missing, it outputs clear instructions without crashing or creating false records.

### Changing the Initial Password:
After initial login, the administrator's password can be updated directly via Firebase Console (Authentication &rarr; Users &rarr; Search User &rarr; Reset Password) or through administrative tools.

---

## 6. Running the Web Application

Run the application development server on Windows:

```powershell
python run.py
```

The portal will be accessible at:
- **Login URL**: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
- **Admin Dashboard**: [http://127.0.0.1:5000/admin/dashboard](http://127.0.0.1:5000/admin/dashboard)

---

## 7. Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
python -m pytest -v
```

### Test Coverage Highlights:
1. `tests/test_auth.py`:
   - Login page rendering and field presence.
   - Missing User ID and password validation.
   - Invalid credentials rejection with uniform messages (anti-enumeration).
   - Admin session creation and dashboard redirection.
   - Student session creation and role dashboard redirection.
   - Deactivated account login prevention.
   - Session termination upon logout.
2. `tests/test_admin.py`:
   - Route protection against unauthenticated visitors.
   - Route protection against non-admin users (students, staff, parents).
   - Admin access to all management directories.
   - Account deactivation and activation status toggling.
   - Profile updating for users.
3. `tests/test_account_creation.py`:
   - Student, staff, and parent provisioning workflows.
   - Rejection of duplicate User IDs.
4. `tests/test_services.py`:
   - Deterministic User ID normalization and internal auth email generator.
   - Role-based user query filtering.
   - Firestore metric calculation.
   - Input validation rules (length, role validity, required fields).

---

## 8. Authentication Architecture & Mapping Strategy

Firebase Authentication natively requires an email address when authenticating with passwords. To support arbitrary custom User IDs:

1. **Deterministic Mapping**:
   When an account is created with User ID `STU-1001`, the system creates:
   - Auth Email: `stu-1001@auth.campusconnect.internal`
   - Mapping Document: `user_id_mappings/stu-1001` storing `uid`, `user_id`, and `role`.
   - User Profile: `users/{uid}` storing full profile metadata and `account_status`.
2. **Login Verification**:
   - The user inputs `user_id` and `password`.
   - The server queries `user_id_mappings/{normalized_id}`.
   - If found, it authenticates with Firebase Auth via the Identity Toolkit API.
   - Upon successful password check, the server loads the trusted Firestore profile and validates `account_status == 'active'`.
   - Session cookie is set with HttpOnly, SameSite, and server-side role data.
3. **Account Deactivation**:
   - Deactivating a user updates `account_status = 'disabled'` in Firestore.
   - Concurrently updates Firebase Auth user `disabled = True`.
   - Calls `auth.revoke_refresh_tokens(uid)` to immediately invalidate active tokens.

---

## 9. Common Errors & Troubleshooting

| Error | Root Cause | Solution |
| :--- | :--- | :--- |
| `Firebase service account file not found at 'service_account.json'` | Service account key is missing or filepath in `.env` is incorrect. | Download your private key from Firebase Console &rarr; Project Settings &rarr; Service accounts and save it as `service_account.json` in the project root. |
| `Firebase Auth rejected login: OPERATION_NOT_ALLOWED` | Email/Password provider not enabled in Firebase Console. | Go to Firebase Console &rarr; Authentication &rarr; Sign-in method &rarr; Enable Email/Password. |
| `User ID is already registered` | Attempted to create an account with a duplicate User ID. | User IDs must be unique across the campus portal. Provide a distinct User ID. |
| `Your security token has expired` | CSRF token mismatch or session timeout. | Reload the page and submit the form again. |
| `Unauthorized access` | Non-admin user attempted to access an admin URL. | The backend RBAC strictly guards all administrative routes. Log in with an admin account. |

---

## 10. Future Extensibility Roadmap (Future Phases)

CampusConnect Phase 1 is designed with a clean modular blueprint architecture to support the upcoming phases:

- **Phase 2: Real-Time Messaging & Channels**
  - Direct 1-to-1 chats between faculty, students, and parents.
  - Departmental group channels and class groups.
- **Phase 3: Campus Announcements & File Sharing**
  - Broadcast notices and circulars.
  - Secure Cloud Storage integration for assignments and documents.
- **Phase 4: Notifications & Presence**
  - Real-time online/offline presence indicators.
  - Web push notifications.
- **Phase 5: DevOps & Containerization**
  - Docker containerization and Kubernetes orchestration.
  - GitHub Actions CI/CD pipelines.
# College-message
