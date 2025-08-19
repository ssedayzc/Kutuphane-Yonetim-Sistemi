#!/usr/bin/env python3
"""
Test dosyası: main.py için testler
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from models import Library, Book


class TestMainFunctions:
    """main.py fonksiyonları için testler"""
    
    def setup_method(self):
        """Her test öncesi çalışır"""
        # Geçici dosya oluştur
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write('[]')
        self.temp_file.close()
        
        # Test library oluştur
        self.library = Library(self.temp_file.name)
    
    def teardown_method(self):
        """Her test sonrası çalışır"""
        # Geçici dosyayı sil
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_add_book_success(self, mock_print, mock_input):
        """Başarılı kitap ekleme testi"""
        # Mock input'ları ayarla
        mock_input.return_value = "978-0199535675"
        
        # Mock add_book_by_isbn metodunu ayarla
        with patch.object(self.library, 'add_book_by_isbn') as mock_add:
            mock_book = Book("Ulysses", "James Joyce", "978-0199535675")
            mock_add.return_value = mock_book
            
            # main.py'deki add_book fonksiyonunu import et ve test et
            from main import add_book
            add_book(self.library)
            
            # Beklenen çıktıları kontrol et
            mock_add.assert_called_once_with("978-0199535675")
            # Başarı mesajının yazdırıldığını kontrol et
            mock_print.assert_any_call("✓ Kitap başarıyla eklendi: Ulysses by James Joyce (ISBN: 978-0199535675)")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_add_book_empty_isbn(self, mock_print, mock_input):
        """Boş ISBN ile kitap ekleme testi"""
        # Mock input'ları ayarla
        mock_input.return_value = ""
        
        from main import add_book
        add_book(self.library)
        
        # Hata mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("ISBN numarası boş olamaz!")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_add_book_short_isbn(self, mock_print, mock_input):
        """Kısa ISBN ile kitap ekleme testi"""
        # Mock input'ları ayarla
        mock_input.return_value = "123"
        
        from main import add_book
        add_book(self.library)
        
        # Hata mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_add_book_api_failure(self, mock_print, mock_input):
        """API hatası ile kitap ekleme testi"""
        # Mock input'ları ayarla
        mock_input.return_value = "978-0199535675"
        
        # Mock add_book_by_isbn metodunu ayarla
        with patch.object(self.library, 'add_book_by_isbn') as mock_add:
            mock_add.return_value = None
            
            from main import add_book
            add_book(self.library)
            
            # Hata mesajının yazdırıldığını kontrol et
            mock_print.assert_any_call("❌ Kitap eklenemedi. Kitap bulunamadı veya zaten mevcut.")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_remove_book_success(self, mock_print, mock_input):
        """Başarılı kitap silme testi"""
        # Test kitabı ekle
        test_book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.library.add_book(test_book)
        
        # Mock input'ları ayarla
        mock_input.return_value = "1234567890"
        
        from main import remove_book
        remove_book(self.library)
        
        # Başarı mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("✓ Kitap başarıyla silindi.")
        # Kitabın gerçekten silindiğini kontrol et
        assert self.library.find_book("1234567890") is None
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_remove_book_not_found(self, mock_print, mock_input):
        """Var olmayan kitap silme testi"""
        # Mock input'ları ayarla
        mock_input.return_value = "9999999999"
        
        from main import remove_book
        remove_book(self.library)
        
        # Hata mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("❌ Kitap bulunamadı.")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_remove_book_empty_isbn(self, mock_print, mock_input):
        """Boş ISBN ile kitap silme testi"""
        # Mock input'ları ayarla
        mock_input.return_value = ""
        
        from main import remove_book
        remove_book(self.library)
        
        # Hata mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("ISBN numarası boş olamaz!")
    
    @patch('builtins.print')
    def test_list_books_empty(self, mock_print):
        """Boş kütüphane listeleme testi"""
        from main import list_books
        list_books(self.library)
        
        # Boş kütüphane mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("Kütüphanede henüz kitap bulunmuyor.")
    
    @patch('builtins.print')
    def test_list_books_with_books(self, mock_print):
        """Kitaplı kütüphane listeleme testi"""
        # Test kitapları ekle
        test_book1 = Book("Test Kitap 1", "Test Yazar 1", "1234567890")
        test_book2 = Book("Test Kitap 2", "Test Yazar 2", "0987654321")
        self.library.add_book(test_book1)
        self.library.add_book(test_book2)
        
        from main import list_books
        list_books(self.library)
        
        # Kitapların listelendiğini kontrol et
        mock_print.assert_any_call("1. Test Kitap 1 by Test Yazar 1 (ISBN: 1234567890)")
        mock_print.assert_any_call("2. Test Kitap 2 by Test Yazar 2 (ISBN: 0987654321)")
        mock_print.assert_any_call("Toplam 2 kitap bulunuyor.")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_find_book_success(self, mock_print, mock_input):
        """Başarılı kitap bulma testi"""
        # Test kitabı ekle
        test_book = Book("Test Kitap", "Test Yazar", "1234567890")
        self.library.add_book(test_book)
        
        # Mock input'ları ayarla
        mock_input.return_value = "1234567890"
        
        from main import find_book
        find_book(self.library)
        
        # Başarı mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("✓ Kitap bulundu: Test Kitap by Test Yazar (ISBN: 1234567890)")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_find_book_not_found(self, mock_print, mock_input):
        """Var olmayan kitap bulma testi"""
        # Mock input'ları ayarla
        mock_input.return_value = "9999999999"
        
        from main import find_book
        find_book(self.library)
        
        # Hata mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("❌ Kitap bulunamadı.")
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_find_book_empty_isbn(self, mock_print, mock_input):
        """Boş ISBN ile kitap bulma testi"""
        # Mock input'ları ayarla
        mock_input.return_value = ""
        
        from main import find_book
        find_book(self.library)
        
        # Hata mesajının yazdırıldığını kontrol et
        mock_print.assert_any_call("ISBN numarası boş olamaz!")


if __name__ == "__main__":
    pytest.main([__file__])
