# Registration with OTP Verification

## Overview
The registration system now requires OTP verification for both students and admins. Additionally, admin registration requires a special admin password (`Admin@123`).

## Registration Flow

### Student Registration

1. **Request OTP**
   ```bash
   POST /otp/generate
   {
     "identifier": "student@example.com"
   }
   ```
   Response:
   ```json
   {
     "message": "OTP generated successfully",
     "identifier": "student@example.com",
     "otp": "123456",  // Only in dev mode - will be sent via email/SMS in production
     "expires_in_seconds": 300
   }
   ```

2. **Register with OTP**
   ```bash
   POST /auth/student/register
   {
     "name": "John Doe",
     "email": "student@example.com",
     "password": "mypassword123",
     "role": "student",
     "otp": "123456"
   }
   ```
   Response:
   ```json
   {
     "message": "User registered successfully",
     "user": {
       "id": 1,
       "name": "John Doe",
       "email": "student@example.com",
       "role": "student"
     }
   }
   ```

### Admin Registration

1. **Request OTP**
   ```bash
   POST /otp/generate
   {
     "identifier": "admin@example.com"
   }
   ```

2. **Register with OTP and Admin Password**
   ```bash
   POST /auth/admin/register
   {
     "name": "Admin User",
     "email": "admin@example.com",
     "password": "Admin@123",  // Must be exactly "Admin@123"
     "otp": "123456"
   }
   ```
   Response:
   ```json
   {
     "message": "Admin registered successfully",
     "admin": {
       "id": 1,
       "name": "Admin User",
       "email": "admin@example.com"
     }
   }
   ```

## Validation Rules

### Student Registration
- **name**: Required, string
- **email**: Required, valid email format
- **password**: Required, 8-20 characters
- **role**: Required, must be "student" or "admin"
- **otp**: Required, exactly 6 digits

### Admin Registration
- **name**: Required, string
- **email**: Required, valid email format
- **password**: Required, must be exactly `Admin@123`
- **otp**: Required, exactly 6 digits

## OTP Rules
- **Length**: Exactly 6 digits
- **Expiry**: 5 minutes after generation
- **Max Attempts**: 3 incorrect attempts before OTP becomes invalid
- **Format**: Numeric only (0-9)

## Error Responses

### Invalid OTP
```json
{
  "detail": "Invalid OTP"
}
```

### Expired OTP
```json
{
  "detail": "OTP has expired"
}
```

### Wrong Admin Password
```json
{
  "detail": "Invalid admin password"
}
```

### Email Already Registered
```json
{
  "detail": "Email already registered"
}
```

### Too Many OTP Attempts
```json
{
  "detail": "Too many incorrect attempts. OTP invalidated."
}
```

## Frontend Integration Example

### Student Registration Form
```html
<form id="studentRegisterForm">
  <input type="text" id="name" placeholder="Full Name" required>
  <input type="email" id="email" placeholder="Email" required>
  <input type="password" id="password" placeholder="Password (8-20 chars)" required>
  <input type="text" id="otp" placeholder="OTP (6 digits)" maxlength="6" required>
  <button type="button" onclick="requestOTP()">Get OTP</button>
  <button type="submit">Register</button>
</form>

<script>
async function requestOTP() {
  const email = document.getElementById('email').value;
  const response = await fetch('/otp/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({identifier: email})
  });
  const data = await response.json();
  alert('OTP sent! (Check console for dev OTP)');
  console.log('OTP:', data.otp); // Only in dev mode
}

async function registerStudent(event) {
  event.preventDefault();
  const formData = {
    name: document.getElementById('name').value,
    email: document.getElementById('email').value,
    password: document.getElementById('password').value,
    role: 'student',
    otp: document.getElementById('otp').value
  };
  
  const response = await fetch('/auth/student/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(formData)
  });
  
  if (response.ok) {
    alert('Registration successful!');
    window.location.href = '/login.html';
  } else {
    const error = await response.json();
    alert('Error: ' + error.detail);
  }
}

document.getElementById('studentRegisterForm').addEventListener('submit', registerStudent);
</script>
```

### Admin Registration Form
```html
<form id="adminRegisterForm">
  <input type="text" id="name" placeholder="Full Name" required>
  <input type="email" id="email" placeholder="Email" required>
  <input type="password" id="password" value="Admin@123" readonly>
  <small>Admin password is fixed: Admin@123</small>
  <input type="text" id="otp" placeholder="OTP (6 digits)" maxlength="6" required>
  <button type="button" onclick="requestAdminOTP()">Get OTP</button>
  <button type="submit">Register Admin</button>
</form>

<script>
async function requestAdminOTP() {
  const email = document.getElementById('email').value;
  const response = await fetch('/otp/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({identifier: email})
  });
  const data = await response.json();
  alert('OTP sent! (Check console for dev OTP)');
  console.log('OTP:', data.otp);
}

async function registerAdmin(event) {
  event.preventDefault();
  const formData = {
    name: document.getElementById('name').value,
    email: document.getElementById('email').value,
    password: 'Admin@123', // Fixed admin password
    otp: document.getElementById('otp').value
  };
  
  const response = await fetch('/auth/admin/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(formData)
  });
  
  if (response.ok) {
    alert('Admin registration successful!');
    window.location.href = '/admin-login.html';
  } else {
    const error = await response.json();
    alert('Error: ' + error.detail);
  }
}

document.getElementById('adminRegisterForm').addEventListener('submit', registerAdmin);
</script>
```

## Security Considerations

### Development vs Production
- **Development**: OTP is returned in the response for testing
- **Production**: OTP should be sent via email/SMS (integrate Twilio/SendGrid)

### Admin Password
- The fixed admin password `Admin@123` is a simple mechanism for this version
- Consider implementing role-based permissions or invitation-based admin creation for production

## Testing Checklist

- [ ] Student can request OTP successfully
- [ ] Student registration succeeds with valid OTP
- [ ] Student registration fails with invalid OTP
- [ ] Student registration fails with expired OTP (wait 5+ minutes)
- [ ] Student registration fails with wrong OTP (3 times)
- [ ] Admin can request OTP successfully
- [ ] Admin registration succeeds with "Admin@123" and valid OTP
- [ ] Admin registration fails with wrong password (not "Admin@123")
- [ ] Admin registration fails with invalid OTP
- [ ] Cannot register with already used email
- [ ] OTP expires after 5 minutes
- [ ] OTP becomes invalid after 3 wrong attempts

## Migration from Old System

### Breaking Changes
1. **Old registration endpoint** (`POST /auth/register`) still exists but now requires OTP field
2. **Admin registration** now requires fixed password "Admin@123"
3. **All registrations** require OTP verification

### Backward Compatibility
- If you have existing registration forms, add:
  - OTP input field
  - "Get OTP" button
  - OTP request logic
