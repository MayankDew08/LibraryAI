// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// Get form elements
const registerForm = document.getElementById('registerForm');
const registerButton = document.getElementById('registerButton');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');

// Request OTP
async function requestOTP() {
    const email = document.getElementById('email').value.trim();
    
    if (!email) {
        showError('Please enter your email first');
        return;
    }
    
    const otpButton = document.getElementById('getOtpButton');
    otpButton.disabled = true;
    otpButton.textContent = 'Sending...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/otp/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ identifier: email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('OTP sent to your email! Check your inbox.');
            otpButton.textContent = 'Resend OTP';
            // Re-enable after 30 seconds
            setTimeout(() => {
                otpButton.disabled = false;
            }, 30000);
        } else {
            showError(data.detail || 'Failed to send OTP');
            otpButton.disabled = false;
            otpButton.textContent = 'Get OTP';
        }
    } catch (error) {
        showError('Network error. Please check your connection.');
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
    successMessage.classList.remove('show');
    setTimeout(() => {
        errorMessage.classList.remove('show');
    }, 5000);
}

// Show success message
function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.classList.add('show');
    errorMessage.classList.remove('show');
}

// Hide messages
function hideMessages() {
    errorMessage.classList.remove('show');
    successMessage.classList.remove('show');
}

// Validate password strength
function validatePassword(password) {
    if (password.length < 8) {
        return 'Password must be at least 8 characters long';
    }
    if (password.length > 20) {
        return 'Password must be at most 20 characters long';
    }
    return null;
}

// Handle form submission
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessages();

    // Get form data
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const otp = document.getElementById('otp').value.trim();
    const termsAccepted = document.getElementById('terms').checked;

    // Validate inputs
    if (!name || !email || !password || !confirmPassword || !otp) {
        showError('Please fill in all fields');
        return;
    }

    if (!termsAccepted) {
        showError('Please accept the Terms & Conditions');
        return;
    }

    // Validate OTP
    if (otp.length !== 6 || !/^\d{6}$/.test(otp)) {
        showError('OTP must be exactly 6 digits');
        return;
    }

    // Validate password
    const passwordError = validatePassword(password);
    if (passwordError) {
        showError(passwordError);
        return;
    }

    // Check if passwords match
    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    // Disable button and show loading state
    registerButton.disabled = true;
    registerButton.classList.add('loading');
    registerButton.querySelector('span').textContent = 'Creating account...';

    try {
        // Call register API
        const response = await fetch(`${API_BASE_URL}/auth/student/register`, {
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
            console.log('Registration successful:', data);
            
            showSuccess('Account created successfully! Redirecting to login...');
            registerButton.querySelector('span').textContent = 'Success!';
            
            // Redirect to login page after 2 seconds
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            // Registration failed
            showError(data.detail || 'Registration failed. Please try again.');
            
            // Reset button
            registerButton.disabled = false;
            registerButton.classList.remove('loading');
            registerButton.querySelector('span').textContent = 'Create Account';
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('Connection error. Please check if the server is running.');
        
        // Reset button
        registerButton.disabled = false;
        registerButton.classList.remove('loading');
        registerButton.querySelector('span').textContent = 'Create Account';
    }
});

// Real-time password validation
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');

passwordInput.addEventListener('input', () => {
    const error = validatePassword(passwordInput.value);
    const hint = passwordInput.parentElement.nextElementSibling;
    
    if (error && passwordInput.value.length > 0) {
        hint.style.color = '#EF4444';
        hint.textContent = error;
    } else {
        hint.style.color = '#94A3B8';
        hint.textContent = 'Password must be 8-20 characters';
    }
});

confirmPasswordInput.addEventListener('input', () => {
    if (confirmPasswordInput.value && passwordInput.value !== confirmPasswordInput.value) {
        confirmPasswordInput.style.borderColor = '#EF4444';
    } else {
        confirmPasswordInput.style.borderColor = 'rgba(255, 255, 255, 0.1)';
    }
});

// Auto-focus on name input
document.getElementById('name').focus();

console.log('📝 Student Registration Page Ready');
console.log('📡 API Base URL:', API_BASE_URL);
