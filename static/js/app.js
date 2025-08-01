class RedditFetcher {
    constructor() {
        this.init();
    }

    init() {
        // Get DOM elements
        this.searchInput = document.getElementById('searchInput');
        this.brandNameInput = document.getElementById('brandNameInput');
        this.hardRefreshCheck = document.getElementById('hardRefreshCheck');
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
        // Clear previous results to show fresh data
        this.postsContainer.innerHTML = '';
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
            const refreshMode = data.refresh_mode || '';
            const refreshText = refreshMode === 'latest' ? ' (Latest Results)' : '';
            this.resultsTitle.innerHTML = `<i class="fas fa-list me-2"></i>Search Results${refreshText}`;
            this.resultsCount.textContent = `Found ${data.count} posts${refreshMode === 'latest' ? ' from this week' : ''}`;
            
            // Display ChatGPT analysis if available
            if (data.chatgpt_analysis) {
                this.renderChatGPTAnalysis(data.chatgpt_analysis);
            }
            
            this.renderPosts(data.posts);
        } else {
            this.resultsTitle.innerHTML = '<i class="fas fa-link me-2"></i>Thread Details';
            this.resultsCount.textContent = 'Single post fetched';
            this.renderPosts([data.post]);
        }
        
        this.resultsContainer.style.display = 'block';
    }

    renderChatGPTAnalysis(analysis) {
        const analysisContainer = document.createElement('div');
        analysisContainer.className = 'alert alert-info mb-4';
        analysisContainer.innerHTML = `
            <div class="d-flex align-items-center mb-3">
                <i class="fas fa-robot me-2"></i>
                <strong>ChatGPT Analysis</strong>
                <span class="badge bg-success ms-2">Reddit cited as source</span>
            </div>
            <div class="analysis-content">
                ${this.formatAnalysisText(analysis.analysis)}
            </div>
            <div class="mt-3 small text-muted">
                <i class="fas fa-chart-bar me-1"></i>
                Analyzed ${analysis.reddit_posts_analyzed} Reddit posts for query: "${analysis.query}"
            </div>
        `;
        
        // Insert at the beginning of posts container
        this.postsContainer.appendChild(analysisContainer);
    }

    formatAnalysisText(text) {
        // Convert line breaks to HTML breaks and preserve formatting
        return text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>').replace(/^/, '<p>').replace(/$/, '</p>');
    }

    renderPosts(posts) {
        // Clear previous results completely
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
            commentsHtml = post.comments.map((comment, commentIndex) => `
                <div class="border-start border-secondary ps-3 mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">
                            <i class="fas fa-user me-1"></i>
                            ${this.escapeHtml(comment.author)}
                        </small>
                        <div class="d-flex align-items-center">
                            <i class="fas fa-arrow-up me-1 text-success"></i>
                            <span class="badge bg-success me-2">${comment.score || 0}</span>
                            <button class="btn btn-outline-primary btn-sm" onclick="redditFetcher.generateReply(\`${comment.body.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`, ${index}, ${commentIndex})">
                                <i class="fas fa-reply me-1"></i>
                                Generate Reply
                            </button>
                        </div>
                    </div>
                    <p class="mb-0 mt-1">${this.escapeHtml(comment.body)}</p>
                    <div id="reply-container-${index}-${commentIndex}" class="mt-2" style="display: none;">
                        <div class="alert alert-info">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <strong><i class="fas fa-robot me-2"></i>AI Generated Reply:</strong>
                                <button class="btn btn-outline-secondary btn-sm" onclick="redditFetcher.regenerateReply(\`${comment.body.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`, ${index}, ${commentIndex})">
                                    <i class="fas fa-redo me-1"></i>
                                    Regenerate
                                </button>
                            </div>
                            <div id="reply-content-${index}-${commentIndex}"></div>
                            <div id="reply-analysis-${index}-${commentIndex}" class="mt-2 small text-muted"></div>
                        </div>
                    </div>
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
                
                <div class="mt-3 mb-4">
                    <button class="btn btn-primary" onclick="redditFetcher.generateMainPostReply(\`${post.title.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`, ${index})">
                        <i class="fas fa-reply me-1"></i>
                        Generate Reply to Main Post
                    </button>
                    <div id="main-reply-container-${index}" class="mt-3" style="display: none;">
                        <div class="alert alert-success">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <strong><i class="fas fa-robot me-2"></i>AI Reply to Main Post:</strong>
                                <button class="btn btn-outline-success btn-sm" onclick="redditFetcher.regenerateMainPostReply(\`${post.title.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`, ${index})">
                                    <i class="fas fa-redo me-1"></i>
                                    Regenerate
                                </button>
                            </div>
                            <div id="main-reply-content-${index}"></div>
                            <div id="main-reply-analysis-${index}" class="mt-2 small text-muted"></div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h6 class="text-muted mb-3">
                        <i class="fas fa-comments me-2"></i>
                        Top 10 Most Upvoted Comments (${post.comments ? post.comments.length : 0})
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
        const forceRefresh = this.hardRefreshCheck.checked;
        
        if (!keyword) {
            this.showError('Please enter a keyword to search');
            return;
        }

        // Check if input looks like a URL
        if (keyword.includes('reddit.com') || keyword.startsWith('http')) {
            this.showError('This looks like a URL. Please use the "Fetch by Thread URL" button instead.');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/search-keyword', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    keyword: keyword,
                    force_refresh: forceRefresh
                })
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

    async generateReply(commentText, postIndex, commentIndex) {
        const replyContainer = document.getElementById(`reply-container-${postIndex}-${commentIndex}`);
        const replyContent = document.getElementById(`reply-content-${postIndex}-${commentIndex}`);
        const replyAnalysis = document.getElementById(`reply-analysis-${postIndex}-${commentIndex}`);
        
        // Show loading state
        replyContent.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Generating reply...';
        replyContainer.style.display = 'block';
        
        try {
            const brandName = this.brandNameInput.value.trim();
            
            const response = await fetch('/generate-reply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    comment_text: commentText,
                    brand_name: brandName,
                    is_main_post: false
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate reply');
            }

            // Display the generated reply
            replyContent.innerHTML = `<p class="mb-0">${this.escapeHtml(data.reply)}</p>`;
            
            // Display analysis information
            const sentiment = data.sentiment || {};
            const emotion = data.emotion || {};
            const primaryEmotion = emotion.emotions_detected && emotion.emotions_detected.length > 0 
                ? emotion.emotions_detected[0].emotion 
                : 'neutral';
            
            const brandUsed = data.brand_used ? `<div class="col-md-12"><span class="badge bg-warning">Brand "${brandName}" integrated</span></div>` : '';
            
            replyAnalysis.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Sentiment:</strong> 
                        <span class="badge bg-${sentiment.type === 'positive' ? 'success' : sentiment.type === 'negative' ? 'danger' : 'secondary'}">
                            ${sentiment.type || 'neutral'} (${(sentiment.score || 0).toFixed(2)})
                        </span>
                    </div>
                    <div class="col-md-6">
                        <strong>Primary Emotion:</strong> 
                        <span class="badge bg-info">${primaryEmotion}</span>
                    </div>
                    ${brandUsed}
                </div>
            `;

        } catch (error) {
            console.error('Reply generation error:', error);
            replyContent.innerHTML = `<div class="text-danger"><i class="fas fa-exclamation-triangle me-1"></i>Failed to generate reply: ${error.message}</div>`;
        }
    }

    async generateMainPostReply(postTitle, postIndex) {
        const replyContainer = document.getElementById(`main-reply-container-${postIndex}`);
        const replyContent = document.getElementById(`main-reply-content-${postIndex}`);
        const replyAnalysis = document.getElementById(`main-reply-analysis-${postIndex}`);
        
        // Show loading state
        replyContent.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Generating reply to main post...';
        replyContainer.style.display = 'block';
        
        try {
            const brandName = this.brandNameInput.value.trim();
            
            const response = await fetch('/generate-reply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    comment_text: postTitle,
                    brand_name: brandName,
                    is_main_post: true
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate reply');
            }

            // Display the generated reply
            replyContent.innerHTML = `<p class="mb-0">${this.escapeHtml(data.reply)}</p>`;
            
            // Display analysis information
            const sentiment = data.sentiment || {};
            const emotion = data.emotion || {};
            const primaryEmotion = emotion.emotions_detected && emotion.emotions_detected.length > 0 
                ? emotion.emotions_detected[0].emotion 
                : 'neutral';
            
            const brandUsed = data.brand_used ? `<div class="col-md-12"><span class="badge bg-warning">Brand "${brandName}" integrated</span></div>` : '';
            
            replyAnalysis.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>Sentiment:</strong> 
                        <span class="badge bg-${sentiment.type === 'positive' ? 'success' : sentiment.type === 'negative' ? 'danger' : 'secondary'}">
                            ${sentiment.type || 'neutral'} (${(sentiment.score || 0).toFixed(2)})
                        </span>
                    </div>
                    <div class="col-md-6">
                        <strong>Primary Emotion:</strong> 
                        <span class="badge bg-info">${primaryEmotion}</span>
                    </div>
                    ${brandUsed}
                </div>
            `;

        } catch (error) {
            console.error('Main post reply generation error:', error);
            replyContent.innerHTML = `<div class="text-danger"><i class="fas fa-exclamation-triangle me-1"></i>Failed to generate reply: ${error.message}</div>`;
        }
    }

    async regenerateReply(commentText, postIndex, commentIndex) {
        // Simply call generateReply again to get a new response
        await this.generateReply(commentText, postIndex, commentIndex);
    }

    async regenerateMainPostReply(postTitle, postIndex) {
        // Simply call generateMainPostReply again to get a new response
        await this.generateMainPostReply(postTitle, postIndex);
    }
}

// Global variable to access the instance from onclick handlers
let redditFetcher;

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    redditFetcher = new RedditFetcher();
});
