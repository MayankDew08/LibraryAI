// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// Get form elements
const registerForm = document.getElementById('adminRegisterForm');
const registerButton = document.getElementById('registerButton');
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
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    // Get form data
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const otp = document.getElementById('otp').value.trim();
    const password = document.getElementById('password').value; // Always "Admin@123"

    // Validate inputs
    if (!name || !email || !otp || !password) {
        showError('Please fill in all fields');
        return;
    }

    // Validate name
    if (name.length < 2) {
        showError('Name must be at least 2 characters long');
        return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('Please enter a valid email address');
        return;
    }

    // Validate OTP format (6 digits)
    if (!/^\d{6}$/.test(otp)) {
        showError('OTP must be exactly 6 digits');
        return;
    }

    // Verify password is Admin@123
    if (password !== 'Admin@123') {
        showError('Admin password must be Admin@123');
        return;
    }

    // Disable button and show loading state
    registerButton.disabled = true;
    registerButton.classList.add('loading');
    registerButton.querySelector('span').textContent = 'Creating Account...';

    try {
        // Call admin registration API
        const response = await fetch(`${API_BASE_URL}/auth/admin/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                email: email,
                password: password,
                otp: otp
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Registration successful
            console.log('Admin registration successful:', data);
            
            // Show success message
            registerButton.querySelector('span').textContent = 'Account Created!';
            
            // Clear form
            registerForm.reset();
            
            // Show success notification
            showError = function(msg) {
                errorMessage.textContent = msg;
                errorMessage.style.backgroundColor = '#4CAF50';
                errorMessage.classList.add('show');
            };
            showError('Admin account created successfully! Redirecting to login...');
            
            // Redirect to login page
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            // Registration failed
            showError(data.detail || 'Registration failed. Please try again.');
            
            // Reset button
            registerButton.disabled = false;
            registerButton.classList.remove('loading');
            registerButton.querySelector('span').textContent = 'Create Admin Account';
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('Connection error. Please check if the server is running.');
        
        // Reset button
        registerButton.disabled = false;
        registerButton.classList.remove('loading');
        registerButton.querySelector('span').textContent = 'Create Admin Account';
    }
});

// Auto-focus on name input
document.getElementById('name').focus();

console.log('🔐 Admin Registration Page Ready');
console.log('📡 API Base URL:', API_BASE_URL);
console.log('ℹ️ Default Admin Password: Admin@123');
