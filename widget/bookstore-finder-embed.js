/**
 * Embeddable Bookstore Finder Widget
 *
 * Usage:
 * 1. Host bookstores.json on your server
 * 2. Include this script on your page
 * 3. Call: BookstoreFinder.init({ container: '#my-container', dataUrl: '/path/to/bookstores.json' })
 */

(function(window) {
    'use strict';

    const BookstoreFinder = {
        bookstores: [],
        container: null,
        dataUrl: '',

        // Default styles
        styles: `
            .bookstore-finder {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                box-sizing: border-box;
            }

            .bookstore-finder * {
                box-sizing: border-box;
            }

            .bookstore-finder-input {
                width: 100%;
                padding: 12px 16px;
                font-size: 16px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                outline: none;
                transition: border-color 0.2s;
            }

            .bookstore-finder-input:focus {
                border-color: #1976d2;
            }

            .bookstore-finder-input::placeholder {
                color: #999;
            }

            .bookstore-finder-results {
                margin-top: 16px;
            }

            .bookstore-finder-result {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
                transition: background 0.2s;
            }

            .bookstore-finder-result:last-child {
                border-bottom: none;
            }

            .bookstore-finder-result:hover {
                background: #f8f9fa;
            }

            .bookstore-finder-name {
                font-weight: 600;
                color: #1976d2;
                text-decoration: none;
                display: block;
                margin-bottom: 4px;
            }

            .bookstore-finder-name:hover {
                text-decoration: underline;
            }

            .bookstore-finder-location {
                font-size: 0.9em;
                color: #666;
            }

            .bookstore-finder-empty {
                padding: 20px;
                text-align: center;
                color: #666;
            }

            .bookstore-finder-hint {
                font-size: 0.85em;
                color: #888;
                margin-top: 8px;
            }
        `,

        /**
         * Initialize the widget
         * @param {Object} options - Configuration options
         * @param {string} options.container - CSS selector for container element
         * @param {string} options.dataUrl - URL to bookstores.json
         */
        init: function(options) {
            if (!options.container) {
                console.error('BookstoreFinder: container option is required');
                return;
            }

            if (!options.dataUrl) {
                console.error('BookstoreFinder: dataUrl option is required');
                return;
            }

            this.container = document.querySelector(options.container);
            if (!this.container) {
                console.error('BookstoreFinder: container element not found:', options.container);
                return;
            }

            this.dataUrl = options.dataUrl;

            // Inject styles
            this.injectStyles();

            // Render widget
            this.render();

            // Load data
            this.loadBookstores();
        },

        injectStyles: function() {
            if (document.getElementById('bookstore-finder-styles')) {
                return; // Already injected
            }

            const styleElement = document.createElement('style');
            styleElement.id = 'bookstore-finder-styles';
            styleElement.textContent = this.styles;
            document.head.appendChild(styleElement);
        },

        render: function() {
            this.container.innerHTML = `
                <div class="bookstore-finder">
                    <input
                        type="text"
                        class="bookstore-finder-input"
                        placeholder="Voer je postcode in (bijv. 1012)"
                        maxlength="4"
                        inputmode="numeric"
                        pattern="[0-9]*"
                    >
                    <div class="bookstore-finder-hint">Voer de eerste 4 cijfers van je postcode in</div>
                    <div class="bookstore-finder-results"></div>
                </div>
            `;

            // Bind events
            const input = this.container.querySelector('.bookstore-finder-input');
            input.addEventListener('input', (e) => {
                const value = e.target.value.replace(/[^0-9]/g, '');
                e.target.value = value;
                this.search(value);
            });
        },

        loadBookstores: async function() {
            try {
                const response = await fetch(this.dataUrl);
                if (!response.ok) {
                    throw new Error('Failed to load bookstores');
                }
                this.bookstores = await response.json();
            } catch (error) {
                console.error('BookstoreFinder: Error loading data:', error);
                const results = this.container.querySelector('.bookstore-finder-results');
                results.innerHTML = '<div class="bookstore-finder-empty">Kon boekhandels niet laden</div>';
            }
        },

        getPostcodeDistance: function(userPostcode, storePostcode) {
            if (!storePostcode) return 999999;

            // Extract numeric parts (first 4 digits)
            const userNum = parseInt(userPostcode);
            const storeNum = parseInt(storePostcode.substring(0, 4));

            // Calculate absolute numerical difference
            const diff = Math.abs(userNum - storeNum);

            // Return the absolute difference as distance
            // This ensures 5038 and 5044 are both 3 units away from 5041
            return diff;
        },

        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        search: function(postcode) {
            const resultsContainer = this.container.querySelector('.bookstore-finder-results');

            if (!postcode || postcode.length < 2) {
                resultsContainer.innerHTML = '';
                return;
            }

            const results = this.bookstores
                .map(store => ({
                    ...store,
                    distance: this.getPostcodeDistance(postcode, store.postal_code)
                }))
                .sort((a, b) => {
                    if (a.distance !== b.distance) {
                        return a.distance - b.distance;
                    }
                    return a.city.localeCompare(b.city);
                })
                .slice(0, 10);

            if (results.length === 0) {
                resultsContainer.innerHTML = '<div class="bookstore-finder-empty">Geen boekhandels gevonden</div>';
                return;
            }

            const html = results.map(store => `
                <div class="bookstore-finder-result">
                    <a href="${store.product_url}" target="_blank" rel="noopener" class="bookstore-finder-name">
                        ${this.escapeHtml(store.name)}
                    </a>
                    <div class="bookstore-finder-location">
                        ${this.escapeHtml(store.postal_code)} ${this.escapeHtml(store.city)}
                    </div>
                </div>
            `).join('');

            resultsContainer.innerHTML = html;
        }
    };

    // Export to window
    window.BookstoreFinder = BookstoreFinder;

})(window);
