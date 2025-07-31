/**
 * Recommendation Widget Loader
 * This script handles loading the recommendation widget dynamically
 */

function loadRecommendationWidget(containerId = 'recommendation-widget-container', trackCurrentPage = false) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Recommendation widget container not found');
        return;
    }
    
    fetch('/recommendation-widget.html')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load recommendation widget');
            }
            return response.text();
        })
        .then(html => {
            container.innerHTML = html;
            
            // Execute any scripts in the widget
            const scripts = container.getElementsByTagName('script');
            for (let i = 0; i < scripts.length; i++) {
                eval(scripts[i].innerText);
            }
            
            // Track the current page if requested
            if (trackCurrentPage) {
                const currentPage = window.location.pathname.split('/').pop().split('.')[0].toLowerCase();
                
                // Only track if it's a destination page
                if (['kerala', 'karnataka', 'maharashtra'].includes(currentPage)) {
                    localStorage.setItem('lastViewedDestination', currentPage);
                    
                    // If user is logged in, track this view
                    const currentUser = window.getCurrentUser ? getCurrentUser() : null;
                    if (currentUser && currentUser.email) {
                        fetch('/api/track/view', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ destination: currentPage })
                        }).catch(err => console.error('Failed to track view:', err));
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error loading recommendation widget:', error);
            container.innerHTML = '<p>Unable to load recommendations at this time.</p>';
        });
}

// If this script is loaded directly on a page
document.addEventListener('DOMContentLoaded', function() {
    // Check if the container exists before trying to load
    if (document.getElementById('recommendation-widget-container')) {
        // For destination pages, track the current page
        const isDestinationPage = ['kerala.html', 'karnataka.html', 'maharashtra.html'].some(
            page => window.location.pathname.endsWith(page)
        );
        
        loadRecommendationWidget('recommendation-widget-container', isDestinationPage);
    }
});