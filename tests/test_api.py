#!/usr/bin/env python3
"""
Test dosyası: api.py için testler
"""

import pytest
import tempfile
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from api import app
from models import Library, Book


class TestAPI:
    """FastAPI uygulaması için testler"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        # Geçici dosya oluştur
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write('[]')
        self.temp_file.close()
        
        # Test client'ı oluştur
        self.client = TestClient(app)
        
        # Library nesnesini geçici dosya ile oluştur
        self.test_library = Library(self.temp_file.name)
        
        # API'deki library nesnesini test library ile değiştir
        app.dependency_overrides = {}
    
    def teardown_method(self):
        """Her test sonrası çalışır"""
        # Geçici dosyayı sil
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_root_endpoint(self):
        """Ana sayfa endpoint testi - HTML döndürür"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<!DOCTYPE html>" in response.text
        assert "Kütüphane Yönetim Sistemi" in response.text
    
    def test_api_info_endpoint(self):
        """API bilgi endpoint testi"""
        response = self.client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Kütüphane API'ye Hoş Geldiniz!"
        assert data["version"] == "1.0.0"
        assert "GET /books" in data["endpoints"]
    
    def test_health_check(self):
        """Sağlık kontrolü endpoint testi"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "Kütüphane API çalışıyor"
        assert "total_books" in data
    
    def test_get_books_empty(self):
        """Boş kütüphane için GET /books testi"""
        # Test library'yi temizle
        self.test_library.books.clear()
        
        with patch('api.library', self.test_library):
            response = self.client.get("/books")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []
    
    def test_get_books_with_books(self):
        """Kitaplı kütüphane için GET /books testi"""
        # Test kitabı ekle
        test_book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.test_library.add_book(test_book)
        
        # API'deki library nesnesini test library ile değiştir
        with patch('api.library', self.test_library):
            response = self.client.get("/books")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Kitap"
            assert data[0]["author"] == "Test Yazar"
            assert data[0]["isbn"] == "1234567890"
    
    def test_post_books_success(self):
        """Başarılı kitap ekleme testi"""
        with patch('api.library', self.test_library):
            with patch.object(self.test_library, 'add_book_by_isbn') as mock_add:
                mock_book = Book("Test Kitap", "Test Yazar", "1234567890")
                mock_add.return_value = mock_book
                
                response = self.client.post(
                    "/books",
                    json={"isbn": "1234567890"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["title"] == "Test Kitap"
                assert data["author"] == "Test Yazar"
                assert data["isbn"] == "1234567890"
    
    def test_post_books_invalid_isbn(self):
        """Geçersiz ISBN ile kitap ekleme testi"""
        response = self.client.post(
            "/books",
            json={"isbn": "123"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Geçersiz ISBN formatı" in data["detail"]
    
    def test_post_books_empty_isbn(self):
        """Boş ISBN ile kitap ekleme testi"""
        response = self.client.post(
            "/books",
            json={"isbn": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Geçersiz ISBN formatı" in data["detail"]
    
    def test_post_books_duplicate_isbn(self):
        """Var olan ISBN ile kitap ekleme testi"""
        # Test kitabı ekle
        test_book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.test_library.add_book(test_book)
        
        with patch('api.library', self.test_library):
            response = self.client.post(
                "/books",
                json={"isbn": "1234567890"}
            )
            
            assert response.status_code == 409
            data = response.json()
            assert "zaten mevcut" in data["detail"]
    
    def test_post_books_api_failure(self):
        """API hatası ile kitap ekleme testi"""
        with patch('api.library', self.test_library):
            with patch.object(self.test_library, 'add_book_by_isbn') as mock_add:
                mock_add.return_value = None
                
                response = self.client.post(
                    "/books",
                    json={"isbn": "1234567890"}
                )
                
                assert response.status_code == 404
                data = response.json()
                assert "bulunamadı" in data["detail"]
    
    def test_delete_book_success(self):
        """Başarılı kitap silme testi"""
        # Test kitabı ekle
        test_book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.test_library.add_book(test_book)
        
        with patch('api.library', self.test_library):
            response = self.client.delete("/books/1234567890")
            
            assert response.status_code == 200
            data = response.json()
            assert "başarıyla silindi" in data["message"]
            assert data["deleted_isbn"] == "1234567890"
    
    def test_delete_book_not_found(self):
        """Var olmayan kitap silme testi"""
        with patch('api.library', self.test_library):
            response = self.client.delete("/books/9999999999")
            
            assert response.status_code == 404
            data = response.json()
            assert "bulunamadı" in data["detail"]
    
    def test_delete_book_invalid_isbn(self):
        """Geçersiz ISBN ile kitap silme testi"""
        response = self.client.delete("/books/123")
        
        assert response.status_code == 400
        data = response.json()
        assert "Geçersiz ISBN formatı" in data["detail"]
    
    def test_get_book_success(self):
        """Başarılı kitap bulma testi"""
        # Test kitabı ekle
        test_book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.test_library.add_book(test_book)
        
        with patch('api.library', self.test_library):
            response = self.client.get("/books/1234567890")
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Kitap"
            assert data["author"] == "Test Yazar"
            assert data["isbn"] == "1234567890"
    
    def test_get_book_not_found(self):
        """Var olmayan kitap bulma testi"""
        with patch('api.library', self.test_library):
            response = self.client.get("/books/9999999999")
            
            assert response.status_code == 404
            data = response.json()
            assert "bulunamadı" in data["detail"]
    
    def test_get_book_invalid_isbn(self):
        """Geçersiz ISBN ile kitap bulma testi"""
        response = self.client.get("/books/123")
        
        assert response.status_code == 400
        data = response.json()
        assert "Geçersiz ISBN formatı" in data["detail"]
    
    def test_missing_isbn_field(self):
        """Eksik ISBN alanı testi"""
        response = self.client.post(
            "/books",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_json(self):
        """Geçersiz JSON testi"""
        response = self.client.post(
            "/books",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__])
