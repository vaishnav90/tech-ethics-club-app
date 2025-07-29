// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFloatingCards();
    initializeThemeToggle();
    initializeScrollIndicator();
    initializeSmoothScrolling();
    initializeAnimations();
});

// Floating Cards Animation
function initializeFloatingCards() {
    const floatingCardsContainer = document.getElementById('floatingCards');
    const cardImages = [
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=120&h=160&fit=crop',
        'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=120&h=160&fit=crop'
    ];

    // Create floating cards
    for (let i = 0; i < 12; i++) {
        const card = document.createElement('div');
        card.className = 'floating-card';
        
        const img = document.createElement('img');
        img.src = cardImages[i % cardImages.length];
        img.alt = 'Floating inspiration card';
        
        card.appendChild(img);
        
        // Random positioning and animation delays
        card.style.left = Math.random() * 80 + 10 + '%';
        card.style.top = Math.random() * 80 + 10 + '%';
        card.style.animationDelay = Math.random() * 20 + 's';
        card.style.animationDuration = (15 + Math.random() * 10) + 's';
        
        floatingCardsContainer.appendChild(card);
    }

    // Add mouse parallax effect
    document.addEventListener('mousemove', function(e) {
        const cards = document.querySelectorAll('.floating-card');
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;

        cards.forEach((card, index) => {
            const speed = 0.5 + (index * 0.1);
            const x = (mouseX - 0.5) * speed * 20;
            const y = (mouseY - 0.5) * speed * 20;
            
            card.style.transform = `translate(${x}px, ${y}px) rotate(${x * 0.5}deg)`;
        });
    });
}

// Theme Toggle
function initializeThemeToggle() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeButtons(currentTheme);

    themeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const theme = this.getAttribute('data-theme');
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            updateThemeButtons(theme);
        });
    });
}

function updateThemeButtons(activeTheme) {
    const themeButtons = document.querySelectorAll('.theme-btn');
    themeButtons.forEach(button => {
        button.classList.remove('active');
        if (button.getAttribute('data-theme') === activeTheme) {
            button.classList.add('active');
        }
    });
}

// Scroll Indicator
function initializeScrollIndicator() {
    const scrollIndicator = document.querySelector('.scroll-indicator');
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        
        // Hide scroll indicator when scrolled down
        if (scrollTop > windowHeight * 0.5) {
            scrollIndicator.style.opacity = '0';
            scrollIndicator.style.pointerEvents = 'none';
        } else {
            scrollIndicator.style.opacity = '1';
            scrollIndicator.style.pointerEvents = 'auto';
        }
    });
}

// Smooth Scrolling
function initializeSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Animations
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all sections
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(section);
    });

    // Parallax effect for hero section
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero');
        const heroContent = document.querySelector('.hero-content');
        
        if (hero && heroContent) {
            heroContent.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    });
}

// Cookie Consent
function acceptCookies() {
    const cookieBanner = document.getElementById('cookieBanner');
    cookieBanner.style.display = 'none';
    localStorage.setItem('cookiesAccepted', 'true');
}

// Check if cookies were already accepted
if (localStorage.getItem('cookiesAccepted')) {
    document.getElementById('cookieBanner').style.display = 'none';
}

// Button Interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Category interactions
    const categories = document.querySelectorAll('.category');
    categories.forEach(category => {
        category.addEventListener('click', function() {
            // Remove active class from all categories
            categories.forEach(c => c.classList.remove('active'));
            // Add active class to clicked category
            this.classList.add('active');
        });
    });

    // Extension card interactions
    const extensionCards = document.querySelectorAll('.extension-card');
    extensionCards.forEach(card => {
        card.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'translateY(-4px)';
            }, 150);
        });
    });

    // Cluster card interactions
    const clusterCards = document.querySelectorAll('.cluster-card');
    clusterCards.forEach(card => {
        card.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'translateY(-2px)';
            }, 150);
        });
    });
});

// Performance optimizations
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Optimize scroll events
const optimizedScrollHandler = debounce(function() {
    // Scroll-based animations and effects
}, 16); // ~60fps

window.addEventListener('scroll', optimizedScrollHandler);

// Add loading animation
window.addEventListener('load', function() {
    document.body.classList.add('loaded');
});

// Add CSS for loading state
const style = document.createElement('style');
style.textContent = `
    body:not(.loaded) {
        overflow: hidden;
    }
    
    body:not(.loaded)::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: var(--bg-primary);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    body:not(.loaded)::after {
        content: 'COSMOS';
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: var(--font-display);
        font-size: 2rem;
        color: var(--text-primary);
        z-index: 10000;
        animation: pulse 2s ease-in-out infinite;
    }
`;
document.head.appendChild(style); 