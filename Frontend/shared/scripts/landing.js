// Background Image Slider
let currentSlide = 0;
const slides = document.querySelectorAll('.background-slider .slide');
const totalSlides = slides.length;

function changeSlide() {
    slides[currentSlide].classList.remove('active');
    currentSlide = (currentSlide + 1) % totalSlides;
    slides[currentSlide].classList.add('active');
}

// Change background every 5 seconds
setInterval(changeSlide, 5000);

// Role Navigation
function navigateToRole(role) {
    if (role === 'student') {
        // Navigate to student login/dashboard
        window.location.href = 'student/pages/login.html';
    } else if (role === 'admin') {
        // Navigate to admin login/dashboard
        window.location.href = 'admin/pages/login.html';
    }
}

// Smooth Scroll for Navigation Links
document.querySelectorAll('.nav a').forEach(link => {
    link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href.startsWith('#')) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Add animation on scroll for features
const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-item').forEach(item => {
    item.style.opacity = '0';
    item.style.transform = 'translateY(20px)';
    item.style.transition = 'all 0.6s ease-out';
    observer.observe(item);
});

// Add hover effect sound (optional - can be enabled)
const roleCards = document.querySelectorAll('.role-card');
roleCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-8px) scale(1.02)';
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0) scale(1)';
    });
});

// Parallax effect for background
let ticking = false;

function updateParallax(scrollPos) {
    const slider = document.querySelector('.background-slider');
    slider.style.transform = `translateY(${scrollPos * 0.5}px)`;
}

window.addEventListener('scroll', () => {
    const scrollPos = window.pageYOffset;
    
    if (!ticking) {
        window.requestAnimationFrame(() => {
            updateParallax(scrollPos);
            ticking = false;
        });
        ticking = true;
    }
});

// Prevent accidental double-clicks
let clickTimeout;
roleCards.forEach(card => {
    card.addEventListener('click', function(e) {
        if (clickTimeout) return;
        
        clickTimeout = setTimeout(() => {
            clickTimeout = null;
        }, 500);
    });
});

console.log('🚀 LibraryAI Landing Page Loaded Successfully!');
console.log('📚 Ready to transform your library experience with AI');
