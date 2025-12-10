// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000';

// Get form elements
const loginForm = document.getElementById('loginForm');
const loginButton = document.getElementById('loginButton');
const errorMessage = document.getElementById('errorMessage');

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
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    // Get form data
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // Validate inputs
    if (!email || !password) {
        showError('Please fill in all fields');
        return;
    }

    // Disable button and show loading state
    loginButton.disabled = true;
    loginButton.classList.add('loading');
    loginButton.querySelector('span').textContent = 'Signing in...';

    try {
        // Call login API
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Login successful
            console.log('Login successful:', data);
            
            // Store user data in localStorage for dashboard access
            localStorage.setItem('student', JSON.stringify({
                user_id: data.user_id,
                name: data.name,
                email: data.email,
                role: data.role
            }));

            // Show success and redirect
            loginButton.querySelector('span').textContent = 'Success! Redirecting...';
            
            setTimeout(() => {
                // Redirect to student dashboard
                window.location.href = 'dashboard.html';
            }, 1000);
        } else {
            // Login failed
            showError(data.detail || 'Invalid email or password');
            
            // Reset button
            loginButton.disabled = false;
            loginButton.classList.remove('loading');
            loginButton.querySelector('span').textContent = 'Sign In';
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Connection error. Please check if the server is running.');
        
        // Reset button
        loginButton.disabled = false;
        loginButton.classList.remove('loading');
        loginButton.querySelector('span').textContent = 'Sign In';
    }
});

// Remember me functionality
const rememberCheckbox = document.getElementById('remember');
const emailInput = document.getElementById('email');

// Load remembered email on page load
window.addEventListener('load', () => {
    const rememberedEmail = localStorage.getItem('rememberedEmail');
    if (rememberedEmail) {
        emailInput.value = rememberedEmail;
        rememberCheckbox.checked = true;
    }
});

// Save email when remember me is checked
rememberCheckbox.addEventListener('change', () => {
    if (rememberCheckbox.checked) {
        localStorage.setItem('rememberedEmail', emailInput.value);
    } else {
        localStorage.removeItem('rememberedEmail');
    }
});

// Auto-focus on email input
emailInput.focus();

console.log('🔐 Student Login Page Ready');
console.log('📡 API Base URL:', API_BASE_URL);
