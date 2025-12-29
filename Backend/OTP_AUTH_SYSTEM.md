# OTP-Based Authentication System

## Overview
Both **Admin** and **Student** login now require **OTP verification** for enhanced security.

---

## 🔐 Authentication Flow

### **For Students:**

#### Step 1: Request OTP
```bash
POST /otp/generate
{
  "identifier": "student@example.com"
}

Response:
{
  "otp": "123456",  # For development only
  "expires_in_minutes": 5
}
```

#### Step 2: Login with OTP
```bash
POST /auth/student/login
{
  "email": "student@example.com",
  "password": "yourpassword",
  "otp": "123456"
}

Response:
{
  "message": "Student login successful",
  "user": {
    "user_id": 1,
    "name": "John Doe",
    "email": "student@example.com",
    "role": "student"
  }
}
```

---

### **For Admins:**

#### Step 1: Register Admin (First Time)
```bash
POST /auth/admin/register
{
  "name": "Admin Name",
  "email": "admin@example.com",
  "password": "securepassword123"
}
```

#### Step 2: Request OTP
```bash
POST /otp/generate
{
  "identifier": "admin@example.com"
}

Response:
{
  "otp": "654321",  # For development only
  "expires_in_minutes": 5
}
```

#### Step 3: Login with OTP
```bash
POST /auth/admin/login
{
  "email": "admin@example.com",
  "password": "securepassword123",
  "otp": "654321"
}

Response:
{
  "message": "Admin login successful",
  "admin": {
    "admin_id": 1,
    "name": "Admin Name",
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

---

## 📋 Setup Instructions

### 1. Create Admins Table
```bash
conda activate audiolib
cd Backend
python create_admins_table.py
```

### 2. Register First Admin
Use API endpoint or create via database:
```bash
POST /auth/admin/register
{
  "name": "Super Admin",
  "email": "admin@library.com",
  "password": "Admin@12345"
}
```

### 3. Test OTP Flow
```bash
# 1. Get OTP
POST /otp/generate {"identifier": "admin@library.com"}

# 2. Login with OTP
POST /auth/admin/login {
  "email": "admin@library.com",
  "password": "Admin@12345",
  "otp": "<received_otp>"
}
```

---

## 🆕 New Endpoints

### Authentication
- `POST /auth/student/register` - Register student
- `POST /auth/student/login` - Student login (email + password + OTP)
- `POST /auth/admin/register` - Register admin
- `POST /auth/admin/login` - Admin login (email + password + OTP)

### OTP Management
- `POST /otp/generate` - Generate OTP
- `POST /otp/verify` - Verify OTP
- `POST /otp/resend` - Resend OTP
- `GET /otp/status/{identifier}` - Check OTP status

---

## 📊 Database Changes

### New Table: `admins`
```sql
- id (Primary Key)
- name
- email (Unique)
- hashed_password
- created_at
- updated_at
- is_active
```

### Existing Table: `users` (Students)
- No changes required
- Still used for student authentication

---

## 🔒 Security Features

✅ **OTP expires after 5 minutes**  
✅ **Max 3 verification attempts**  
✅ **Password hashing with bcrypt**  
✅ **Separate admin and student tables**  
✅ **Email validation**  
✅ **Active status check**

---

## 🎯 Frontend Integration

### Student Login Form
```javascript
// 1. User clicks "Get OTP" button
async function requestOTP() {
  const email = document.getElementById('email').value;
  const response = await fetch('/otp/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({identifier: email})
  });
  const data = await response.json();
  alert('OTP sent! (Dev: ' + data.otp + ')');
}

// 2. User submits login form
async function login() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const otp = document.getElementById('otp').value;
  
  const response = await fetch('/auth/student/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email, password, otp})
  });
  
  if (response.ok) {
    const data = await response.json();
    // Store user data and redirect
    localStorage.setItem('user', JSON.stringify(data.user));
    window.location.href = '/student/dashboard.html';
  }
}
```

### Admin Login Form
Same as student, just change endpoint to `/auth/admin/login`

---

## ⚠️ Breaking Changes

### Old Endpoints (DEPRECATED)
- ❌ `POST /auth/register` → Use `/auth/student/register`
- ❌ `POST /auth/login` → Use `/auth/student/login` (with OTP)
- ❌ `POST /auth/admin-login` → Use `/auth/admin/login` (with OTP)

### Migration Path
1. Update frontend to use new endpoints
2. Add OTP request flow before login
3. Add OTP input field to login forms

---

## 🧪 Testing Checklist

- [ ] Create admins table
- [ ] Register a test admin
- [ ] Request OTP for admin
- [ ] Login admin with OTP
- [ ] Register a test student
- [ ] Request OTP for student
- [ ] Login student with OTP
- [ ] Test OTP expiry (wait 5+ minutes)
- [ ] Test wrong OTP (3 attempts)
- [ ] Test OTP resend

---

## 🚀 Production Deployment

### Replace OTP Response with Email/SMS
In `app/routes/otp.py`, modify `/otp/generate`:

```python
# Instead of returning OTP in response:
return {
    "message": "OTP sent to your email",
    "identifier": request.identifier,
    # DON'T return: "otp": otp
}

# Add email/SMS sending:
send_email(request.identifier, otp)  ***REMOVED***
# or
send_sms(request.identifier, otp)    # Twilio
```

---

## 📞 Support

Common issues:
- **OTP expired**: Wait time exceeded 5 minutes → Request new OTP
- **Invalid OTP**: Wrong number entered → Check carefully, 3 attempts max
- **Email not found**: User/admin not registered → Register first
- **Wrong password**: Incorrect password → Reset or try again

---

**Status: ✅ READY FOR USE**

Both admin and student authentication now require OTP verification for enhanced security!
