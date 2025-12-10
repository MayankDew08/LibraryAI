const API_BASE_URL = 'http://127.0.0.1:8000';
let currentBookId = null;
let studentEmail = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Get student info from localStorage
    const studentData = JSON.parse(localStorage.getItem('student') || '{}');
    studentEmail = studentData.email || 'student@example.com';
    
    // Update student name in header
    if (studentData.name) {
        document.getElementById('studentName').textContent = studentData.name;
        document.getElementById('studentAvatar').textContent = studentData.name.charAt(0).toUpperCase();
    }
    
    // Setup navigation
    setupNavigation();
    
    // Setup search
    setupSearch();
    
    // Setup tabs
    setupTabs();
    
    // Load initial library
    loadLibrary();
});

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = link.getAttribute('data-view');
            switchView(view);
        });
    });
}

function switchView(view) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-view="${view}"]`).classList.add('active');
    
    // Update views
    document.querySelectorAll('.view-content').forEach(v => {
        v.classList.remove('active');
    });
    document.getElementById(`${view}-view`).classList.add('active');
    
    // Load data
    if (view === 'library') {
        loadLibrary();
    } else if (view === 'my-books') {
        loadMyBooks();
    }
}

// Search
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length === 0) {
            loadLibrary();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            searchBooks(query);
        }, 500);
    });
}

async function searchBooks(title) {
    try {
        const response = await fetch(`${API_BASE_URL}/student/books/search?title=${encodeURIComponent(title)}`);
        const books = await response.json();
        displayBooks(books);
    } catch (error) {
        console.error('Error searching books:', error);
    }
}

// Load Library
async function loadLibrary() {
    const container = document.getElementById('booksContainer');
    container.innerHTML = '<div class="content-loading"><div class="spinner"></div><p>Loading library...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/student/books/`);
        const books = await response.json();
        displayBooks(books);
    } catch (error) {
        console.error('Error loading library:', error);
        container.innerHTML = '<div class="empty-state"><h3>Error loading library</h3><p>' + error.message + '</p></div>';
    }
}

function displayBooks(books) {
    const container = document.getElementById('booksContainer');
    
    if (books.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" stroke-width="2"/>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" stroke-width="2"/>
                </svg>
                <h3>No books found</h3>
                <p>Try a different search term</p>
            </div>
        `;
        return;
    }
    
    const booksHTML = books.map(book => `
        <div class="book-card" onclick="openBookDetail(${book.book_id})">
            ${book.cover_image ? `
                <div class="book-cover">
                    <img src="${API_BASE_URL}/${book.cover_image.replace(/\\/g, '/')}" alt="${book.title}">
                </div>
            ` : ''}
            <div class="book-info">
                <h3>${book.title}</h3>
                <p class="book-author">${book.author}</p>
                <p><strong>Available:</strong> ${book.available_copies} / ${book.total_copies}</p>
                <span class="availability-badge ${book.available_copies > 0 ? 'available' : 'unavailable'}">
                    ${book.available_copies > 0 ? '✓ Available' : '✗ Unavailable'}
                </span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = booksHTML;
}

// Book Detail Modal
async function openBookDetail(bookId) {
    currentBookId = bookId;
    const modal = document.getElementById('bookDetailModal');
    modal.classList.add('active');
    
    try {
        // Fetch book details
        const response = await fetch(`${API_BASE_URL}/student/books/`);
        const books = await response.json();
        const book = books.find(b => b.book_id === bookId);
        
        if (!book) return;
        
        // Update modal header
        document.getElementById('detailTitle').textContent = book.title;
        document.getElementById('detailAuthor').textContent = book.author;
        document.getElementById('detailAvailability').textContent = `Available: ${book.available_copies} / ${book.total_copies}`;
        
        if (book.cover_image) {
            document.getElementById('detailCoverImage').src = `${API_BASE_URL}/${book.cover_image.replace(/\\/g, '/')}`;
        }
        
        // Check if user has borrowed this book
        let hasBorrowed = false;
        try {
            const borrowsResponse = await fetch(`${API_BASE_URL}/borrow/user/email/${studentEmail}`);
            const borrows = await borrowsResponse.json();
            hasBorrowed = borrows.some(b => b.book_title === book.title && b.status === 'Borrowed');
        } catch (error) {
            console.error('Error checking borrow status:', error);
        }
        
        // Update borrow and return buttons
        const borrowBtn = document.getElementById('borrowBookBtn');
        const returnBtn = document.getElementById('returnBookBtn');
        
        if (hasBorrowed) {
            borrowBtn.style.display = 'none';
            returnBtn.style.display = 'block';
        } else {
            returnBtn.style.display = 'none';
            borrowBtn.style.display = 'block';
            
            if (book.available_copies > 0) {
                borrowBtn.disabled = false;
                borrowBtn.textContent = 'Borrow Book';
            } else {
                borrowBtn.disabled = true;
                borrowBtn.textContent = 'Not Available';
            }
        }
        
        // Load PDF
        loadPDF(bookId);
        
        // Switch to first tab
        switchTab('pdf');
    } catch (error) {
        console.error('Error loading book details:', error);
    }
}

function closeBookDetail() {
    document.getElementById('bookDetailModal').classList.remove('active');
    currentBookId = null;
    
    // Clear chat messages
    document.getElementById('chatMessages').innerHTML = '';
}

// Tabs
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            switchTab(tab);
        });
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load content based on tab
    if (tabName === 'summary') {
        loadSummary(currentBookId);
    } else if (tabName === 'qa') {
        loadQA(currentBookId);
    } else if (tabName === 'audio') {
        loadAudio(currentBookId);
    }
}

// Load PDF
function loadPDF(bookId) {
    fetch(`${API_BASE_URL}/student/books/`)
        .then(res => res.json())
        .then(books => {
            const book = books.find(b => b.book_id === bookId);
            if (book && book.pdf_url) {
                document.getElementById('pdfEmbed').src = `${API_BASE_URL}/${book.pdf_url.replace(/\\/g, '/')}`;
            }
        });
}

// Load Summary
async function loadSummary(bookId) {
    const loading = document.querySelector('#summary-tab .content-loading');
    const content = document.getElementById('summaryContent');
    
    loading.style.display = 'flex';
    content.classList.remove('loaded');
    
    try {
        const response = await fetch(`${API_BASE_URL}/student/books/${bookId}/summary`);
        
        if (!response.ok) {
            throw new Error('Summary not available for this book');
        }
        
        const data = await response.json();
        
        if (data.summary_text) {
            // Display text with preserved formatting
            const textContent = document.createElement('div');
            textContent.className = 'formatted-content';
            textContent.style.whiteSpace = 'pre-wrap';
            textContent.textContent = data.summary_text;
            content.innerHTML = '';
            content.appendChild(textContent);
            content.classList.add('loaded');
        }
        loading.style.display = 'none';
    } catch (error) {
        console.error('Error loading summary:', error);
        content.innerHTML = `
            <div class="confidential-notice">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                    <path d="M12 15v2m0-6v2m0-10C7 3 3 7 3 12s4 9 9 9 9-4 9-9-4-9-9-9z" stroke="currentColor" stroke-width="2"/>
                </svg>
                <h3>Content Not Available</h3>
                <p>This book was uploaded as confidential or content hasn't been generated yet. Summary is not available.</p>
            </div>
        `;
        content.classList.add('loaded');
        loading.style.display = 'none';
    }
}

// Load Q&A
async function loadQA(bookId) {
    const loading = document.querySelector('#qa-tab .content-loading');
    const content = document.getElementById('qaContent');
    
    loading.style.display = 'flex';
    content.classList.remove('loaded');
    
    try {
        const response = await fetch(`${API_BASE_URL}/student/books/${bookId}/qa`);
        
        if (!response.ok) {
            throw new Error('Q&A not available for this book');
        }
        
        const data = await response.json();
        
        if (data.qa_json) {
            // Parse Q&A text into structured format
            const qaHTML = parseQAText(data.qa_json);
            content.innerHTML = qaHTML;
            content.classList.add('loaded');
        } else {
            content.innerHTML = `
                <div class="confidential-notice">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                        <path d="M12 15v2m0-6v2m0-10C7 3 3 7 3 12s4 9 9 9 9-4 9-9-4-9-9-9z" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>Confidential Content</h3>
                    <p>This book was uploaded as confidential. Q&A is not available.</p>
                </div>
            `;
            content.classList.add('loaded');
        }
        loading.style.display = 'none';
    } catch (error) {
        console.error('Error loading Q&A:', error);
        content.innerHTML = `
            <div class="confidential-notice">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                    <path d="M12 15v2m0-6v2m0-10C7 3 3 7 3 12s4 9 9 9 9-4 9-9-4-9-9-9z" stroke="currentColor" stroke-width="2"/>
                </svg>
                <h3>Content Not Available</h3>
                <p>This book was uploaded as confidential or content hasn't been generated yet. Q&A is not available.</p>
            </div>
        `;
        content.classList.add('loaded');
        loading.style.display = 'none';
    }
}

function parseQAText(qaText) {
    if (!qaText) return '';
    
    // Try to parse as JSON array first
    try {
        const qaArray = JSON.parse(qaText);
        if (Array.isArray(qaArray)) {
            return qaArray.map(qa => {
                const question = qa.question || qa.Q || '';
                const answer = qa.answer || qa.A || '';
                return `
                    <div class="qa-item">
                        <div class="question"><strong>Q:</strong> ${escapeHtml(question)}</div>
                        <div class="answer"><strong>A:</strong> ${escapeHtml(answer)}</div>
                    </div>
                `;
            }).join('');
        }
    } catch (e) {
        // Not JSON, parse as text
    }
    
    // Parse text format - just display as-is with pre-wrap
    const lines = qaText.split('\n');
    let html = '';
    let currentQ = '';
    let currentA = '';
    let inAnswer = false;
    
    lines.forEach(line => {
        line = line.trim();
        if (!line) return;
        
        // Check for question markers
        if (line.match(/^(Q\d*:|Question\s*\d*:)/i)) {
            // Save previous Q&A pair
            if (currentQ && currentA) {
                html += `
                    <div class="qa-item">
                        <div class="question"><strong>Q:</strong> ${escapeHtml(currentQ)}</div>
                        <div class="answer"><strong>A:</strong> ${escapeHtml(currentA)}</div>
                    </div>
                `;
            }
            currentQ = line.replace(/^(Q\d*:|Question\s*\d*:)/i, '').trim();
            currentA = '';
            inAnswer = false;
        } 
        // Check for answer markers
        else if (line.match(/^(A\d*:|Answer\s*\d*:)/i)) {
            currentA = line.replace(/^(A\d*:|Answer\s*\d*:)/i, '').trim();
            inAnswer = true;
        } 
        // Continue previous answer
        else if (inAnswer && currentA) {
            currentA += ' ' + line;
        }
        // Continue previous question
        else if (currentQ && !inAnswer) {
            currentQ += ' ' + line;
        }
    });
    
    // Add last Q&A pair
    if (currentQ && currentA) {
        html += `
            <div class="qa-item">
                <div class="question"><strong>Q:</strong> ${escapeHtml(currentQ)}</div>
                <div class="answer"><strong>A:</strong> ${escapeHtml(currentA)}</div>
            </div>
        `;
    }
    
    // If no Q&A pairs found, just display as pre-formatted text
    if (!html) {
        html = `<div class="formatted-content" style="white-space: pre-wrap;">${escapeHtml(qaText)}</div>`;
    }
    
    return html;
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load Audio
async function loadAudio(bookId) {
}

// Load Audio
async function loadAudio(bookId) {
    const loading = document.querySelector('#audio-tab .content-loading');
    const content = document.getElementById('audioContent');
    
    loading.style.display = 'flex';
    content.classList.remove('loaded');
    
    try {
        const response = await fetch(`${API_BASE_URL}/student/books/${bookId}/audio`);
        
        if (!response.ok) {
            throw new Error('Audio not available for this book');
        }
        
        const data = await response.json();
        
        if (data.audio_url) {
            content.innerHTML = `
                <h3 style="color: var(--student-primary); margin-bottom: 1rem;">🎧 Podcast Audio</h3>
                <audio controls>
                    <source src="${API_BASE_URL}/${data.audio_url.replace(/\\/g, '/')}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            `;
            content.classList.add('loaded');
        } else {
            content.innerHTML = `
                <div class="confidential-notice">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                        <path d="M12 15v2m0-6v2m0-10C7 3 3 7 3 12s4 9 9 9 9-4 9-9-4-9-9-9z" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>Confidential Content</h3>
                    <p>This book was uploaded as confidential. Podcast audio is not available.</p>
                </div>
            `;
            content.classList.add('loaded');
        }
        loading.style.display = 'none';
    } catch (error) {
        console.error('Error loading audio:', error);
        content.innerHTML = `
            <div class="confidential-notice">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                    <path d="M12 15v2m0-6v2m0-10C7 3 3 7 3 12s4 9 9 9 9-4 9-9-4-9-9-9z" stroke="currentColor" stroke-width="2"/>
                </svg>
                <h3>Content Not Available</h3>
                <p>This book was uploaded as confidential or content hasn't been generated yet. Podcast audio is not available.</p>
            </div>
        `;
        content.classList.add('loaded');
        loading.style.display = 'none';
    }
}

// Chat
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    
    if (!question || !currentBookId) return;
    
    // Add user message
    addChatMessage(question, 'user');
    input.value = '';
    
    // Add loading message
    const loadingId = Date.now();
    addChatMessage('Thinking...', 'bot', loadingId);
    
    try {
        const response = await fetch(`${API_BASE_URL}/rag/books/${currentBookId}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                num_chunks: 5
            })
        });
        
        // Check if response is ok
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get response');
        }
        
        const data = await response.json();
        
        // Remove loading message
        document.querySelector(`[data-id="${loadingId}"]`)?.remove();
        
        // Add bot response
        if (data.answer) {
            // Check if answer indicates missing content
            if (data.answer.includes('Book Content') && data.answer.includes('empty')) {
                addChatMessage(
                    '⚠️ This book hasn\'t been properly indexed yet.\n\n' +
                    'The book PDF may not contain extractable text, or it needs to be re-uploaded.\n\n' +
                    'Please contact the administrator or try another book.',
                    'bot'
                );
            } else {
                addChatMessage(data.answer, 'bot');
            }
        } else if (data.error) {
            addChatMessage('⚠️ ' + data.error, 'bot');
        } else {
            addChatMessage('Sorry, I could not find an answer to your question.', 'bot');
        }
    } catch (error) {
        console.error('Error sending chat message:', error);
        document.querySelector(`[data-id="${loadingId}"]`)?.remove();
        addChatMessage('Error: Could not get a response. Please try again.', 'bot');
    }
}

function addChatMessage(message, type, id = null) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    if (id) messageDiv.setAttribute('data-id', id);
    
    // Display all messages as plain text with preserved formatting
    messageDiv.style.whiteSpace = 'pre-wrap';
    messageDiv.textContent = message;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle Enter key in chat
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    chatInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
});

// Borrow Book
async function borrowBook() {
    if (!currentBookId || !studentEmail) {
        alert('Please log in to borrow books');
        return;
    }
    
    const btn = document.getElementById('borrowBookBtn');
    btn.disabled = true;
    btn.textContent = 'Borrowing...';
    
    try {
        // Get book title
        const response = await fetch(`${API_BASE_URL}/student/books/`);
        const books = await response.json();
        const book = books.find(b => b.book_id === currentBookId);
        
        if (!book) {
            throw new Error('Book not found');
        }
        
        const borrowResponse = await fetch(`${API_BASE_URL}/borrow/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                book_title: book.title,
                user_email: studentEmail
            })
        });
        
        if (borrowResponse.ok) {
            alert('✓ Book borrowed successfully!');
            closeBookDetail();
            loadLibrary(); // Refresh library
        } else {
            const error = await borrowResponse.json();
            alert('✗ Error: ' + (error.detail || 'Failed to borrow book'));
        }
    } catch (error) {
        console.error('Error borrowing book:', error);
        alert('✗ Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Borrow Book';
    }
}

// Return Book
async function returnBook() {
    if (!currentBookId || !studentEmail) {
        alert('Please log in to return books');
        return;
    }
    
    const btn = document.getElementById('returnBookBtn');
    btn.disabled = true;
    btn.textContent = 'Returning...';
    
    try {
        // Get book title
        const response = await fetch(`${API_BASE_URL}/student/books/`);
        const books = await response.json();
        const book = books.find(b => b.book_id === currentBookId);
        
        if (!book) {
            throw new Error('Book not found');
        }
        
        const returnResponse = await fetch(`${API_BASE_URL}/borrow/student/return`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                book_title: book.title,
                user_email: studentEmail
            })
        });
        
        if (returnResponse.ok) {
            const result = await returnResponse.json();
            alert('✓ ' + result.message);
            closeBookDetail();
            loadLibrary(); // Refresh library
        } else {
            const error = await returnResponse.json();
            alert('✗ Error: ' + (error.detail || 'Failed to return book'));
        }
    } catch (error) {
        console.error('Error returning book:', error);
        alert('✗ Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Return Book';
    }
}

// Load My Books
async function loadMyBooks() {
    const container = document.getElementById('myBooksContainer');
    container.innerHTML = '<div class="content-loading"><div class="spinner"></div><p>Loading your books...</p></div>';
    
    if (!studentEmail) {
        container.innerHTML = '<div class="empty-state"><h3>Please log in</h3><p>You need to log in to view your borrowed books</p></div>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/borrow/user/email/${studentEmail}`);
        const borrows = await response.json();
        
        if (borrows.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" stroke-width="2"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>No borrowed books</h3>
                    <p>You haven't borrowed any books yet</p>
                </div>
            `;
            return;
        }
        
        const tableHTML = `
            <table class="borrow-table">
                <thead>
                    <tr>
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
                    ${borrows.map(borrow => `
                        <tr>
                            <td>${borrow.book_title}</td>
                            <td>${borrow.author}</td>
                            <td>${new Date(borrow.borrowed_date).toLocaleDateString()}</td>
                            <td>${new Date(borrow.due_date).toLocaleDateString()}</td>
                            <td>${borrow.return_date ? new Date(borrow.return_date).toLocaleDateString() : '-'}</td>
                            <td>${borrow.fine_amount > 0 ? '₹' + borrow.fine_amount : '-'}</td>
                            <td><span class="status-badge ${borrow.status.toLowerCase()}">${borrow.status}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
    } catch (error) {
        console.error('Error loading borrowed books:', error);
        container.innerHTML = `<div class="empty-state"><h3>Error loading books</h3><p>${error.message}</p></div>`;
    }
}
