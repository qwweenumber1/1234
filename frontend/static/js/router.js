/**
 * Smart3D SPA Router
 * A simple OOP-based router for handling Single Page Application navigation.
 */
class AppRouter {
    constructor() {
        this.mainContent = document.getElementById('main-content');
        this.links = document.querySelectorAll('[data-link]');
        this.init();
    }

    init() {
        // Intercept global link clicks
        document.body.addEventListener('click', e => {
            const link = e.target.closest('[data-link]');
            if (link) {
                e.preventDefault();
                this.navigateTo(link.getAttribute('href'));
            }
        });

        // Handle browser Back/Forward buttons
        window.addEventListener('popstate', () => {
            this.handleNavigation(window.location.pathname);
        });

        // Initial load
        console.log('Router initialized');
    }

    /**
     * Navigates to a specific URL and updates history
     */
    async navigateTo(url) {
        if (url === '#' || !url) return;
        history.pushState(null, null, url);
        await this.handleNavigation(url);
    }

    /**
     * Fetches content from the server and updates the DOM
     */
    async handleNavigation(url) {
        // Show loading state if needed
        this.mainContent.style.opacity = '0.5';

        try {
            const response = await fetch(url, {
                headers: {
                    'X-SPA': 'true',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`Navigation failed: ${response.status}`);
            }

            const html = await response.text();

            // Extract title if possible
            const titleMatch = html.match(/<title>(.*?)<\/title>/);
            if (titleMatch) {
                document.title = titleMatch[1];
            }

            // Update content
            this.mainContent.innerHTML = html;
            this.mainContent.style.opacity = '1';

            // Re-run scripts if they are in the content
            this.executeScripts(this.mainContent);

            // Notify page-specific JS
            window.dispatchEvent(new CustomEvent('page-loaded', { detail: { url } }));

            // Scroll to top
            window.scrollTo(0, 0);

            // Re-bind links in the new content
            this.handleAuthStatus();

        } catch (error) {
            console.error('Routing error:', error);
            this.mainContent.innerHTML = `<div style="padding: 50px; text-align: center;"><h2>Помилка завантаження</h2><p>${error.message}</p></div>`;
            this.mainContent.style.opacity = '1';
        }
    }

    /**
     * Executes script tags found in the new content
     */
    executeScripts(container) {
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }

    /**
     * Updates UI based on auth status (e.g., Вхід/Вихід)
     */
    handleAuthStatus() {
        if (typeof handleAuth === 'function') {
            handleAuth();
        }
    }
}

// Initialize router when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.appRouter = new AppRouter();
});
