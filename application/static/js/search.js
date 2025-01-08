document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('liveSearchResults');
    let searchTimeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }

        // Show loading state
        resultsContainer.innerHTML = '<div class="p-3">Searching...</div>';
        resultsContainer.style.display = 'block';

        // Debounce the search
        searchTimeout = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(results => {
                    if (results.length === 0) {
                        resultsContainer.innerHTML = '<div class="p-3">No results found</div>';
                        return;
                    }

                    resultsContainer.innerHTML = results.map(result => `
                        <a href="${result.url}" class="live-search-item d-block text-decoration-none">
                            <div class="d-flex align-items-center">
                                <div>
                                    <h6 class="mb-0">${result.title}</h6>
                                </div>
                            </div>
                        </a>
                    `).join('');
                })
                .catch(error => {
                    console.error('Search error:', error);
                    resultsContainer.innerHTML = '<div class="p-3">Error performing search</div>';
                });
        }, 300);
    });

    // Close results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.style.display = 'none';
        }
    });
}); 