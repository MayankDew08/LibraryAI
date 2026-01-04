const API_BASE_URL = 'http://127.0.0.1:8000';

// SECURITY: Clear student session on admin pages
localStorage.removeItem('student');

// Get authentication headers with JWT token
function getAuthHeaders() {
    const admin = JSON.parse(localStorage.getItem('admin') || '{}');
    if (!admin.access_token || admin.role !== 'admin') {
        // Redirect to login if no token or not admin
        localStorage.removeItem('admin');
        window.location.replace('login.html');
        return {};
    }
    return {
        'Authorization': `Bearer ${admin.access_token}`
    };
}

// Check if admin is authenticated - verifies token with backend
async function checkAuth() {
    const admin = JSON.parse(localStorage.getItem('admin') || '{}');
    
    // SECURITY: Must have token AND role must be 'admin'
    if (!admin.access_token || admin.role !== 'admin') {
        localStorage.removeItem('admin');
        window.location.replace('login.html');
        return false;
    }
    
    // SECURITY: Verify token is valid by making actual API call to admin endpoint
    try {
        const response = await fetch(`${API_BASE_URL}/admin/books/`, {
            headers: { 'Authorization': `Bearer ${admin.access_token}` }
        });
        
        if (response.status === 401 || response.status === 403) {
            // Token expired, invalid, or not authorized as admin
            localStorage.removeItem('admin');
            window.location.replace('login.html');
            return false;
        }
        
        if (!response.ok) {
            // Other server error - don't show admin panel
            console.error('Server error during auth verification');
            localStorage.removeItem('admin');
            window.location.replace('login.html');
            return false;
        }
        
        // Token is valid AND user is admin - show the page content
        document.body.classList.add('authenticated');
        return true;
    } catch (error) {
        console.error('Auth verification failed:', error);
        // SECURITY: Network error - DO NOT show admin panel, redirect to login
        localStorage.removeItem('admin');
        window.location.replace('login.html');
        return false;
    }
}

// Navigation
function navigateTo(page) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
    
    // Show selected page
    document.getElementById(`${page}-page`).classList.add('active');
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Update page title
    const titles = {
        'overview': { title: 'Dashboard Overview', subtitle: 'Manage your library system' },
        'add-book': { title: 'Add New Book', subtitle: 'Upload a new book to the library' },
        'all-books': { title: 'All Books', subtitle: 'Manage and view all books' },
        'borrow-records': { title: 'Borrow Records', subtitle: 'View student borrow history' },
        'verify-returns': { title: 'Verify Returns', subtitle: 'Verify fine payments and returns' }
    };
    
    document.getElementById('pageTitle').textContent = titles[page].title;
    document.getElementById('pageSubtitle').textContent = titles[page].subtitle;
    
    // Load page data
    if (page === 'overview') {
        loadOverviewStats();
    } else if (page === 'all-books') {
        loadAllBooks();
    } else if (page === 'borrow-records') {
        loadBorrowRecords();
    } else if (page === 'verify-returns') {
        loadPendingVerifications();
    }
}

// Setup navigation listeners
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first - this verifies with backend and shows page if valid
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) return;
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            navigateTo(page);
        });
    });
    
    // Setup file input displays
    setupFileInputs();
    
    // Setup form submission
    document.getElementById('addBookForm').addEventListener('submit', handleBookSubmission);
    
    // Load initial overview
    loadOverviewStats();
});

// File input handlers
function setupFileInputs() {
    const pdfInput = document.getElementById('pdfFile');
    const imageInput = document.getElementById('coverImage');
    
    pdfInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || 'Choose PDF file';
        pdfInput.parentElement.querySelector('.file-name').textContent = fileName;
    });
    
    imageInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || 'Choose image file';
        imageInput.parentElement.querySelector('.file-name').textContent = fileName;
    });
}

// Load overview statistics
async function loadOverviewStats() {
    try {
        // Fetch all books
        const booksResponse = await fetch(`${API_BASE_URL}/admin/books/`, {
            headers: getAuthHeaders()
        });
        const books = await booksResponse.json();
        document.getElementById('totalBooks').textContent = books.length || 0;
        
        // Fetch borrow records
        const borrowsResponse = await fetch(`${API_BASE_URL}/borrow/admin/all-borrows`, {
            headers: getAuthHeaders()
        });
        const borrowsData = await borrowsResponse.json();
        const borrows = borrowsData.borrow_records || [];
        
        // Count active borrows
        const activeBorrows = borrows.filter(b => b.status === 'ACTIVE' || b.status === 'OVERDUE').length;
        document.getElementById('activeBorrows').textContent = activeBorrows;
        
        // Calculate pending fines
        const pendingFines = borrows
            .filter(b => b.fine_amount > 0 && b.status !== 'RETURNED')
            .reduce((sum, b) => sum + b.fine_amount, 0);
        document.getElementById('pendingFines').textContent = `₹${pendingFines}`;
        
        // Fetch pending verifications
        const verifyResponse = await fetch(`${API_BASE_URL}/borrow/admin/pending-verifications`, {
            headers: getAuthHeaders()
        });
        const verifyData = await verifyResponse.json();
        const verifications = verifyData.pending_verifications || [];
        document.getElementById('pendingVerifications').textContent = verifications.length || 0;
        
        // Load analytics
        loadAnalytics(books, borrows);
        
    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
}

// Load comprehensive analytics
function loadAnalytics(books, borrows) {
    renderCategoryDistribution(books);
    renderBorrowStatus(borrows);
    renderTopBorrowedBooks(books, borrows);
    renderFineAnalytics(borrows);
    renderAvailability(books);
    renderBorrowingTrends(borrows);
}

// 1. Category Distribution Chart
function renderCategoryDistribution(books) {
    const categoryMap = {};
    books.forEach(book => {
        if (book.categories && Array.isArray(book.categories)) {
            book.categories.forEach(cat => {
                categoryMap[cat] = (categoryMap[cat] || 0) + 1;
            });
        }
    });
    
    // Show ALL categories, sorted by count
    const categories = Object.entries(categoryMap)
        .sort((a, b) => b[1] - a[1]);
    
    const totalCategories = categories.length;
    document.getElementById('categoryCount').textContent = `${totalCategories} ${totalCategories === 1 ? 'category' : 'categories'}`;
    
    const maxCount = Math.max(...categories.map(c => c[1]), 1);
    const colors = ['#EC4899', '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#06B6D4', '#6366F1', '#F472B6', '#A78BFA'];
    
    const chartHTML = categories.length > 0 ? `
        <div class="chart-bar-wrapper" style="max-height: 400px; overflow-y: auto; padding-right: 0.5rem;">
            ${categories.map(([name, count], idx) => `
                <div class="chart-bar-item">
                    <div class="chart-bar-label">${name}</div>
                    <div class="chart-bar-track">
                        <div class="chart-bar-fill" style="width: ${(count / maxCount * 100)}%; background: linear-gradient(90deg, ${colors[idx % colors.length]}, ${colors[idx % colors.length]}aa);">
                            <span class="chart-bar-value">${count}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    ` : '<p style="color: rgba(255,255,255,0.5); text-align: center; padding: 2rem;">No categories available</p>';
    
    document.getElementById('categoryChart').innerHTML = chartHTML;
}

// 2. Borrow Status Distribution
function renderBorrowStatus(borrows) {
    const statusMap = {};
    borrows.forEach(b => {
        statusMap[b.status] = (statusMap[b.status] || 0) + 1;
    });
    
    document.getElementById('borrowTotal').textContent = `${borrows.length} total`;
    
    const statuses = Object.entries(statusMap).sort((a, b) => b[1] - a[1]);
    const maxCount = Math.max(...statuses.map(s => s[1]), 1);
    
    const statusColors = {
        'Borrowed': '#F59E0B',
        'Returned': '#10B981',
        'Overdue': '#EF4444',
        'PendingVerification': '#8B5CF6'
    };
    
    const chartHTML = `
        <div class="chart-bar-wrapper">
            ${statuses.map(([status, count]) => `
                <div class="chart-bar-item">
                    <div class="chart-bar-label">${status}</div>
                    <div class="chart-bar-track">
                        <div class="chart-bar-fill" style="width: ${(count / maxCount * 100)}%; background: linear-gradient(90deg, ${statusColors[status] || '#6366F1'}, ${statusColors[status] || '#6366F1'}aa);">
                            <span class="chart-bar-value">${count}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    document.getElementById('borrowStatusChart').innerHTML = chartHTML || '<p style="color: rgba(255,255,255,0.5); text-align: center;">No borrow records</p>';
}

// 3. Top Borrowed Books
function renderTopBorrowedBooks(books, borrows) {
    const bookBorrowCount = {};
    borrows.forEach(b => {
        // Find book by title since API returns book_title field
        const book = books.find(book => book.title === b.book_title);
        if (book) {
            bookBorrowCount[book.book_id] = (bookBorrowCount[book.book_id] || 0) + 1;
        }
    });
    
    const topBooks = books
        .map(book => ({
            ...book,
            borrowCount: bookBorrowCount[book.book_id] || 0
        }))
        .sort((a, b) => b.borrowCount - a.borrowCount)
        .slice(0, 5);
    
    const listHTML = topBooks.length > 0 ? topBooks.map((book, idx) => {
        const rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : 'rank-other';
        return `
            <div class="top-item">
                <div class="top-item-rank ${rankClass}">${idx + 1}</div>
                <div class="top-item-info">
                    <div class="top-item-title">${book.title}</div>
                    <div class="top-item-subtitle">${book.author}</div>
                </div>
                <div class="top-item-count">${book.borrowCount} 📚</div>
            </div>
        `;
    }).join('') : '<p style="color: rgba(255,255,255,0.5); text-align: center;">No borrowing activity yet</p>';
    
    document.getElementById('topBooksList').innerHTML = listHTML;
}

// 4. Fine Analytics
function renderFineAnalytics(borrows) {
    const totalFines = borrows.reduce((sum, b) => sum + (b.fine_amount || 0), 0);
    const paidFines = borrows.filter(b => b.status === 'RETURNED').reduce((sum, b) => sum + (b.fine_amount || 0), 0);
    const pendingFines = borrows.filter(b => b.status !== 'RETURNED' && b.fine_amount > 0).reduce((sum, b) => sum + (b.fine_amount || 0), 0);
    const borrowsWithFines = borrows.filter(b => b.fine_amount > 0).length;
    
    document.getElementById('fineInsights').textContent = `₹${paidFines} collected`;
    
    const statsHTML = `
        <div class="fine-stat-item">
            <div class="fine-stat-value">₹${totalFines}</div>
            <div class="fine-stat-label">Total Fines</div>
        </div>
        <div class="fine-stat-item">
            <div class="fine-stat-value">₹${paidFines}</div>
            <div class="fine-stat-label">Collected</div>
        </div>
        <div class="fine-stat-item">
            <div class="fine-stat-value">₹${pendingFines}</div>
            <div class="fine-stat-label">Pending</div>
        </div>
        <div class="fine-stat-item">
            <div class="fine-stat-value">${borrowsWithFines}</div>
            <div class="fine-stat-label">Books with Fines</div>
        </div>
    `;
    
    document.getElementById('fineStatsGrid').innerHTML = statsHTML;
}

// 5. Book Availability
function renderAvailability(books) {
    const totalCopies = books.reduce((sum, b) => sum + b.total_copies, 0);
    const availableCopies = books.reduce((sum, b) => sum + b.available_copies, 0);
    const borrowedCopies = totalCopies - availableCopies;
    
    const availabilityRate = totalCopies > 0 ? ((availableCopies / totalCopies) * 100).toFixed(1) : 0;
    document.getElementById('availabilityRate').textContent = `${availabilityRate}%`;
    
    const chartHTML = `
        <div class="availability-item">
            <div class="availability-header">
                <span class="availability-label">Available Copies</span>
                <span class="availability-value">${availableCopies} / ${totalCopies}</span>
            </div>
            <div class="availability-bar">
                <div class="availability-fill" style="width: ${(availableCopies / totalCopies * 100) || 0}%;"></div>
            </div>
        </div>
        <div class="availability-item">
            <div class="availability-header">
                <span class="availability-label">Currently Borrowed</span>
                <span class="availability-value">${borrowedCopies} copies</span>
            </div>
            <div class="availability-bar">
                <div class="availability-fill" style="width: ${(borrowedCopies / totalCopies * 100) || 0}%; background: linear-gradient(90deg, #F59E0B, #FBBF24);"></div>
            </div>
        </div>
    `;
    
    document.getElementById('availabilityChart').innerHTML = chartHTML;
}

// 6. Borrowing Trends
function renderBorrowingTrends(borrows) {
    const now = new Date();
    const thisMonth = borrows.filter(b => {
        const borrowDate = new Date(b.borrowed_date);
        return borrowDate.getMonth() === now.getMonth() && borrowDate.getFullYear() === now.getFullYear();
    }).length;
    
    const lastMonth = borrows.filter(b => {
        const borrowDate = new Date(b.borrowed_date);
        const lastMonthDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        return borrowDate.getMonth() === lastMonthDate.getMonth() && borrowDate.getFullYear() === lastMonthDate.getFullYear();
    }).length;
    
    const overdueBorrows = borrows.filter(b => {
        if (b.status !== 'ACTIVE' && b.status !== 'OVERDUE') return false;
        const dueDate = new Date(b.due_date);
        return dueDate < now;
    }).length;
    
    const avgBorrowDuration = borrows.filter(b => b.status === 'RETURNED' && b.return_date).length > 0
        ? Math.round(borrows.filter(b => b.status === 'RETURNED' && b.return_date).reduce((sum, b) => {
            const borrow = new Date(b.borrowed_date);
            const returned = new Date(b.return_date);
            return sum + Math.floor((returned - borrow) / (1000 * 60 * 60 * 24));
        }, 0) / borrows.filter(b => b.status === 'RETURNED' && b.return_date).length)
        : 0;
    
    const trend = thisMonth > lastMonth ? 'up' : thisMonth < lastMonth ? 'down' : 'neutral';
    const trendSymbol = trend === 'up' ? '📈' : trend === 'down' ? '📉' : '➡️';
    
    document.getElementById('trendIndicator').textContent = `${trendSymbol} This month`;
    
    const trendsHTML = `
        <div class="trend-item">
            <span class="trend-label">This Month</span>
            <div class="trend-value">
                ${thisMonth}
                <span class="trend-indicator ${trend}">${trendSymbol}</span>
            </div>
        </div>
        <div class="trend-item">
            <span class="trend-label">Last Month</span>
            <div class="trend-value">${lastMonth}</div>
        </div>
        <div class="trend-item">
            <span class="trend-label">Overdue Books</span>
            <div class="trend-value">
                ${overdueBorrows}
                ${overdueBorrows > 0 ? '<span class="trend-indicator down">⚠️</span>' : ''}
            </div>
        </div>
        <div class="trend-item">
            <span class="trend-label">Avg. Borrow Duration</span>
            <div class="trend-value">${avgBorrowDuration} days</div>
        </div>
    `;
    
    document.getElementById('trendContainer').innerHTML = trendsHTML;
}

// Global flag to track if book submission is in progress
let isBookSubmissionInProgress = false;

// Prevent navigation during book submission
window.addEventListener('beforeunload', (e) => {
    if (isBookSubmissionInProgress) {
        e.preventDefault();
        e.returnValue = 'Book is being indexed. Leaving this page will cancel the process.';
        return e.returnValue;
    }
});

// Show loading overlay
function showLoadingOverlay(message, subMessage = '') {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.innerHTML = `
            <div class="loading-overlay-content">
                <div class="loading-spinner-large"></div>
                <h3 id="loadingMessage"></h3>
                <p id="loadingSubMessage" class="loading-sub"></p>
                <div class="loading-warning">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <span>Do NOT close, refresh, or navigate away from this page!</span>
                </div>
                <div class="loading-progress">
                    <div class="loading-progress-bar"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingSubMessage').textContent = subMessage;
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
    document.body.style.overflow = '';
}

// Handle book form submission
async function handleBookSubmission(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBookBtn');
    const successMsg = document.getElementById('successMessage');
    const errorMsg = document.getElementById('errorMessage');
    
    // Hide messages
    successMsg.style.display = 'none';
    errorMsg.style.display = 'none';
    
    // Set submission flag and show overlay
    isBookSubmissionInProgress = true;
    const visibility = document.querySelector('input[name="visibility"]:checked').value;
    const loadingMsg = visibility === 'public' 
        ? 'Adding Book & Generating AI Content...'
        : 'Adding Book & RAG Indexing...';
    const subMsg = visibility === 'public'
        ? 'Generating Summary, Q&A, Podcast & RAG Index. This may take 2-3 minutes.'
        : 'Indexing PDF for RAG chat. This may take 30-60 seconds.';
    showLoadingOverlay(loadingMsg, subMsg);
    
    // Disable button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Adding Book...</span>';
    
    try {
        // Get form data
        const formData = new FormData();
        formData.append('title', document.getElementById('bookTitle').value);
        formData.append('author', document.getElementById('bookAuthor').value);
        formData.append('total_copies', document.getElementById('totalCopies').value);
        
        // Add categories (comma-separated string) - always send field (backend requires it)
        const categories = document.getElementById('bookCategories').value.trim();
        formData.append('categories', categories || '');
        
        formData.append('pdf_file', document.getElementById('pdfFile').files[0]);
        formData.append('cover_image', document.getElementById('coverImage').files[0]);
        
        // Determine endpoint based on visibility
        const visibility = document.querySelector('input[name="visibility"]:checked').value;
        const endpoint = visibility === 'public' 
            ? `${API_BASE_URL}/admin/books/`
            : `${API_BASE_URL}/admin/books/quick-add`;
        
        // Submit form
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            const visibility = document.querySelector('input[name="visibility"]:checked').value;
            successMsg.textContent = visibility === 'public' 
                ? `✓ Book added successfully! AI content (Summary, Q&A, Podcast) is being generated. This may take 2-3 minutes.`
                : `✓ Book added successfully with RAG indexing! Chat functionality enabled. (AI content generation skipped)`;
            successMsg.style.display = 'block';
            
            // Reset form
            document.getElementById('addBookForm').reset();
            document.querySelectorAll('.file-name').forEach(el => {
                el.textContent = el.closest('.file-input-wrapper').querySelector('input').accept.includes('pdf') 
                    ? 'Choose PDF file' 
                    : 'Choose image file';
            });
            
            // Scroll to message
            successMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
        } else {
            const error = await response.json();
            errorMsg.textContent = `✗ Error: ${error.detail || 'Failed to add book'}`;
            errorMsg.style.display = 'block';
            errorMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
    } catch (error) {
        console.error('Error adding book:', error);
        errorMsg.textContent = `✗ Network error: ${error.message}`;
        errorMsg.style.display = 'block';
        errorMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } finally {
        // Clear submission flag and hide overlay
        isBookSubmissionInProgress = false;
        hideLoadingOverlay();
        
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <span>Add Book</span>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 4L13 10L7 16" stroke="currentColor" stroke-width="2"/>
            </svg>
        `;
    }
}

// Reset form
function resetForm() {
    document.getElementById('addBookForm').reset();
    document.getElementById('successMessage').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
    document.querySelectorAll('.file-name').forEach(el => {
        el.textContent = el.closest('.file-input-wrapper').querySelector('input').accept.includes('pdf') 
            ? 'Choose PDF file' 
            : 'Choose image file';
    });
}

// Load all books
async function loadAllBooks() {
    const container = document.getElementById('allBooksContainer');
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/books/`, {
            headers: getAuthHeaders()
        });
        const books = await response.json();
        
        if (books.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" stroke-width="2"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>No books found</h3>
                    <p>Add your first book to get started</p>
                </div>
            `;
            return;
        }
        
        const booksHTML = `
            <div class="books-grid">
                ${books.map(book => `
                    <div class="book-card">
                        ${book.cover_image ? `
                            <div class="book-cover">
                                <img src="${API_BASE_URL}/${book.cover_image.replace(/\\/g, '/')}" alt="${book.title}" onerror="this.style.display='none'">
                            </div>
                        ` : ''}
                        <div class="book-info">
                            <h3>${book.title}</h3>
                            <p class="book-author"><strong>Author:</strong> ${book.author}</p>
                            <p><strong>Total Copies:</strong> ${book.total_copies}</p>
                            <p><strong>Available:</strong> ${book.available_copies}</p>
                            <div class="book-meta">
                                <span>ID: ${book.book_id}</span>
                                <span class="availability-badge ${book.available_copies > 0 ? 'available' : 'unavailable'}">
                                    ${book.available_copies > 0 ? '✓ Available' : '✗ Not Available'}
                                </span>
                            </div>
                            <div class="rag-status">
                                <span class="rag-badge ${book.rag_indexed ? 'rag-indexed' : 'rag-not-indexed'}">
                                    ${book.rag_indexed ? '✓ RAG Indexed' : '⚠ Not Indexed'}
                                </span>
                            </div>
                            <button class="delete-book-btn" onclick="deleteBook(${book.book_id}, '${book.title.replace(/'/g, "\\'")}')">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                    <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                                Delete
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.innerHTML = booksHTML;
        
    } catch (error) {
        console.error('Error loading books:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>Error loading books</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Delete book function
async function deleteBook(bookId, bookTitle) {
    if (!confirm(`Are you sure you want to delete "${bookTitle}"?\n\nThis action cannot be undone. All associated data (PDF, cover image, summaries, Q&A, audio) will be permanently deleted.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/books/${bookId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            alert(`Successfully deleted "${bookTitle}"`);
            loadAllBooks(); // Refresh the books list
            loadStats(); // Update overview stats
        } else {
            const error = await response.json();
            alert(`Failed to delete book: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting book:', error);
        alert(`Error deleting book: ${error.message}`);
    }
}

// Load borrow records
async function loadBorrowRecords() {
    const container = document.getElementById('borrowRecordsContainer');
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/borrow/admin/all-borrows`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();
        const records = data.borrow_records || [];
        
        if (records.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                        <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="2"/>
                        <path d="M16 16l5 5" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>No borrow records found</h3>
                    <p>No books have been borrowed yet</p>
                </div>
            `;
            return;
        }
        
        // Calculate statistics
        const totalBorrows = records.length;
        const activeBorrows = records.filter(r => r.status === 'ACTIVE' || r.status === 'OVERDUE').length;
        const returned = records.filter(r => r.status === 'RETURNED').length;
        const totalFines = records.reduce((sum, r) => sum + (r.fine_amount || 0), 0);
        
        const statsHTML = `
            <div class="borrow-stats-grid">
                <div class="borrow-stat-card">
                    <div class="borrow-stat-icon" style="background: rgba(99, 102, 241, 0.15);">📚</div>
                    <div>
                        <div class="borrow-stat-value">${totalBorrows}</div>
                        <div class="borrow-stat-label">Total Borrows</div>
                    </div>
                </div>
                <div class="borrow-stat-card">
                    <div class="borrow-stat-icon" style="background: rgba(245, 158, 11, 0.15);">📖</div>
                    <div>
                        <div class="borrow-stat-value">${activeBorrows}</div>
                        <div class="borrow-stat-label">Currently Borrowed</div>
                    </div>
                </div>
                <div class="borrow-stat-card">
                    <div class="borrow-stat-icon" style="background: rgba(16, 185, 129, 0.15);">✅</div>
                    <div>
                        <div class="borrow-stat-value">${returned}</div>
                        <div class="borrow-stat-label">Returned</div>
                    </div>
                </div>
                <div class="borrow-stat-card">
                    <div class="borrow-stat-icon" style="background: rgba(236, 72, 153, 0.15);">💰</div>
                    <div>
                        <div class="borrow-stat-value">₹${totalFines}</div>
                        <div class="borrow-stat-label">Total Fines</div>
                    </div>
                </div>
            </div>
        `;
        
        const tableHTML = `
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Student Name</th>
                            <th>Email</th>
                            <th>Book Title</th>
                            <th>Author</th>
                            <th>Borrowed Date</th>
                            <th>Due Date</th>
                            <th>Return Date</th>
                            <th>Fine</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${records.map(record => {
                            const isOverdue = !record.return_date && new Date(record.due_date) < new Date();
                            const statusClass = record.status === 'RETURNED' ? 'returned' : 
                                              record.status === 'OVERDUE' || isOverdue ? 'overdue' : 'active';
                            const statusText = record.status === 'RETURNED' ? 'RETURNED' : 
                                             isOverdue ? 'OVERDUE' : 'ACTIVE';
                            return `
                            <tr>
                                <td><strong>#${record.borrow_id}</strong></td>
                                <td>${record.user_name}</td>
                                <td><small>${record.user_email}</small></td>
                                <td><strong>${record.book_title}</strong></td>
                                <td>${record.author}</td>
                                <td>${new Date(record.borrowed_date).toLocaleDateString('en-IN')}</td>
                                <td>${new Date(record.due_date).toLocaleDateString('en-IN')}</td>
                                <td>${record.return_date ? new Date(record.return_date).toLocaleDateString('en-IN') : '<span style="color: rgba(255,255,255,0.5);">Not Returned</span>'}</td>
                                <td>${record.fine_amount > 0 ? `<strong style="color: #EC4899;">₹${record.fine_amount}</strong>` : '-'}</td>
                                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                            </tr>
                        `}).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = statsHTML + tableHTML;
        
    } catch (error) {
        console.error('Error loading borrow records:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>Error loading records</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Load pending verifications
async function loadPendingVerifications() {
    const container = document.getElementById('verifyReturnsContainer');
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/borrow/admin/pending-verifications`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();
        const verifications = data.pending_verifications || [];
        
        if (verifications.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                        <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2"/>
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>No pending verifications</h3>
                    <p>All fine payments have been verified</p>
                </div>
            `;
            return;
        }
        
        const tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Student Name</th>
                        <th>Email</th>
                        <th>Book Title</th>
                        <th>Borrowed Date</th>
                        <th>Return Date</th>
                        <th>Days Late</th>
                        <th>Fine Amount</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${verifications.map(record => `
                        <tr>
                            <td>${record.student_name}</td>
                            <td>${record.student_email}</td>
                            <td>${record.book_title}</td>
                            <td>${new Date(record.borrowed_date).toLocaleDateString()}</td>
                            <td>${new Date(record.return_date).toLocaleDateString()}</td>
                            <td>${record.days_late} days</td>
                            <td>₹${record.fine_amount}</td>
                            <td>
                                <button class="btn-primary" onclick="verifyReturn(${record.borrow_id})" style="padding: 0.5rem 1rem; font-size: 0.875rem;">
                                    Verify Payment
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Error loading pending verifications:', error);
        container.innerHTML = `
            <div class="empty-state">
                <h3>Error loading verifications</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// Verify return and fine payment
async function verifyReturn(borrowId) {
    if (!confirm('Are you sure you want to verify this fine payment?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/borrow/admin/verify/${borrowId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                fine_paid: true
            })
        });
        
        if (response.ok) {
            alert('✓ Fine payment verified successfully!');
            loadPendingVerifications(); // Reload the list
            loadOverviewStats(); // Update stats
        } else {
            const error = await response.json();
            alert(`✗ Error: ${error.detail || 'Failed to verify payment'}`);
        }
        
    } catch (error) {
        console.error('Error verifying return:', error);
        alert(`✗ Network error: ${error.message}`);
    }
}
