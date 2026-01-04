// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// Get form elements
const adminLoginForm = document.getElementById('adminLoginForm');
const adminLoginButton = document.getElementById('adminLoginButton');
const errorMessage = document.getElementById('errorMessage');

// Request OTP
async function requestOTP() {
    const email = document.getElementById('email').value.trim();
    
    if (!email) {
        showError('Please enter your email address');
        return;
    }

    const otpButton = document.getElementById('getOtpButton');
    if (!otpButton) {
        console.error('OTP button not found');
        return;
    }

    otpButton.disabled = true;
    otpButton.textContent = 'Sending...';

    try {
        const response = await fetch(`${API_BASE_URL}/otp/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                identifier: email
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Show success message
            const errorMsg = document.getElementById('errorMessage');
            const originalBg = errorMsg.style.backgroundColor;
            errorMsg.textContent = '✓ OTP sent to your email!';
            errorMsg.style.backgroundColor = '#10B981';
            errorMsg.classList.add('show');
            setTimeout(() => {
                errorMsg.classList.remove('show');
                errorMsg.style.backgroundColor = originalBg;
            }, 5000);
            
            let countdown = 30;
            otpButton.textContent = `Resend OTP (${countdown}s)`;
            
            const timer = setInterval(() => {
                countdown--;
                if (countdown <= 0) {
                    clearInterval(timer);
                    otpButton.disabled = false;
                    otpButton.textContent = 'Get OTP';
                } else {
                    otpButton.textContent = `Resend OTP (${countdown}s)`;
                }
            }, 1000);
        } else {
            showError(data.detail || 'Failed to send OTP');
            otpButton.disabled = false;
            otpButton.textContent = 'Get OTP';
        }
    } catch (error) {
        console.error('OTP error:', error);
        showError('Connection error. Please try again.');
        otpButton.disabled = false;
        otpButton.textContent = 'Get OTP';
    }
}

// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.parentElement.querySelector('.toggle-password');
    
    if (input.type === 'password') {
        input.type = 'text';
        button.innerHTML = `
            <svg class="eye-closed" width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M3 3L17 17M10 7C8.34315 7 7 8.34315 7 10C7 11.6569 8.34315 13 10 13" stroke="currentColor" stroke-width="1.5"/>
                <path d="M10 3C5 3 1.73 7.11 1 10C1.73 12.89 5 17 10 17C15 17 18.27 12.89 19 10" stroke="currentColor" stroke-width="1.5"/>
            </svg>
        `;
    } else {
        input.type = 'password';
        button.innerHTML = `
            <svg class="eye-open" width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 7C8.34315 7 7 8.34315 7 10C7 11.6569 8.34315 13 10 13C11.6569 13 13 11.6569 13 10C13 8.34315 11.6569 7 10 7Z" stroke="currentColor" stroke-width="1.5"/>
                <path d="M10 3C5 3 1.73 7.11 1 10C1.73 12.89 5 17 10 17C15 17 18.27 12.89 19 10C18.27 7.11 15 3 10 3Z" stroke="currentColor" stroke-width="1.5"/>
            </svg>
        `;
    }
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    setTimeout(() => {
        errorMessage.classList.remove('show');
    }, 5000);
}

// Hide error message
function hideError() {
    errorMessage.classList.remove('show');
}

// Handle form submission
adminLoginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    // Get form data
    const email = document.getElementById('email').value.trim();
    const otp = document.getElementById('otp').value.trim();
    const password = document.getElementById('password').value;

    // Validate inputs
    if (!email || !otp || !password) {
        showError('Please fill in all fields');
        return;
    }

    // Validate OTP format (6 digits)
    if (!/^\d{6}$/.test(otp)) {
        showError('OTP must be exactly 6 digits');
        return;
    }

    // Disable button and show loading state
    adminLoginButton.disabled = true;
    adminLoginButton.classList.add('loading');
    adminLoginButton.querySelector('span').textContent = 'Verifying...';

    try {
        // Call admin login API
        const response = await fetch(`${API_BASE_URL}/auth/admin/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                otp: otp,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Admin login successful
            console.log('Admin login successful:', data);
            
            // SECURITY: Clear any student session to prevent conflicts
            localStorage.removeItem('student');
            
            // Store admin session in localStorage
            // Backend returns { message: "...", admin: { admin_id, name, email, role, access_token, token_type } }
            const adminData = data.admin || data;
            localStorage.setItem('admin', JSON.stringify({
                admin_id: adminData.admin_id,
                name: adminData.name,
                email: adminData.email,
                role: 'admin',
                access_token: adminData.access_token,
                token_type: adminData.token_type || 'bearer',
                access_granted: true,
                login_time: new Date().toISOString()
            }));

            // Show success and redirect
            adminLoginButton.querySelector('span').textContent = 'Access Granted!';
            
            setTimeout(() => {
                // Redirect to admin dashboard
                window.location.href = 'dashboard.html';
            }, 1000);
        } else {
            // Login failed
            showError(data.detail || 'Invalid admin password');
            
            // Reset button
            adminLoginButton.disabled = false;
            adminLoginButton.classList.remove('loading');
            adminLoginButton.querySelector('span').textContent = 'Access Admin Panel';
        }
    } catch (error) {
        console.error('Admin login error:', error);
        showError('Connection error. Please check if the server is running.');
        
        // Reset button
        adminLoginButton.disabled = false;
        adminLoginButton.classList.remove('loading');
        adminLoginButton.querySelector('span').textContent = 'Access Admin Panel';
    }
});

// Auto-focus on email input
document.getElementById('email').focus();

// Add shake animation on error
function shakeCard() {
    const card = document.querySelector('.auth-card');
    card.style.animation = 'shake 0.5s';
    setTimeout(() => {
        card.style.animation = '';
    }, 500);
}

// Add shake keyframes dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }
`;
document.head.appendChild(style);

// Shake on wrong password
adminLoginForm.addEventListener('submit', (e) => {
    setTimeout(() => {
        if (errorMessage.classList.contains('show')) {
            shakeCard();
        }
    }, 100);
});

console.log('🔐 Admin Login Page Ready');
console.log('📡 API Base URL:', API_BASE_URL);
console.log('ℹ️ Default Password: Admin@123');
