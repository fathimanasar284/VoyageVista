// auth.js - Handles authentication and user sessions

document.addEventListener('DOMContentLoaded', function() {
    // Registration form handling
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Store user data (in a real app, this would be a server API call)
            const userData = {
                username: username,
                email: email,
                password: password // In a real app, this should be securely hashed!
            };
            
            // Store in localStorage for demo purposes
            localStorage.setItem('users_' + email, JSON.stringify(userData));
            
            // Set as current user
            setCurrentUser(userData);
            
            alert('Registration successful!');
            window.location.href = 'index.html';
        });
    }
    
    // Sign in form handling
    const signinForm = document.getElementById('signinForm');
    if (signinForm) {
        signinForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('signinEmail').value;
            const password = document.getElementById('signinPassword').value;
            
            // Retrieve user (in a real app, this would be a server API call)
            const storedUserJSON = localStorage.getItem('users_' + email);
            
            if (storedUserJSON) {
                const storedUser = JSON.parse(storedUserJSON);
                
                if (storedUser.password === password) {
                    // Set as current user
                    setCurrentUser(storedUser);
                    
                    alert('Login successful!');
                    window.location.href = 'index.html';
                } else {
                    alert('Incorrect password!');
                }
            } else {
                alert('User not found!');
            }
        });
    }
    
    // Check for session and update UI on every page
    checkSession();
});

// Set the current logged-in user
function setCurrentUser(userData) {
    localStorage.setItem('currentUser', JSON.stringify(userData));
}

// Get the current logged-in user
function getCurrentUser() {
    const currentUserJSON = localStorage.getItem('currentUser');
    return currentUserJSON ? JSON.parse(currentUserJSON) : null;
}

// Log out the current user
function logoutUser() {
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

// Check if a user is logged in and update the UI accordingly
function checkSession() {
    const currentUser = getCurrentUser();
    
    // Get auth links container (for pages with auth links)
    const authLinks = document.querySelector('.auth-links');
    
    // Get nav links container (for all pages)
    const navLinks = document.querySelector('.nav-links');
    
    if (currentUser) {
        // User is logged in
        if (authLinks) {
            authLinks.innerHTML = '';
            
            // Create user avatar
            const userAvatar = document.createElement('div');
            userAvatar.className = 'user-avatar';
            
            // Get first letter of username for the avatar
            const firstLetter = currentUser.username.charAt(0).toUpperCase();
            userAvatar.innerHTML = `
                <div class="avatar-circle">
                    <span class="avatar-text">${firstLetter}</span>
                </div>
                <div class="dropdown-content">
                    <span>${currentUser.username}</span>
                    <a href="#" onclick="logoutUser()">Log Out</a>
                </div>
            `;
            
            authLinks.appendChild(userAvatar);
        }
        
        // If the page doesn't have authLinks but has navLinks (like destinations.html)
        if (!authLinks && navLinks) {
            // Check if user avatar already exists in nav
            if (!document.querySelector('.user-avatar')) {
                // Create user avatar for nav
                const userAvatar = document.createElement('div');
                userAvatar.className = 'user-avatar';
                
                // Get first letter of username for the avatar
                const firstLetter = currentUser.username.charAt(0).toUpperCase();
                userAvatar.innerHTML = `
                    <div class="avatar-circle">
                        <span class="avatar-text">${firstLetter}</span>
                    </div>
                    <div class="dropdown-content">
                        <span>${currentUser.username}</span>
                        <a href="#" onclick="logoutUser()">Log Out</a>
                    </div>
                `;
                
                navLinks.appendChild(userAvatar);
            }
        }
    } else {
        // User is not logged in, ensure auth links are visible
        if (authLinks) {
            authLinks.innerHTML = `
                <a href="register.html">Register</a>
                <a href="signin.html">Sign In</a>
            `;
        }
    }
}