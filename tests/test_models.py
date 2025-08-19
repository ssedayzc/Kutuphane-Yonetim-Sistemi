#!/usr/bin/env python3
"""
Test dosyası: models.py için testler
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, Mock
from models import Book, Library


class TestBook:
    """Book sınıfı için testler"""
    
    def test_book_creation(self):
        """Book nesnesi oluşturma testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        
        assert book.title == "Test Kitap"
        assert book.author == "Test Yazar"
        assert book.isbn == "1234567890"
    
    def test_book_str_method(self):
        """Book.__str__ metodu testi"""
        book = Book("Ulysses", "James Joyce", "978-0199535675")
        expected = "Ulysses by James Joyce (ISBN: 978-0199535675)"
        
        assert str(book) == expected
    
    def test_book_to_dict(self):
        """Book.to_dict metodu testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        book_dict = book.to_dict()
        
        assert book_dict["title"] == "Test Kitap"
        assert book_dict["author"] == "Test Yazar"
        assert book_dict["isbn"] == "1234567890"
        assert isinstance(book_dict, dict)
    
    def test_book_from_dict(self):
        """Book.from_dict class method testi"""
        book_data = {
            "title": "Test Kitap",
            "author": "Test Yazar",
            "isbn": "1234567890"
        }
        
        book = Book.from_dict(book_data)
        
        assert isinstance(book, Book)
        assert book.title == "Test Kitap"
        assert book.author == "Test Yazar"
        assert book.isbn == "1234567890"


class TestLibrary:
    """Library sınıfı için testler"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        # Geçici dosya oluştur
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write('[]')
        self.temp_file.close()
        
        # Library nesnesini geçici dosya ile oluştur
        self.library = Library(self.temp_file.name)
    
    def teardown_method(self):
        """Her test sonrası çalışır"""
        # Geçici dosyayı sil
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_library_initialization(self):
        """Library başlatma testi"""
        assert self.library.books == []
        assert self.library.filename == self.temp_file.name
    
    def test_add_book(self):
        """Kitap ekleme testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        
        result = self.library.add_book(book)
        
        assert result is True
        assert len(self.library.books) == 1
        assert self.library.books[0] == book
    
    def test_add_duplicate_book(self):
        """Aynı ISBN ile kitap ekleme testi"""
        book1 = Book("Test Kitap 1", "Test Yazar 1", "1234567890")
        book2 = Book("Test Kitap 2", "Test Yazar 2", "1234567890")
        
        # İlk kitabı ekle
        self.library.add_book(book1)
        
        # Aynı ISBN ile ikinci kitabı eklemeye çalış
        result = self.library.add_book(book2)
        
        assert result is False
        assert len(self.library.books) == 1
    
    def test_remove_book(self):
        """Kitap silme testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.library.add_book(book)
        
        result = self.library.remove_book("1234567890")
        
        assert result is True
        assert len(self.library.books) == 0
    
    def test_remove_nonexistent_book(self):
        """Var olmayan kitap silme testi"""
        result = self.library.remove_book("9999999999")
        
        assert result is False
    
    def test_find_book(self):
        """Kitap bulma testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.library.add_book(book)
        
        found_book = self.library.find_book("1234567890")
        
        assert found_book == book
    
    def test_find_nonexistent_book(self):
        """Var olmayan kitap bulma testi"""
        found_book = self.library.find_book("9999999999")
        
        assert found_book is None
    
    def test_list_books(self):
        """Kitapları listeleme testi"""
        book1 = Book("Test Kitap 1", "Test Yazar 1", "1234567890")
        book2 = Book("Test Kitap 2", "Test Yazar 2", "0987654321")
        
        self.library.add_book(book1)
        self.library.add_book(book2)
        
        books = self.library.list_books()
        
        assert len(books) == 2
        assert book1 in books
        assert book2 in books
        # Liste kopyası olduğunu kontrol et
        assert books is not self.library.books
    
    def test_save_and_load_books(self):
        """Kitapları kaydetme ve yükleme testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.library.add_book(book)
        
        # Yeni bir Library nesnesi oluştur ve aynı dosyadan yükle
        new_library = Library(self.temp_file.name)
        
        assert len(new_library.books) == 1
        assert new_library.books[0].title == "Test Kitap"
        assert new_library.books[0].author == "Test Yazar"
        assert new_library.books[0].isbn == "1234567890"
    
    @patch('models.httpx.Client')
    def test_fetch_book_from_api_success(self, mock_client):
        """API'den başarılı kitap çekme testi"""
        # Mock response'ları hazırla
        mock_book_response = Mock()
        mock_book_response.status_code = 200
        mock_book_response.json.return_value = {
            "title": "Test Kitap",
            "authors": [{"key": "/authors/OL12345A"}]
        }
        
        mock_author_response = Mock()
        mock_author_response.status_code = 200
        mock_author_response.json.return_value = {
            "name": "Test Yazar"
        }
        
        # Mock client'ı ayarla
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [mock_book_response, mock_author_response]
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Test et
        book_info = self.library._fetch_book_from_api("1234567890")
        
        assert book_info is not None
        assert book_info["title"] == "Test Kitap"
        assert book_info["author"] == "Test Yazar"
    
    @patch('models.httpx.Client')
    def test_fetch_book_from_api_not_found(self, mock_client):
        """API'den kitap bulunamama testi"""
        # Mock response hazırla
        mock_response = Mock()
        mock_response.status_code = 404
        
        # Mock client'ı ayarla
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        # Test et
        book_info = self.library._fetch_book_from_api("9999999999")
        
        assert book_info is None
    
    def test_add_book_by_isbn_success(self):
        """ISBN ile başarılı kitap ekleme testi"""
        with patch.object(self.library, '_fetch_book_from_api') as mock_fetch:
            mock_fetch.return_value = {
                "title": "Test Kitap",
                "author": "Test Yazar"
            }
            
            result = self.library.add_book_by_isbn("1234567890")
            
            assert result is not None
            assert result.title == "Test Kitap"
            assert result.author == "Test Yazar"
            assert result.isbn == "1234567890"
            assert len(self.library.books) == 1
    
    def test_add_book_by_isbn_api_failure(self):
        """ISBN ile kitap ekleme API hatası testi"""
        with patch.object(self.library, '_fetch_book_from_api') as mock_fetch:
            mock_fetch.return_value = None
            
            result = self.library.add_book_by_isbn("1234567890")
            
            assert result is None
            assert len(self.library.books) == 0
    
    def test_get_books_as_dicts(self):
        """Kitapları dictionary listesi olarak alma testi"""
        book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.library.add_book(book)
        
        books_dict = self.library.get_books_as_dicts()
        
        assert len(books_dict) == 1
        assert books_dict[0]["title"] == "Test Kitap"
        assert books_dict[0]["author"] == "Test Yazar"
        assert books_dict[0]["isbn"] == "1234567890"


if __name__ == "__main__":
    pytest.main([__file__])
