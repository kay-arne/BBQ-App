// Modern BBQ App JavaScript - Enhanced functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('BBQ App loaded successfully');
    
    // Initialize form handling
    initializeForm();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize animations
    initializeAnimations();
});

// Form handling
function initializeForm() {
    const form = document.getElementById('bbqForm');
    if (!form) return;
    
    form.addEventListener('submit', handleFormSubmit);
    
    // Add real-time validation
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearFieldError);
    });
}

function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitButton = form.querySelector('.submit-button');
    const buttonText = submitButton.querySelector('.button-text');
    const buttonLoading = submitButton.querySelector('.button-loading');
    
    // Show loading state
    submitButton.classList.add('loading');
    submitButton.disabled = true;
    
    // Validate form
    if (!validateForm(form)) {
        resetButtonState(submitButton, buttonText, buttonLoading);
            return;
        }

    // Prepare form data
    const formData = new FormData(form);
    
    // Show loading message
    showMessage('Uw aanmelding wordt verwerkt...', 'info');
    
    // Submit form
    fetch('/api/register', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Aanmelding succesvol! U wordt doorgestuurd naar de betaalpagina...', 'success');
            setTimeout(() => {
                window.location.href = data.payment_url || '/success';
            }, 2000);
        } else {
            showMessage(data.message || 'Er is een fout opgetreden. Probeer het opnieuw.', 'error');
        }
    })
    .catch(error => {
        console.error('Form submission error:', error);
        showMessage('Er is een fout opgetreden. Controleer uw internetverbinding en probeer het opnieuw.', 'error');
    })
    .finally(() => {
        resetButtonState(submitButton, buttonText, buttonLoading);
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    // Clear previous errors
    clearAllErrors(form);
    
    requiredFields.forEach(field => {
        if (!validateField({ target: field })) {
            isValid = false;
        }
    });
    
    // Validate email if provided
    const emailField = form.querySelector('input[type="email"]');
    if (emailField && emailField.value) {
        if (!isValidEmail(emailField.value)) {
            showFieldError(emailField, 'Voer een geldig e-mailadres in');
            isValid = false;
        }
    }
    
    // Validate phone if provided
    const phoneField = form.querySelector('input[type="tel"]');
    if (phoneField && phoneField.value) {
        if (!isValidPhone(phoneField.value)) {
            showFieldError(phoneField, 'Voer een geldig telefoonnummer in');
            isValid = false;
        }
    }
    
    return isValid;
}

function validateField(e) {
    const field = e.target;
    const value = field.value.trim();
    
    // Clear previous error
    clearFieldError(e);
    
    // Check if required field is empty
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'Dit veld is verplicht');
        return false;
    }
    
    // Specific validations
    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Voer een geldig e-mailadres in');
        return false;
    }
    
    if (field.type === 'tel' && value && !isValidPhone(value)) {
        showFieldError(field, 'Voer een geldig telefoonnummer in');
        return false;
    }
    
    if (field.name === 'houseNumber' && value && !isValidHouseNumber(value)) {
        showFieldError(field, 'Voer een geldig huisnummer in (bijv. 46 of 46a)');
        return false;
    }
    
    if (field.type === 'number') {
        const num = parseInt(value);
        if (value && (isNaN(num) || num < 0)) {
            showFieldError(field, 'Voer een geldig getal in');
            return false;
        }
        
        if (field.name === 'personsAdults' && num > 20) {
            showFieldError(field, 'Maximaal 20 volwassenen per aanmelding');
            return false;
        }
        
        if (field.name === 'personsChildren' && num > 20) {
            showFieldError(field, 'Maximaal 20 kinderen per aanmelding');
            return false;
        }
    }
    
    return true;
}

function clearFieldError(e) {
    const field = e.target;
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
    field.classList.remove('error');
}

function clearAllErrors(form) {
    const errorElements = form.querySelectorAll('.field-error');
    errorElements.forEach(error => error.remove());
    
    const errorFields = form.querySelectorAll('.error');
    errorFields.forEach(field => field.classList.remove('error'));
}

function showFieldError(field, message) {
    field.classList.add('error');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    errorElement.style.color = '#e74c3c';
    errorElement.style.fontSize = '0.8rem';
    errorElement.style.marginTop = '0.25rem';
    
    field.parentNode.appendChild(errorElement);
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

function isValidHouseNumber(houseNumber) {
    const houseNumberRegex = /^\d+[a-zA-Z]?$/;
    return houseNumberRegex.test(houseNumber);
}

function resetButtonState(submitButton, buttonText, buttonLoading) {
    submitButton.classList.remove('loading');
    submitButton.disabled = false;
}

function showMessage(message, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    messageElement.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    
    // Insert message at the top of the form
    const form = document.getElementById('bbqForm');
    if (form) {
        form.insertBefore(messageElement, form.firstChild);
        
        // Auto-remove after 5 seconds for info messages
        if (type === 'info') {
                setTimeout(() => {
                messageElement.remove();
            }, 5000);
        }
    }
}

// Smooth scrolling
function initializeSmoothScrolling() {
    // Handle anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
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
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animateElements = document.querySelectorAll('.event-card, .benefit-card, .step-item');
    animateElements.forEach(el => {
        observer.observe(el);
    });
}

// Utility functions
function scrollToForm() {
    const formSection = document.getElementById('registration-form');
    if (formSection) {
        formSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(15, 15, 15, 0.98)';
        } else {
            navbar.style.background = 'rgba(15, 15, 15, 0.95)';
        }
    }
});

// Form auto-save (optional)
function autoSaveForm() {
    const form = document.getElementById('bbqForm');
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        // Load saved value
        const savedValue = localStorage.getItem(`bbq_form_${input.name}`);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
        
        // Save on change
        input.addEventListener('input', function() {
            localStorage.setItem(`bbq_form_${this.name}`, this.value);
        });
    });
}

// Clear form data after successful submission
function clearFormData() {
    const form = document.getElementById('bbqForm');
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        localStorage.removeItem(`bbq_form_${input.name}`);
    });
}

// Initialize auto-save
document.addEventListener('DOMContentLoaded', autoSaveForm);

// Export functions for global access
window.scrollToForm = scrollToForm;
window.clearFormData = clearFormData;