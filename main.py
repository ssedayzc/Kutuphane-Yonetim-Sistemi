#!/usr/bin/env python3
"""
Python 202 Bootcamp - Kütüphane Projesi
Aşama 1 ve 2: Terminal Uygulaması
"""

from models import Library, Book


def print_menu():
    """Ana menüyü yazdırır"""
    print("\n" + "="*50)
    print("           KÜTÜPHANE YÖNETİM SİSTEMİ")
    print("="*50)
    print("1. Kitap Ekle (ISBN ile)")
    print("2. Kitap Sil")
    print("3. Kitapları Listele")
    print("4. Kitap Ara")
    print("5. Çıkış")
    print("="*50)


def add_book(library: Library):
    """ISBN ile kitap ekleme işlemi"""
    print("\n--- Kitap Ekleme ---")
    isbn = input("ISBN numarasını girin: ").strip()
    
    if not isbn:
        print("ISBN numarası boş olamaz!")
        return
    
    # ISBN formatını kontrol et (tire ve boşlukları çıkararak)
    clean_isbn = isbn.replace("-", "").replace(" ", "").replace(".", "").replace("_", "")
    if len(clean_isbn) < 10:
        print("Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.")
        return
    
    print("Kitap bilgileri Open Library API'den çekiliyor...")
    book = library.add_book_by_isbn(isbn)
    
    if book:
        print(f"✓ Kitap başarıyla eklendi: {book}")
    else:
        print("❌ Kitap eklenemedi. Kitap bulunamadı veya zaten mevcut.")


def remove_book(library: Library):
    """Kitap silme işlemi"""
    print("\n--- Kitap Silme ---")
    isbn = input("Silinecek kitabın ISBN numarasını girin: ").strip()
    
    if not isbn:
        print("ISBN numarası boş olamaz!")
        return
    
    # ISBN formatını kontrol et (tire ve boşlukları çıkararak)
    clean_isbn = isbn.replace("-", "").replace(" ", "").replace(".", "").replace("_", "")
    if len(clean_isbn) < 10:
        print("Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.")
        return
    
    if library.remove_book(isbn):
        print("✓ Kitap başarıyla silindi.")
    else:
        print("❌ Kitap bulunamadı.")


def list_books(library: Library):
    """Kitapları listeleme işlemi"""
    print("\n--- Kütüphanedeki Kitaplar ---")
    books = library.list_books()
    
    if not books:
        print("Kütüphanede henüz kitap bulunmuyor.")
        return
    
    for i, book in enumerate(books, 1):
        print(f"{i}. {book}")
    
    print(f"Toplam {len(books)} kitap bulunuyor.")


def find_book(library: Library):
    """Kitap arama işlemi"""
    print("\n--- Kitap Arama ---")
    isbn = input("Aranacak kitabın ISBN numarasını girin: ").strip()
    
    if not isbn:
        print("ISBN numarası boş olamaz!")
        return
    
    # ISBN formatını kontrol et (tire ve boşlukları çıkararak)
    clean_isbn = isbn.replace("-", "").replace(" ", "").replace(".", "").replace("_", "")
    if len(clean_isbn) < 10:
        print("Geçersiz ISBN formatı! ISBN en az 10 karakter olmalıdır.")
        return
    
    book = library.find_book(isbn)
    if book:
        print(f"✓ Kitap bulundu: {book}")
    else:
        print("❌ Kitap bulunamadı.")


def main():
    """Ana uygulama döngüsü"""
    print("Kütüphane Yönetim Sistemi başlatılıyor...")
    
    # Library nesnesini oluştur
    library = Library()
    
    print("✓ Kütüphane sistemi hazır!")
    
    while True:
        print_menu()
        
        try:
            choice = input("\nSeçiminizi yapın (1-5): ").strip()
            
            if choice == "1":
                add_book(library)
            elif choice == "2":
                remove_book(library)
            elif choice == "3":
                list_books(library)
            elif choice == "4":
                find_book(library)
            elif choice == "5":
                print("\nKütüphane sistemi kapatılıyor...")
                print("✓ Değişiklikler kaydedildi. Güle güle!")
                break
            else:
                print("❌ Geçersiz seçim! Lütfen 1-5 arasında bir sayı girin.")
                
        except KeyboardInterrupt:
            print("\n\nProgram kullanıcı tarafından kesildi.")
            print("✓ Değişiklikler kaydedildi. Güle güle!")
            break
        except Exception as e:
            print(f"\n❌ Beklenmeyen bir hata oluştu: {e}")
            print("Lütfen tekrar deneyin.")


if __name__ == "__main__":
    main()

"""
ISBN formatları:
978-0-441-17271-9 (Dune)
9780316769480 (The Catcher in the Rye)
978-0-452-28423-4 (1984)

"""