const API_BASE_URL = 'http://127.0.0.1:8000';

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
document.addEventListener('DOMContentLoaded', () => {
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
        const booksResponse = await fetch(`${API_BASE_URL}/admin/books/`);
        const books = await booksResponse.json();
        document.getElementById('totalBooks').textContent = books.length || 0;
        
        // Fetch borrow records
        const borrowsResponse = await fetch(`${API_BASE_URL}/borrow/admin/all-borrows`);
        const borrowsData = await borrowsResponse.json();
        const borrows = borrowsData.borrow_records || [];
        
        // Count active borrows
        const activeBorrows = borrows.filter(b => b.status === 'Borrowed').length;
        document.getElementById('activeBorrows').textContent = activeBorrows;
        
        // Calculate pending fines
        const pendingFines = borrows
            .filter(b => b.fine_amount > 0 && b.status !== 'Returned')
            .reduce((sum, b) => sum + b.fine_amount, 0);
        document.getElementById('pendingFines').textContent = `₹${pendingFines}`;
        
        // Fetch pending verifications
        const verifyResponse = await fetch(`${API_BASE_URL}/borrow/admin/pending-verifications`);
        const verifyData = await verifyResponse.json();
        const verifications = verifyData.pending_verifications || [];
        document.getElementById('pendingVerifications').textContent = verifications.length || 0;
        
    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
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
    
    // Disable button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Adding Book...</span>';
    
    try {
        // Get form data
        const formData = new FormData();
        formData.append('title', document.getElementById('bookTitle').value);
        formData.append('author', document.getElementById('bookAuthor').value);
        formData.append('total_copies', document.getElementById('totalCopies').value);
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
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            successMsg.textContent = visibility === 'public' 
                ? `✓ Book added successfully! Summary, Q&A, and podcast are being generated.`
                : `✓ Book added successfully! RAG indexing completed.`;
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
        const response = await fetch(`${API_BASE_URL}/admin/books/`);
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

// Load borrow records
async function loadBorrowRecords() {
    const container = document.getElementById('borrowRecordsContainer');
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/borrow/admin/all-borrows`);
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
        
        const tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
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
                    ${records.map(record => `
                        <tr>
                            <td>${record.user_name}</td>
                            <td>${record.user_email}</td>
                            <td>${record.book_title}</td>
                            <td>${record.author}</td>
                            <td>${new Date(record.borrowed_date).toLocaleDateString()}</td>
                            <td>${new Date(record.due_date).toLocaleDateString()}</td>
                            <td>${record.return_date ? new Date(record.return_date).toLocaleDateString() : '-'}</td>
                            <td>${record.fine_amount > 0 ? `₹${record.fine_amount}` : '-'}</td>
                            <td><span class="status-badge ${record.status.toLowerCase()}">${record.status}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
        
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
        const response = await fetch(`${API_BASE_URL}/borrow/admin/pending-verifications`);
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
                'Content-Type': 'application/json'
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
