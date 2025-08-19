// Kütüphane Yönetim Sistemi - JavaScript
class LibraryManager {
    constructor() {
        // API URL'ini dinamik olarak al
        this.apiBaseUrl = window.location.origin || 'http://127.0.0.1:8000';
        this.authToken = null;
        this.currentUser = null;
        this.currentRole = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadBooks();
    }

    bindEvents() {
        // Auth
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        if (loginBtn) loginBtn.addEventListener('click', () => this.login());
        if (registerBtn) registerBtn.addEventListener('click', () => this.register());
        if (logoutBtn) logoutBtn.addEventListener('click', () => this.logout());

        // Kitap ekleme
        document.getElementById('addBookBtn').addEventListener('click', () => {
            this.addBook();
        });

        // Kitap arama
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.searchBook();
        });

        // Yenile butonu
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadBooks();
        });

        // Enter tuşu ile kitap ekleme
        const addIsbnEl = document.getElementById('addIsbnInput');
        addIsbnEl && addIsbnEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.addBook();
            }
        });

        // Enter tuşu ile kitap arama
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchBook();
            }
        });

        // Enter ile güncelleme (başlık/yazar alanlarında)
        const editTitle = document.getElementById('updateTitleInput');
        const editAuthor = document.getElementById('updateAuthorInput');
        if (editTitle) editTitle.addEventListener('keypress', (e) => { if (e.key === 'Enter') { this.updateBook(); } });
        if (editAuthor) editAuthor.addEventListener('keypress', (e) => { if (e.key === 'Enter') { this.updateBook(); } });

        // Modal kapatma
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        // Modal dışına tıklama
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });

        // ESC tuşu ile modal kapatma
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // User panel events
        const userAddBookBtn = document.getElementById('userAddBookBtn');
        const userRefreshBtn = document.getElementById('userRefreshBtn');
        const userReadRefreshBtn = document.getElementById('userReadRefreshBtn');
        if (userAddBookBtn) userAddBookBtn.addEventListener('click', () => this.userAddBook());
        if (userRefreshBtn) userRefreshBtn.addEventListener('click', () => { this.loadUserToRead(); this.loadUserReadBooks(); });
        if (userReadRefreshBtn) userReadRefreshBtn.addEventListener('click', () => this.loadUserReadBooks());

        // Kütüphane arama alanı kaldırıldı (mevcut arama bölümü kullanılıyor)

        const updateBookBtn = document.getElementById('updateBookBtn');
        if (updateBookBtn) updateBookBtn.addEventListener('click', () => this.updateBook());
    }

    // Kitap ekleme
    async addBook() {
        const isbnInput = document.getElementById('addIsbnInput');
        const isbn = isbnInput.value.trim();

        if (!isbn) {
            this.showStatus('Lütfen bir ISBN numarası girin.', 'error', 'addBookStatus');
            return;
        }

        // ISBN formatını kontrol et
        const cleanIsbn = isbn.replace(/[-.\s_]/g, '');
        if (cleanIsbn.length < 10) {
            this.showStatus('Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.', 'error');
            return;
        }

        try {
            this.showStatus('Kitap bilgileri Open Library API\'den çekiliyor...', 'info', 'addBookStatus');
            
            // Admin varsa admin endpointi kullanalım, aksi halde normal endpoint (eski davranış)
            const endpoint = this.currentRole === 'admin' ? '/admin/books' : '/books';
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(this.authToken ? { 'Authorization': `Bearer ${this.authToken}` } : {}),
                },
                body: JSON.stringify({ isbn: isbn })
            });

            const data = await response.json();

            if (response.ok) {
                this.showStatus(`✓ Kitap başarıyla eklendi: ${data.title} by ${data.author}`, 'success', 'addBookStatus');
                isbnInput.value = '';
                setTimeout(() => this.loadBooks(), 200); // Küçük bir gecikme ile kitapları yenile
            } else {
                this.showStatus(`❌ ${data.detail}`, 'error', 'addBookStatus');
            }
        } catch (error) {
            console.error('Kitap ekleme hatası:', error);
            this.showStatus('❌ Kitap eklenirken bir hata oluştu. Lütfen tekrar deneyin.', 'error', 'addBookStatus');
        }
    }

    // Kitap arama
    async searchBook() {
        const searchInput = document.getElementById('searchInput');
        const isbn = searchInput.value.trim();
        const resultDiv = document.getElementById('searchResult');

        if (!isbn) {
            this.showStatus('Lütfen bir ISBN numarası girin.', 'error');
            return;
        }

        // ISBN formatını kontrol et
        const cleanIsbn = isbn.replace(/[-.\s_]/g, '');
        if (cleanIsbn.length < 10) {
            this.showStatus('Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/books/${cleanIsbn}`);
            const data = await response.json();

            if (response.ok) {
                this.displaySearchResult(data);
            } else {
                this.showStatus(`❌ ${data.detail}`, 'error');
                resultDiv.style.display = 'none';
            }
        } catch (error) {
            console.error('Kitap arama hatası:', error);
            this.showStatus('❌ Kitap aranırken bir hata oluştu. Lütfen tekrar deneyin.', 'error');
            resultDiv.style.display = 'none';
        }
    }

    // Arama sonucunu göster
    displaySearchResult(book) {
        const resultDiv = document.getElementById('searchResult');
        const adminActions = this.currentRole === 'admin' ? `
            <div class="book-actions">
                <button class="btn btn-small" onclick="libraryManager.prefillEditForm('${book.isbn}','${encodeURIComponent(book.title)}','${encodeURIComponent(book.author)}')">
                    <i class="fas fa-pen"></i> Düzenle
                </button>
                <button class="btn btn-small btn-danger" onclick="libraryManager.showDeleteModal('${book.isbn}', '${book.title}', '${book.author}')">
                    <i class="fas fa-trash"></i> Sil
                </button>
            </div>` : '';
        resultDiv.innerHTML = `
            <div class="book-card">
                <div class="book-header">
                    <div class="book-icon">
                        <i class="fas fa-book"></i>
                    </div>
                    <h3 class="book-title">${book.title}</h3>
                </div>
                <div class="book-details">
                    <div class="book-author">
                        <span>${book.author}</span>
                    </div>
                    <div class="book-isbn">
                        <span>${book.isbn}</span>
                    </div>
                </div>
                ${adminActions}
            </div>`;
        resultDiv.style.display = 'block';
        resultDiv.classList.add('show');
    }

    // Kitapları yükle
    async loadBooks() {
        const booksListDiv = document.getElementById('booksList');
        // Kitaplar yüklenmeden önce DOM'u temizle
        booksListDiv.innerHTML = '';
        try {
            booksListDiv.innerHTML = '<div class="loading">Kitaplar yükleniyor...</div>';
            // Cache'i tamamen devre dışı bırak
            const response = await fetch(`${this.apiBaseUrl}/books`, { cache: 'no-store' });
            const books = await response.json();

            if (books.length === 0) {
                booksListDiv.innerHTML = '<div class="empty-state">Kütüphanede henüz kitap bulunmuyor.</div>';
            } else {
                this.displayBooks(books);
            }
        } catch (error) {
            console.error('Kitaplar yüklenirken hata:', error);
            booksListDiv.innerHTML = '<div class="error-state">Kitaplar yüklenirken bir hata oluştu.</div>';
        }
    }

    // Kitapları göster
    displayBooks(books) {
        const booksListDiv = document.getElementById('booksList');
        const isAdmin = (this.currentRole === 'admin');
        const booksHtml = books.map(book => {
            const adminActions = isAdmin ? `
                <div class="book-actions">
                    <button class="btn btn-small" onclick="libraryManager.prefillEditForm('${book.isbn}','${encodeURIComponent(book.title)}','${encodeURIComponent(book.author)}')">
                        <i class="fas fa-pen"></i> Düzenle
                    </button>
                    <button class="btn btn-small btn-danger" onclick="libraryManager.showDeleteModal('${book.isbn}', '${book.title}', '${book.author}')">
                        <i class="fas fa-trash"></i> Sil
                    </button>
                </div>` : '';
            return `
            <div class="book-card" data-isbn="${book.isbn}">
                <div class="book-header">
                    <div class="book-icon">
                        <i class="fas fa-book"></i>
                    </div>
                    <h3 class="book-title">${book.title}</h3>
                </div>
                <div class="book-details">
                    <div class="book-author">
                        <span>${book.author}</span>
                    </div>
                    <div class="book-isbn">
                        <span>${book.isbn}</span>
                    </div>
                </div>
                ${adminActions}
            </div>`;
        }).join('');
        booksListDiv.innerHTML = `<div class="books-grid">${booksHtml}</div>`;
    }

    // Kitap silme modal'ını göster
    showDeleteModal(isbn, title, author) {
        document.getElementById('deleteBookTitle').textContent = title;
        document.getElementById('deleteBookAuthor').textContent = author;
        document.getElementById('deleteBookIsbn').textContent = isbn;
        
        // Modal'ı göster
        document.getElementById('deleteModal').style.display = 'block';
        
        // Silme butonuna event listener ekle
        document.getElementById('confirmDeleteBtn').onclick = () => {
            this.deleteBook(isbn);
        };
        
        // İptal butonuna event listener ekle
        document.getElementById('cancelDeleteBtn').onclick = () => {
            this.closeModal();
        };
    }

    // Modal'ı kapat
    closeModal() {
        document.getElementById('deleteModal').style.display = 'none';
    }

    // Kitap silme
    async deleteBook(isbn) {
        try {
            // Admin endpointi varsa onu kullan
            const endpoint = this.currentRole === 'admin' ? `/admin/books/${isbn}` : `/books/${isbn}`;
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    ...(this.authToken ? { 'Authorization': `Bearer ${this.authToken}` } : {}),
                }
            });

            if (response.ok) {
                this.showStatus('✓ Kitap başarıyla silindi.', 'success');
                this.closeModal();
                this.loadBooks(); // Kitap listesini yenile
                
                // Arama sonucunu da temizle
                const searchResult = document.getElementById('searchResult');
                if (searchResult.style.display === 'block') {
                    searchResult.style.display = 'none';
                }
            } else {
                const data = await response.json();
                this.showStatus(`❌ ${data.detail}`, 'error');
            }
        } catch (error) {
            console.error('Kitap silme hatası:', error);
            this.showStatus('❌ Kitap silinirken bir hata oluştu. Lütfen tekrar deneyin.', 'error');
        }
    }

    async updateBook() {
        if (this.currentRole !== 'admin') { this.showStatus('Bu işlem için admin gerekli.', 'error', 'updateBookStatus'); return; }
        const updateBtn = document.getElementById('updateBookBtn');
        const isbnRaw = (document.getElementById('updateIsbnInput').value || '').trim();
        const isbn = isbnRaw.replace(/[-.\s_]/g, '').toUpperCase();
        const title = (document.getElementById('updateTitleInput').value || '').trim();
        const author = (document.getElementById('updateAuthorInput').value || '').trim();
        if (!isbn) { this.showStatus('ISBN gerekli', 'error', 'updateBookStatus'); return; }
        if (isbn.length < 10) { this.showStatus('Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.', 'error', 'updateBookStatus'); return; }
        if (!title && !author) { this.showStatus('Güncellenecek alan yok. Başlık veya yazar girin.', 'error', 'updateBookStatus'); return; }
        try {
            updateBtn && (updateBtn.disabled = true);
            const res = await fetch(`${this.apiBaseUrl}/admin/books/${isbn}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    ...(this.authToken ? { 'Authorization': `Bearer ${this.authToken}` } : {}),
                },
                body: JSON.stringify({ title: title || null, author: author || null })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Güncelleme başarısız');
            this.showStatus('✓ Kitap güncellendi.', 'success', 'updateBookStatus');
            // Alanları temizle (düzenlemeden sonra)
            document.getElementById('updateTitleInput').value = '';
            document.getElementById('updateAuthorInput').value = '';
            setTimeout(() => this.loadBooks(), 200); // Küçük bir gecikme ile kitapları yenile
        } catch (e) {
            this.showStatus(`❌ ${e.message}`, 'error', 'updateBookStatus');
        } finally {
            updateBtn && (updateBtn.disabled = false);
        }
    }

    // Admin düzenleme formunu doldur
    prefillEditForm(isbn, encTitle = '', encAuthor = '') {
        if (this.currentRole !== 'admin') { return; }
        try {
            const title = encTitle ? decodeURIComponent(encTitle) : '';
            const author = encAuthor ? decodeURIComponent(encAuthor) : '';
            const isbnInput = document.getElementById('updateIsbnInput');
            const titleInput = document.getElementById('updateTitleInput');
            const authorInput = document.getElementById('updateAuthorInput');
            if (isbnInput) isbnInput.value = isbn || '';
            if (titleInput) titleInput.value = title;
            if (authorInput) authorInput.value = author;
            this.showStatus('Düzenleme için alanlar dolduruldu.', 'info', 'updateBookStatus');
        } catch {
            // yoksay
        }
    }

    // Durum mesajı göster
    showStatus(message, type = 'info', targetId = 'addBookStatus') {
        const statusDiv = document.getElementById(targetId) || document.getElementById('addBookStatus');
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
        statusDiv.style.display = 'block';
        
        // 5 saniye sonra mesajı gizle
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }

    // API bağlantısını test et
    async testConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // ---------- AUTH ----------
    setAuthUI() {
        const outEl = document.getElementById('authLoggedOut');
        const inEl = document.getElementById('authLoggedIn');
        const userPanel = document.getElementById('userPanel');
        const adminPanel = document.getElementById('adminPanel');
        if (this.authToken) {
            outEl && (outEl.style.display = 'none');
            inEl && (inEl.style.display = 'flex');
            document.getElementById('currentUser').textContent = this.currentUser || '';
            document.getElementById('currentRole').textContent = this.currentRole || '';
            if (this.currentRole === 'admin') {
                userPanel && (userPanel.style.display = 'none');
                adminPanel && (adminPanel.style.display = 'block');
            } else {
                userPanel && (userPanel.style.display = 'block');
                adminPanel && (adminPanel.style.display = 'none');
                this.loadUserToRead();
                this.loadUserReadBooks();
            }
        } else {
            outEl && (outEl.style.display = 'flex');
            inEl && (inEl.style.display = 'none');
            userPanel && (userPanel.style.display = 'none');
            adminPanel && (adminPanel.style.display = 'none');
        }
        // this.loadBooks(); // <-- Bunu kaldırdım
    }

    async login() {
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value.trim();
        if (!username || !password) {
            this.showStatus('Kullanıcı adı ve şifre zorunlu.', 'error');
            return;
        }
        try {
            const res = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Giriş başarısız');
            this.authToken = data.token;
            this.currentUser = data.username;
            this.currentRole = data.role;
            this.setAuthUI();
            this.loadBooks(); // Girişten hemen sonra kitapları yükle
            this.showStatus('Giriş başarılı.', 'success');
        } catch (e) {
            this.showStatus(`❌ ${e.message}`, 'error');
        }
    }

    async register() {
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value.trim();
        if (!username || !password) {
            this.showStatus('Kullanıcı adı ve şifre zorunlu.', 'error');
            return;
        }
        try {
            const res = await fetch(`${this.apiBaseUrl}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Kayıt başarısız');
            this.showStatus('Kayıt başarılı. Şimdi giriş yapabilirsiniz.', 'success');
        } catch (e) {
            this.showStatus(`❌ ${e.message}`, 'error');
        }
    }

    async logout() {
        try {
            // Token varsa logout endpoint'ini çağır
            if (this.authToken) {
                await fetch(`${this.apiBaseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`
                    }
                });
            }
        } catch (error) {
            console.log('Logout API hatası (göz ardı edildi):', error);
        }
        
        // Local storage'dan da temizle
        try {
            localStorage.removeItem('auth');
        } catch {}
        
        this.authToken = null;
        this.currentUser = null;
        this.currentRole = null;
        this.setAuthUI();
        this.loadBooks(); // Çıkıştan hemen sonra kitapları yükle
        this.showStatus('Çıkış yapıldı.', 'info');
    }

    // ---------- USER BOOKLIST ----------
    async loadUserToRead() {
        if (!this.authToken) return;
        const target = document.getElementById('userToreadList');
        try {
            target.innerHTML = '<div class="loading">Kitaplar yükleniyor...</div>';
            const res = await fetch(`${this.apiBaseUrl}/me/books`, {
                headers: { 'Authorization': `Bearer ${this.authToken}` }
            });
            const books = await res.json();
            const toRead = (Array.isArray(books) ? books : []).filter(b => !b.is_read);
            if (toRead.length === 0) {
                target.innerHTML = '<div class="empty-state">Okunacak kitap yok.</div>';
                return;
            }
            target.innerHTML = `<div class="books-grid">${toRead.map(b => `
                <div class="book-card" data-isbn="${b.isbn}">
                    <div class="book-header">
                        <div class="book-icon"><i class="fas fa-book"></i></div>
                        <h3 class="book-title">${b.title}</h3>
                    </div>
                    <div class="book-details">
                        <div class="book-author"><span>${b.author}</span></div>
                        <div class="book-isbn"><span>${b.isbn}</span></div>
                    </div>
                    <div class="book-actions">
                        <button class="btn btn-small ${b.is_read ? 'btn-outline' : 'btn-secondary'}" onclick="libraryManager.toggleRead('${b.isbn}', ${!b.is_read})">
                            <i class="fas ${b.is_read ? 'fa-rotate-left' : 'fa-check'}"></i> ${b.is_read ? 'Okunmadı' : 'Okundu'}
                        </button>
                        <button class="btn btn-small btn-danger" onclick="libraryManager.removeFromUser('${b.isbn}')"><i class="fas fa-trash"></i> Kaldır</button>
                    </div>
                </div>`).join('')}</div>`;
        } catch (e) {
            target.innerHTML = '<div class="error-state">Kullanıcı kitapları yüklenemedi.</div>';
        }
    }

    async loadUserReadBooks() {
        if (!this.authToken) return;
        const target = document.getElementById('userReadBooksList');
        try {
            target.innerHTML = '<div class="loading">Kitaplar yükleniyor...</div>';
            const res = await fetch(`${this.apiBaseUrl}/me/books/read`, {
                headers: { 'Authorization': `Bearer ${this.authToken}` }
            });
            const books = await res.json();
            if (!Array.isArray(books) || books.length === 0) {
                target.innerHTML = '<div class="empty-state">Henüz okuduğunuz kitap yok.</div>';
                return;
            }
            target.innerHTML = `<div class="books-grid">${books.map(b => `
                <div class="book-card">
                    <div class="book-header">
                        <div class="book-icon"><i class="fas fa-check"></i></div>
                        <h3 class="book-title">${b.title}</h3>
                    </div>
                    <div class="book-details">
                        <div class="book-author"><span>${b.author}</span></div>
                        <div class="book-isbn"><span>${b.isbn}</span></div>
                    </div>
                </div>`).join('')}</div>`;
        } catch (e) {
            target.innerHTML = '<div class="error-state">Okunan kitaplar yüklenemedi.</div>';
        }
    }

    async userAddBook() {
        if (!this.authToken) {
            this.showStatus('Lütfen giriş yapın.', 'error');
            return;
        }
        const input = document.getElementById('userIsbnInput');
        const isbn = input.value.trim();
        if (!isbn) {
            this.showStatus('ISBN gerekli', 'error');
            return;
        }
        try {
            const res = await fetch(`${this.apiBaseUrl}/me/books`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({ isbn })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Ekleme başarısız');
            input.value = '';
            this.loadUserToRead();
            this.showStatus('Listeye eklendi.', 'success');
        } catch (e) {
            this.showStatus(`❌ ${e.message}`, 'error');
        }
    }

    async toggleRead(isbn, isRead) {
        if (!this.authToken) return;
        try {
            const res = await fetch(`${this.apiBaseUrl}/me/books/${isbn}/${isRead ? 'read' : 'unread'}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.authToken}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Güncelleme başarısız');
            this.loadUserToRead();
            this.loadUserReadBooks();
        } catch (e) {
            this.showStatus(`❌ ${e.message}`, 'error');
        }
    }

    async removeFromUser(isbn) {
        if (!this.authToken) return;
        try {
            const res = await fetch(`${this.apiBaseUrl}/me/books/${isbn}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.authToken}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Silme başarısız');
            this.loadUserToRead();
            this.showStatus('Listeden kaldırıldı.', 'success');
        } catch (e) {
            this.showStatus(`❌ ${e.message}`, 'error');
        }
    }

    // (library search removed)
}

// Sayfa yüklendiğinde LibraryManager'ı başlat
document.addEventListener('DOMContentLoaded', () => {
    window.libraryManager = new LibraryManager();
    
    // API bağlantısını test et
    libraryManager.testConnection().then(isConnected => {
        if (!isConnected) {
            libraryManager.showStatus('⚠️ API sunucusuna bağlanılamıyor. Lütfen uvicorn api:app --reload komutunu çalıştırın.', 'error');
        }
    });

    // Local storage'dan token yükle
    try {
        const saved = JSON.parse(localStorage.getItem('auth') || '{}');
        if (saved && saved.token) {
            libraryManager.authToken = saved.token;
            libraryManager.currentUser = saved.username;
            libraryManager.currentRole = saved.role;
            // Token geçerli mi kontrol et
            fetch(`${libraryManager.apiBaseUrl}/me`, {
                headers: { 'Authorization': `Bearer ${saved.token}` }
            })
            .then(res => {
                if (res.ok) {
                    libraryManager.setAuthUI();
                } else {
                    // Token geçersiz, çıkış yap
                    libraryManager.logout();
                }
            })
            .catch(() => {
                // API hatası varsa da çıkış yap
                libraryManager.logout();
            });
        }
    } catch {}
});

// Sayfa yenilendiğinde form alanlarını temizle
window.addEventListener('beforeunload', () => {
    document.getElementById('isbnInput').value = '';
    document.getElementById('searchInput').value = '';
    // Token'ı kaydet
    try {
        if (libraryManager.authToken) {
            localStorage.setItem('auth', JSON.stringify({ token: libraryManager.authToken, username: libraryManager.currentUser, role: libraryManager.currentRole }));
        } else {
            localStorage.removeItem('auth');
        }
    } catch {}
});

// Hata yakalama
window.addEventListener('error', (e) => {
    console.error('JavaScript hatası:', e.error);
});

// Unhandled promise rejection yakalama
window.addEventListener('unhandledrejection', (e) => {
    console.error('Promise hatası:', e.reason);
    e.preventDefault();
});
