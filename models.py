import json
import httpx
import sqlite3
import os
from typing import List, Optional, Dict, Tuple


class Book:
    """Kitap sınıfı - her bir kitabı temsil eder"""
    
    def __init__(self, title: str, author: str, isbn: str):
        self.title = title
        self.author = author
        self.isbn = isbn
    
    def __str__(self) -> str:
        """Kitap bilgilerini okunaklı formatta döndürür"""
        return f"{self.title} by {self.author} (ISBN: {self.isbn})"
    
    def to_dict(self) -> dict:
        """Kitap nesnesini dictionary formatına çevirir"""
        return {
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Book':
        """Dictionary'den Book nesnesi oluşturur"""
        return cls(
            title=data["title"],
            author=data["author"],
            isbn=data["isbn"]
        )


class Library:
    """Kütüphane sınıfı - tüm kütüphane operasyonlarını yönetir

    SQLite desteği: db_path verildiğinde JSON yerine SQLite kullanılır.
    """
    
    def __init__(self, filename: str = "library.json", db_path: Optional[str] = None):
        self.filename = filename
        self.db_path = db_path
        self.use_sqlite = bool(db_path)
        self.books: List[Book] = []
        if self.use_sqlite:
            self._init_db()
            self._migrate_json_to_sqlite_if_needed()
            self.load_books()
        else:
            self.load_books()

    def _get_conn(self) -> sqlite3.Connection:
        assert self.db_path
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    isbn TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _migrate_json_to_sqlite_if_needed(self):
        # Eğer DB boşsa ve JSON dosyası varsa içeri aktarmayı dene
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM books")
            count = cur.fetchone()[0]
        if count == 0 and os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    with self._get_conn() as conn:
                        for item in data:
                            isbn = self._normalize_isbn(item.get('isbn', ''))
                            title = item.get('title', '')
                            author = item.get('author', '')
                            if isbn and title and author:
                                conn.execute(
                                    "INSERT OR IGNORE INTO books (isbn, title, author) VALUES (?, ?, ?)",
                                    (isbn, title, author)
                                )
                        conn.commit()
            except Exception:
                # sessiz geç
                pass
    
    def _normalize_isbn(self, isbn: str) -> str:
        """ISBN değerini standartlaştırır (tire, boşluk ve nokta işaretlerini kaldırır)."""
        if not isinstance(isbn, str):
            return ""
        # Tüm tire, boşluk, nokta ve alt çizgileri kaldır
        normalized = isbn.replace("-", "").replace(" ", "").replace(".", "").replace("_", "").upper()
        return normalized
    
    def add_book(self, book: Book) -> bool:
        """Yeni bir kitabı kütüphaneye ekler"""
        # ISBN'i normalize et ve tekrar yaz
        book.isbn = self._normalize_isbn(book.isbn)
        # ISBN zaten varsa ekleme
        if self.find_book(book.isbn):
            return False

        if self.use_sqlite:
            try:
                with self._get_conn() as conn:
                    conn.execute(
                        "INSERT INTO books (isbn, title, author) VALUES (?, ?, ?)",
                        (book.isbn, book.title, book.author)
                    )
                    conn.commit()
                self.books.append(book)
                return True
            except sqlite3.IntegrityError:
                return False
        else:
            self.books.append(book)
            self.save_books()
            return True
    
    def add_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """ISBN ile Open Library API'den kitap bilgilerini çeker ve ekler"""
        try:
            normalized_isbn = self._normalize_isbn(isbn)
            # Open Library API'den kitap bilgilerini çek
            book_info = self._fetch_book_from_api(normalized_isbn)
            if book_info:
                book = Book(
                    title=book_info["title"],
                    author=book_info["author"],
                    isbn=normalized_isbn
                )
                if self.add_book(book):
                    return book
                else:
                    return None  # Kitap zaten mevcut
            else:
                return None  # API'den kitap bulunamadı
        except Exception as e:
            print(f"Kitap eklenirken hata oluştu: {e}")
            return None
    
    def remove_book(self, isbn: str) -> bool:
        """ISBN ile kitabı kütüphaneden siler"""
        normalized_isbn = self._normalize_isbn(isbn)
        book = self.find_book(normalized_isbn)
        if not book:
            return False
        if self.use_sqlite:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM books WHERE isbn = ?", (normalized_isbn,))
                conn.commit()
            # Bellek listesini güncelle
            self.books = [b for b in self.books if b.isbn != normalized_isbn]
            return True
        else:
            self.books.remove(book)
            self.save_books()
            return True
    
    def list_books(self) -> List[Book]:
        """Kütüphanedeki tüm kitapları listeler"""
        if self.use_sqlite:
            # DB'den taze çekip dön
            with self._get_conn() as conn:
                cur = conn.execute("SELECT title, author, isbn FROM books ORDER BY title")
                rows = cur.fetchall()
            self.books = [Book(title=row[0], author=row[1], isbn=row[2]) for row in rows]
            return self.books.copy()
        return self.books.copy()
    
    def find_book(self, isbn: str) -> Optional[Book]:
        """ISBN ile belirli bir kitabı bulur"""
        normalized_isbn = self._normalize_isbn(isbn)
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT title, author, isbn FROM books WHERE isbn = ?", (normalized_isbn,))
                row = cur.fetchone()
            if not row:
                return None
            return Book(title=row[0], author=row[1], isbn=row[2])
        for book in self.books:
            if book.isbn == normalized_isbn:
                return book
        return None
    
    def _fetch_book_from_api(self, isbn: str) -> Optional[dict]:
        """Open Library API'den kitap bilgilerini çeker"""
        try:
            normalized_isbn = self._normalize_isbn(isbn)
            url = f"https://openlibrary.org/isbn/{normalized_isbn}.json"
            with httpx.Client() as client:
                response = client.get(url, timeout=10.0, follow_redirects=True)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Kitap başlığını al
                    title = data.get("title", "Bilinmeyen Başlık")
                    
                    # Yazar bilgisini al
                    authors = data.get("authors", [])
                    if authors:
                        # İlk yazarın adını al
                        author_key = authors[0]["key"]
                        author_response = client.get(
                            f"https://openlibrary.org{author_key}.json",
                            timeout=10.0,
                            follow_redirects=True,
                        )
                        if author_response.status_code == 200:
                            author_data = author_response.json()
                            author = author_data.get("name", "Bilinmeyen Yazar")
                        else:
                            author = "Bilinmeyen Yazar"
                    else:
                        author = "Bilinmeyen Yazar"
                    
                    return {
                        "title": title,
                        "author": author
                    }
                else:
                    return None
                    
        except Exception as e:
            print(f"API'den veri çekilirken hata: {e}")
            return None
    
    def load_books(self):
        """Kitapları depodan yükler (SQLite varsa oradan)"""
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT title, author, isbn FROM books ORDER BY title")
                rows = cur.fetchall()
                self.books = [Book(title=row[0], author=row[1], isbn=row[2]) for row in rows]
            return
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.books = [Book.from_dict(book_data) for book_data in data]
        except FileNotFoundError:
            self.books = []
        except json.JSONDecodeError:
            print("library.json dosyasında hata bulundu, boş kütüphane ile başlanıyor.")
            self.books = []
    
    def save_books(self):
        """Kütüphanede bir değişiklik olduğunda tüm kitap listesini dosyaya yazar
        (yalnızca JSON modu için). SQLite modunda gerekmez.
        """
        if self.use_sqlite:
            return
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump([book.to_dict() for book in self.books], file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Kitaplar kaydedilirken hata oluştu: {e}")
    
    def get_books_as_dicts(self) -> List[dict]:
        """Kitapları dictionary listesi olarak döndürür (API için)"""
        return [book.to_dict() for book in self.books]

    def update_book(self, isbn: str, title: Optional[str] = None, author: Optional[str] = None) -> Optional[Book]:
        """Mevcut bir kitabın başlık/yazar bilgilerini günceller"""
        normalized_isbn = self._normalize_isbn(isbn)
        book = self.find_book(normalized_isbn)
        if not book:
            return None
        new_title = book.title
        new_author = book.author
        if title and isinstance(title, str) and title.strip():
            new_title = title.strip()
        if author and isinstance(author, str) and author.strip():
            new_author = author.strip()
        if self.use_sqlite:
            with self._get_conn() as conn:
                conn.execute("UPDATE books SET title = ?, author = ? WHERE isbn = ?", (new_title, new_author, normalized_isbn))
                conn.commit()
            # Bellek objesini güncelle
            book.title = new_title
            book.author = new_author
            return book
        else:
            book.title = new_title
            book.author = new_author
            self.save_books()
            return book


class UserBook:
    """Kullanıcının kitap listesinde yer alan kitap ve okuma durumunu temsil eder"""

    def __init__(self, book: Book, is_read: bool = False):
        self.book = book
        self.is_read = is_read

    def to_dict(self) -> dict:
        return {
            "title": self.book.title,
            "author": self.book.author,
            "isbn": self.book.isbn,
            "is_read": self.is_read,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UserBook':
        return cls(
            book=Book(
                title=data["title"],
                author=data["author"],
                isbn=data["isbn"],
            ),
            is_read=data.get("is_read", False),
        )


class User:
    """Uygulama kullanıcısı (admin veya normal)"""

    def __init__(self, username: str, password_hash: str, role: str = "user", books: Optional[List[UserBook]] = None):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.books: List[UserBook] = books or []

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role,
            "books": [b.to_dict() for b in self.books],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            username=data["username"],
            password_hash=data["password_hash"],
            role=data.get("role", "user"),
            books=[UserBook.from_dict(b) for b in data.get("books", [])],
        )


class UserManager:
    """Kullanıcı yönetimi ve kullanıcı bazlı kitap listeleri

    SQLite desteği: db_path verildiğinde JSON yerine SQLite kullanılır.
    """
 
    def __init__(self, filename: str = "users.json", db_path: Optional[str] = None):
        self.filename = filename
        self.db_path = db_path
        self.use_sqlite = bool(db_path)
        self.users: Dict[str, User] = {}
        self._library_helper = Library()  # ISBN normalize ve API için yardımcı
        if self.use_sqlite:
            self._init_db()
            self._migrate_json_to_sqlite_if_needed()
            # Varsayılan kullanıcıları DB'de yoksa ekle
            if not self.get_user("admin"):
                self.create_user("admin", "admin123", role="admin")
            if not self.get_user("demo"):
                self.create_user("demo", "demo123", role="user")
        else:
            self.load_users()
            # Varsayılan admin yoksa oluştur
            if "admin" not in self.users:
                self.create_user("admin", "admin123", role="admin")
                self.save_users()
            # Varsayılan normal kullanıcı (demo) yoksa oluştur
            if "demo" not in self.users:
                self.create_user("demo", "demo123", role="user")
                self.save_users()

    def _get_conn(self) -> sqlite3.Connection:
        assert self.db_path
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_books (
                    username TEXT NOT NULL,
                    isbn TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (username, isbn),
                    FOREIGN KEY (username) REFERENCES users(username)
                )
                """
            )
            conn.commit()

    def _migrate_json_to_sqlite_if_needed(self):
        # Eğer users tablosu boşsa ve JSON dosyası varsa içeri aktar
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
        if count == 0 and os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    with self._get_conn() as conn:
                        for u in data:
                            username = u.get('username')
                            password_hash = u.get('password_hash')
                            role = u.get('role', 'user')
                            if username and password_hash:
                                conn.execute(
                                    "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                    (username, password_hash, role)
                                )
                                # Kullanıcı kitaplarını aktar
                                for b in u.get('books', []):
                                    isbn = b.get('isbn')
                                    title = b.get('title')
                                    author = b.get('author')
                                    is_read = 1 if b.get('is_read') else 0
                                    if isbn and title and author:
                                        conn.execute(
                                            "INSERT OR IGNORE INTO user_books (username, isbn, title, author, is_read) VALUES (?, ?, ?, ?, ?)",
                                            (username, isbn, title, author, is_read)
                                        )
                        conn.commit()
            except Exception:
                pass

    def _hash_password(self, password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def load_users(self):
        if self.use_sqlite:
            # SQLite modunda in-memory kullanıcı sözlüğü tutulmaz
            return
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.users = {u["username"]: User.from_dict(u) for u in data}
        except FileNotFoundError:
            self.users = {}
        except json.JSONDecodeError:
            self.users = {}

    def save_users(self):
        if self.use_sqlite:
            return
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([u.to_dict() for u in self.users.values()], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Kullanıcılar kaydedilirken hata: {e}")

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        if not username or not password:
            return False
        password_hash = self._hash_password(password)
        if self.use_sqlite:
            with self._get_conn() as conn:
                # Mevcut mu?
                cur = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
                if cur.fetchone():
                    return False
                conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role)
                )
                conn.commit()
            return True
        # JSON modu
        if username in self.users:
            return False
        self.users[username] = User(username=username, password_hash=password_hash, role=role)
        self.save_users()
        return True

    def verify_user(self, username: str, password: str) -> Optional[User]:
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
                row = cur.fetchone()
            if not row:
                return None
            if row[1] == self._hash_password(password):
                return User(username=row[0], password_hash=row[1], role=row[2], books=self._load_user_books_from_db(row[0]))
            return None
        user = self.users.get(username)
        if not user:
            return None
        if user.password_hash == self._hash_password(password):
            return user
        return None

    def get_user(self, username: str) -> Optional[User]:
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
                row = cur.fetchone()
            if not row:
                return None
            return User(username=row[0], password_hash=row[1], role=row[2], books=self._load_user_books_from_db(row[0]))
        return self.users.get(username)

    def _load_user_books_from_db(self, username: str) -> List[UserBook]:
        if not self.use_sqlite:
            return []
        with self._get_conn() as conn:
            cur = conn.execute("SELECT title, author, isbn, is_read FROM user_books WHERE username = ?", (username,))
            rows = cur.fetchall()
        result: List[UserBook] = []
        for row in rows:
            result.append(UserBook(Book(title=row[0], author=row[1], isbn=row[2]), is_read=bool(row[3])))
        return result

    # Kullanıcı kitap işlemleri
    def list_user_books(self, username: str) -> List[dict]:
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT title, author, isbn, is_read FROM user_books WHERE username = ?", (username,))
                rows = cur.fetchall()
            return [
                {
                    "title": row[0],
                    "author": row[1],
                    "isbn": row[2],
                    "is_read": bool(row[3])
                }
                for row in rows
            ]
        user = self.get_user(username)
        if not user:
            return []
        return [b.to_dict() for b in user.books]

    def add_book_to_user_by_isbn(self, username: str, isbn: str) -> Optional[dict]:
        if self.use_sqlite:
            normalized = self._library_helper._normalize_isbn(isbn)
            with self._get_conn() as conn:
                # Kullanıcı var mı?
                cur = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
                if not cur.fetchone():
                    return None
                # Zaten var mı?
                cur = conn.execute("SELECT 1 FROM user_books WHERE username = ? AND isbn = ?", (username, normalized))
                if cur.fetchone():
                    return None
                info = self._library_helper._fetch_book_from_api(normalized)
                if not info:
                    return None
                conn.execute(
                    "INSERT INTO user_books (username, isbn, title, author, is_read) VALUES (?, ?, ?, ?, 0)",
                    (username, normalized, info["title"], info["author"]) 
                )
                conn.commit()
            return {"title": info["title"], "author": info["author"], "isbn": normalized, "is_read": False}
        # JSON modu
        user = self.get_user(username)
        if not user:
            return None
        normalized = self._library_helper._normalize_isbn(isbn)
        for b in user.books:
            if b.book.isbn == normalized:
                return None
        info = self._library_helper._fetch_book_from_api(normalized)
        if not info:
            return None
        user_book = UserBook(Book(title=info["title"], author=info["author"], isbn=normalized), is_read=False)
        user.books.append(user_book)
        self.save_users()
        return user_book.to_dict()

    def remove_user_book(self, username: str, isbn: str) -> bool:
        normalized = self._library_helper._normalize_isbn(isbn)
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("DELETE FROM user_books WHERE username = ? AND isbn = ?", (username, normalized))
                conn.commit()
                return cur.rowcount > 0
        user = self.get_user(username)
        if not user:
            return False
        for b in list(user.books):
            if b.book.isbn == normalized:
                user.books.remove(b)
                self.save_users()
                return True
        return False

    def mark_user_book_read(self, username: str, isbn: str, is_read: bool = True) -> Optional[dict]:
        normalized = self._library_helper._normalize_isbn(isbn)
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute(
                    "UPDATE user_books SET is_read = ? WHERE username = ? AND isbn = ?",
                    (1 if is_read else 0, username, normalized)
                )
                conn.commit()
            # Güncellenen kaydı döndür
            with self._get_conn() as conn:
                cur = conn.execute(
                    "SELECT title, author, isbn, is_read FROM user_books WHERE username = ? AND isbn = ?",
                    (username, normalized)
                )
                row = cur.fetchone()
            if not row:
                return None
            return {"title": row[0], "author": row[1], "isbn": row[2], "is_read": bool(row[3])}
        user = self.get_user(username)
        if not user:
            return None
        for b in user.books:
            if b.book.isbn == normalized:
                b.is_read = is_read
                self.save_users()
                return b.to_dict()
        return None

    def list_user_read_books(self, username: str) -> List[dict]:
        if self.use_sqlite:
            with self._get_conn() as conn:
                cur = conn.execute("SELECT title, author, isbn, is_read FROM user_books WHERE username = ? AND is_read = 1", (username,))
                rows = cur.fetchall()
            return [
                {"title": row[0], "author": row[1], "isbn": row[2], "is_read": bool(row[3])}
                for row in rows
            ]
        user = self.get_user(username)
        if not user:
            return []
        return [b.to_dict() for b in user.books if b.is_read]
