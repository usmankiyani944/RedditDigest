class RedditFetcher {
    constructor() {
        this.init();
    }

    init() {
        // Get DOM elements
        this.searchInput = document.getElementById('searchInput');
        this.searchKeywordBtn = document.getElementById('searchKeywordBtn');
        this.fetchUrlBtn = document.getElementById('fetchUrlBtn');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.errorContainer = document.getElementById('errorContainer');
        this.errorMessage = document.getElementById('errorMessage');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.resultsTitle = document.getElementById('resultsTitle');
        this.resultsCount = document.getElementById('resultsCount');
        this.postsContainer = document.getElementById('postsContainer');

        // Bind event listeners
        this.searchKeywordBtn.addEventListener('click', () => this.searchByKeyword());
        this.fetchUrlBtn.addEventListener('click', () => this.fetchByUrl());
        
        // Allow Enter key to trigger keyword search
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.searchByKeyword();
            }
        });
    }

    showLoading() {
        this.loadingIndicator.style.display = 'block';
        this.errorContainer.style.display = 'none';
        this.resultsContainer.style.display = 'none';
        this.searchKeywordBtn.disabled = true;
        this.fetchUrlBtn.disabled = true;
    }

    hideLoading() {
        this.loadingIndicator.style.display = 'none';
        this.searchKeywordBtn.disabled = false;
        this.fetchUrlBtn.disabled = false;
    }

    showError(message) {
        this.hideLoading();
        this.errorMessage.textContent = message;
        this.errorContainer.style.display = 'block';
        this.resultsContainer.style.display = 'none';
    }

    showResults(data, isSearch = true) {
        this.hideLoading();
        this.errorContainer.style.display = 'none';
        
        if (isSearch) {
            this.resultsTitle.innerHTML = '<i class="fas fa-list me-2"></i>Search Results';
            this.resultsCount.textContent = `Found ${data.count} posts`;
            this.renderPosts(data.posts);
        } else {
            this.resultsTitle.innerHTML = '<i class="fas fa-link me-2"></i>Thread Details';
            this.resultsCount.textContent = 'Single post fetched';
            this.renderPosts([data.post]);
        }
        
        this.resultsContainer.style.display = 'block';
    }

    renderPosts(posts) {
        this.postsContainer.innerHTML = '';
        
        posts.forEach((post, index) => {
            const postElement = this.createPostElement(post, index);
            this.postsContainer.appendChild(postElement);
        });
    }

    createPostElement(post, index) {
        const postDiv = document.createElement('div');
        postDiv.className = 'card mb-4';
        
        // Create comments HTML
        let commentsHtml = '';
        if (post.comments && post.comments.length > 0) {
            commentsHtml = post.comments.map(comment => `
                <div class="border-start border-secondary ps-3 mb-2">
                    <small class="text-muted">
                        <i class="fas fa-user me-1"></i>
                        ${this.escapeHtml(comment.author)}
                    </small>
                    <p class="mb-0 mt-1">${this.escapeHtml(comment.body)}</p>
                </div>
            `).join('');
        } else {
            commentsHtml = '<p class="text-muted fst-italic">No comments available</p>';
        }

        postDiv.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <div>
                    <span class="badge bg-secondary me-2">r/${this.escapeHtml(post.subreddit)}</span>
                    <small class="text-muted">
                        <i class="fas fa-user me-1"></i>
                        ${this.escapeHtml(post.author)}
                    </small>
                </div>
                <div class="d-flex align-items-center">
                    <i class="fas fa-arrow-up me-1"></i>
                    <span class="badge bg-info">${post.score}</span>
                </div>
            </div>
            <div class="card-body">
                <h5 class="card-title mb-3">
                    <a href="${post.url}" target="_blank" class="text-decoration-none">
                        ${this.escapeHtml(post.title)}
                        <i class="fas fa-external-link-alt ms-1 small"></i>
                    </a>
                </h5>
                
                <div class="mt-4">
                    <h6 class="text-muted mb-3">
                        <i class="fas fa-comments me-2"></i>
                        Top Comments (${post.comments ? post.comments.length : 0})
                    </h6>
                    <div class="comments-section">
                        ${commentsHtml}
                    </div>
                </div>
            </div>
        `;

        return postDiv;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async searchByKeyword() {
        const keyword = this.searchInput.value.trim();
        
        if (!keyword) {
            this.showError('Please enter a keyword to search');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/search-keyword', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keyword })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to search Reddit');
            }

            this.showResults(data, true);

        } catch (error) {
            console.error('Search error:', error);
            this.showError(`Search failed: ${error.message}`);
        }
    }

    async fetchByUrl() {
        const url = this.searchInput.value.trim();
        
        if (!url) {
            this.showError('Please enter a Reddit URL to fetch');
            return;
        }

        // Basic URL validation
        if (!url.includes('reddit.com')) {
            this.showError('Please enter a valid Reddit URL');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/fetch-by-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch Reddit post');
            }

            this.showResults(data, false);

        } catch (error) {
            console.error('Fetch error:', error);
            this.showError(`Fetch failed: ${error.message}`);
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RedditFetcher();
});
