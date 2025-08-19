import json
import httpx
from typing import List, Optional
from typing import Dict


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
    """Kütüphane sınıfı - tüm kütüphane operasyonlarını yönetir"""
    
    def __init__(self, filename: str = "library.json"):
        self.filename = filename
        self.books: List[Book] = []
        self.load_books()
    
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
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False
    
    def list_books(self) -> List[Book]:
        """Kütüphanedeki tüm kitapları listeler"""
        return self.books.copy()
    
    def find_book(self, isbn: str) -> Optional[Book]:
        """ISBN ile belirli bir kitabı bulur"""
        normalized_isbn = self._normalize_isbn(isbn)
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
        """Uygulama başladığında library.json dosyasından kitapları yükler"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.books = [Book.from_dict(book_data) for book_data in data]
        except FileNotFoundError:
            # Dosya yoksa boş liste ile başla
            self.books = []
        except json.JSONDecodeError:
            # JSON hatası varsa boş liste ile başla
            print("library.json dosyasında hata bulundu, boş kütüphane ile başlanıyor.")
            self.books = []
    
    def save_books(self):
        """Kütüphanede bir değişiklik olduğunda tüm kitap listesini dosyaya yazar"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump([book.to_dict() for book in self.books], file, 
                         ensure_ascii=False, indent=2)
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
        if title and isinstance(title, str) and title.strip():
            book.title = title.strip()
        if author and isinstance(author, str) and author.strip():
            book.author = author.strip()
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
    """Kullanıcı yönetimi ve kullanıcı bazlı kitap listeleri"""

    def __init__(self, filename: str = "users.json"):
        self.filename = filename
        self.users: Dict[str, User] = {}
        self._library_helper = Library()  # ISBN normalize ve API için yardımcı
        self.load_users()
        # Varsayılan admin yoksa oluştur
        if "admin" not in self.users:
            self.create_user("admin", "admin123", role="admin")
            self.save_users()
        # Varsayılan normal kullanıcı (demo) yoksa oluştur
        if "demo" not in self.users:
            self.create_user("demo", "demo123", role="user")
            self.save_users()

    def _hash_password(self, password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def load_users(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.users = {u["username"]: User.from_dict(u) for u in data}
        except FileNotFoundError:
            self.users = {}
        except json.JSONDecodeError:
            self.users = {}

    def save_users(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([u.to_dict() for u in self.users.values()], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Kullanıcılar kaydedilirken hata: {e}")

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        if not username or not password:
            return False
        if username in self.users:
            return False
        password_hash = self._hash_password(password)
        self.users[username] = User(username=username, password_hash=password_hash, role=role)
        self.save_users()
        return True

    def verify_user(self, username: str, password: str) -> Optional[User]:
        user = self.users.get(username)
        if not user:
            return None
        if user.password_hash == self._hash_password(password):
            return user
        return None

    def get_user(self, username: str) -> Optional[User]:
        return self.users.get(username)

    # Kullanıcı kitap işlemleri
    def list_user_books(self, username: str) -> List[dict]:
        user = self.get_user(username)
        if not user:
            return []
        return [b.to_dict() for b in user.books]

    def add_book_to_user_by_isbn(self, username: str, isbn: str) -> Optional[dict]:
        user = self.get_user(username)
        if not user:
            return None
        normalized = self._library_helper._normalize_isbn(isbn)
        # Zaten var mı?
        for b in user.books:
            if b.book.isbn == normalized:
                return None
        # API'den çek
        info = self._library_helper._fetch_book_from_api(normalized)
        if not info:
            return None
        user_book = UserBook(Book(title=info["title"], author=info["author"], isbn=normalized), is_read=False)
        user.books.append(user_book)
        self.save_users()
        return user_book.to_dict()

    def remove_user_book(self, username: str, isbn: str) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        normalized = self._library_helper._normalize_isbn(isbn)
        for b in list(user.books):
            if b.book.isbn == normalized:
                user.books.remove(b)
                self.save_users()
                return True
        return False

    def mark_user_book_read(self, username: str, isbn: str, is_read: bool = True) -> Optional[dict]:
        user = self.get_user(username)
        if not user:
            return None
        normalized = self._library_helper._normalize_isbn(isbn)
        for b in user.books:
            if b.book.isbn == normalized:
                b.is_read = is_read
                self.save_users()
                return b.to_dict()
        return None

    def list_user_read_books(self, username: str) -> List[dict]:
        user = self.get_user(username)
        if not user:
            return []
        return [b.to_dict() for b in user.books if b.is_read]
