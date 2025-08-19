#!/usr/bin/env python3
"""
Python 202 Bootcamp - Kütüphane Projesi
Aşama 3: FastAPI ile Web Servisi
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from models import Library, UserManager
import uvicorn
import secrets
from typing import Optional, Dict


# FastAPI uygulamasını oluştur
app = FastAPI(
    title="Kütüphane API",
    description="Python 202 Bootcamp Kütüphane Projesi - FastAPI ile Web Servisi",
    version="1.0.0"
)

# Static dosyaları serve et
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic modelleri
class ISBNRequest(BaseModel):
    """POST /books endpoint'i için ISBN request modeli"""
    isbn: str

class BookResponse(BaseModel):
    """Book response modeli"""
    title: str
    author: str
    isbn: str

class ErrorResponse(BaseModel):
    """Hata response modeli"""
    error: str
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    username: str
    role: str

class UserBookRequest(BaseModel):
    isbn: str

class UserBookResponse(BaseModel):
    title: str
    author: str
    isbn: str
    is_read: bool

class BookUpdateRequest(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None

# Library ve UserManager nesnelerini oluştur (varsayılan olarak SQLite kullan)
library = Library(db_path="app.db")
user_manager = UserManager(db_path="app.db")

# Basit token yönetimi (in-memory). Üretim için JWT önerilir.
active_tokens: Dict[str, str] = {}


@app.get("/", tags=["Ana Sayfa"])
async def root():
    """Ana sayfa - HTML arayüzü"""
    return FileResponse("static/index.html")

@app.get("/api", tags=["API Bilgi"])
async def api_info():
    """API hakkında bilgi"""
    return {
        "message": "Kütüphane API'ye Hoş Geldiniz!",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "GET /books": "Tüm kitapları listele",
            "POST /books": "ISBN ile kitap ekle",
            "DELETE /books/{isbn}": "ISBN ile kitap sil"
        }
    }


# Yardımcı auth fonksiyonları
def get_current_username(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Yetkilendirme gerekli")
    token = authorization.replace("Bearer ", "")
    username = active_tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")
    return username

def require_admin(username: str = Depends(get_current_username)) -> str:
    user = user_manager.get_user(username)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    return username


@app.get("/books", response_model=list[BookResponse], tags=["Kitaplar"])
async def get_books():
    """Kütüphanedeki tüm kitapların listesini döndürür"""
    try:
        books = library.get_books_as_dicts()
        return books
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kitaplar listelenirken hata oluştu: {str(e)}"
        )


@app.post("/books", response_model=BookResponse, tags=["Kitaplar"])
async def add_book(isbn_request: ISBNRequest):
    """ISBN ile yeni kitap ekler"""
    try:
        isbn = isbn_request.isbn.strip()
        # Kullanıcı tireli ISBN girse bile destekle
        
        # ISBN formatını kontrol et
        if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
            raise HTTPException(
                status_code=400,
                detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır."
            )
        
        # Kitabın zaten var olup olmadığını kontrol et
        existing_book = library.find_book(isbn)
        if existing_book:
            raise HTTPException(
                status_code=409,
                detail=f"Bu ISBN ({isbn}) ile kitap zaten mevcut."
            )
        
        # Open Library API'den kitap bilgilerini çek ve ekle
        book = library.add_book_by_isbn(isbn)
        
        if book:
            return book.to_dict()
        else:
            raise HTTPException(
                status_code=404,
                detail=f"ISBN {isbn} ile kitap bulunamadı veya eklenemedi."
            )
            
    except HTTPException:
        # HTTPException'ları tekrar fırlat
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kitap eklenirken beklenmeyen hata oluştu: {str(e)}"
        )


@app.delete("/books/{isbn}", tags=["Kitaplar"])
async def delete_book(isbn: str):
    """Belirtilen ISBN'e sahip kitabı kütüphaneden siler"""
    try:
        isbn = isbn.strip()
        
        # ISBN formatını kontrol et
        if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
            raise HTTPException(
                status_code=400,
                detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır."
            )
        
        # Kitabı sil
        if library.remove_book(isbn):
            return {
                "message": f"ISBN {isbn} ile kitap başarıyla silindi.",
                "deleted_isbn": isbn
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"ISBN {isbn} ile kitap bulunamadı."
            )
            
    except HTTPException:
        # HTTPException'ları tekrar fırlat
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kitap silinirken beklenmeyen hata oluştu: {str(e)}"
        )


@app.get("/books/{isbn}", response_model=BookResponse, tags=["Kitaplar"])
async def get_book(isbn: str):
    """Belirtilen ISBN'e sahip kitabı döndürür"""
    try:
        isbn = isbn.strip()
        
        # ISBN formatını kontrol et
        if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
            raise HTTPException(
                status_code=400,
                detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır."
            )
        
        # Kitabı bul
        book = library.find_book(isbn)
        if book:
            return book.to_dict()
        else:
            raise HTTPException(
                status_code=404,
                detail=f"ISBN {isbn} ile kitap bulunamadı."
            )
            
    except HTTPException:
        # HTTPException'ları tekrar fırlat
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kitap aranırken beklenmeyen hata oluştu: {str(e)}"
        )


@app.get("/health", tags=["Sistem"])
async def health_check():
    """API sağlık kontrolü"""
    return {
        "status": "healthy",
        "message": "Kütüphane API çalışıyor",
        "total_books": len(library.list_books())
    }


# Admin: Kütüphane kitap işlemleri (yetki gerekli)
@app.post("/admin/books", response_model=BookResponse, tags=["Admin"])
async def admin_add_book(isbn_request: ISBNRequest, username: str = Depends(require_admin)):
    try:
        isbn = isbn_request.isbn.strip()
        if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
            raise HTTPException(status_code=400, detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır.")
        existing_book = library.find_book(isbn)
        if existing_book:
            raise HTTPException(status_code=409, detail=f"Bu ISBN ({isbn}) ile kitap zaten mevcut.")
        book = library.add_book_by_isbn(isbn)
        if book:
            return book.to_dict()
        else:
            raise HTTPException(status_code=404, detail=f"ISBN {isbn} ile kitap bulunamadı veya eklenemedi.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kitap eklenirken beklenmeyen hata oluştu: {str(e)}")


@app.delete("/admin/books/{isbn}", tags=["Admin"])
async def admin_delete_book(isbn: str, username: str = Depends(require_admin)):
    try:
        isbn = isbn.strip()
        if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
            raise HTTPException(status_code=400, detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır.")
        if library.remove_book(isbn):
            return {"message": f"ISBN {isbn} ile kitap başarıyla silindi.", "deleted_isbn": isbn}
        else:
            raise HTTPException(status_code=404, detail=f"ISBN {isbn} ile kitap bulunamadı.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kitap silinirken beklenmeyen hata oluştu: {str(e)}")


@app.patch("/admin/books/{isbn}", response_model=BookResponse, tags=["Admin"])
async def admin_update_book(isbn: str, payload: BookUpdateRequest, username: str = Depends(require_admin)):
    try:
        if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
            raise HTTPException(status_code=400, detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır.")
        updated = library.update_book(isbn, title=payload.title, author=payload.author)
        if not updated:
            raise HTTPException(status_code=404, detail="Kitap bulunamadı")
        return updated.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kitap güncellenirken beklenmeyen hata oluştu: {str(e)}")


# Kimlik Doğrulama
@app.post("/auth/login", response_model=LoginResponse, tags=["Kimlik"])
async def login(payload: LoginRequest):
    user = user_manager.verify_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    token = secrets.token_urlsafe(24)
    active_tokens[token] = user.username
    return {"token": token, "username": user.username, "role": user.role}

@app.post("/auth/register", tags=["Kimlik"])
async def register(payload: LoginRequest):
    created = user_manager.create_user(payload.username, payload.password, role="user")
    if not created:
        raise HTTPException(status_code=400, detail="Kullanıcı oluşturulamadı. Kullanıcı mevcut olabilir.")
    return {"message": "Kullanıcı oluşturuldu"}

@app.post("/auth/logout", tags=["Kimlik"])
async def logout(username: str = Depends(get_current_username), authorization: Optional[str] = Header(default=None)):
    if authorization:
        token = authorization.replace("Bearer ", "")
        active_tokens.pop(token, None)
    return {"message": "Çıkış yapıldı"}


# Kullanıcı Kitap Listesi
@app.get("/me/books", response_model=list[UserBookResponse], tags=["Kullanıcı"])
async def me_list_books(username: str = Depends(get_current_username)):
    try:
        return user_manager.list_user_books(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kullanıcı kitapları listelenirken hata: {e}")

@app.get("/me/books/read", response_model=list[UserBookResponse], tags=["Kullanıcı"])
async def me_list_read_books(username: str = Depends(get_current_username)):
    try:
        return user_manager.list_user_read_books(username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Okunan kitaplar listelenirken hata: {e}")

@app.post("/me/books", response_model=UserBookResponse, tags=["Kullanıcı"])
async def me_add_book(payload: UserBookRequest, username: str = Depends(get_current_username)):
    isbn = payload.isbn.strip()
    if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
        raise HTTPException(status_code=400, detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır.")
    added = user_manager.add_book_to_user_by_isbn(username, isbn)
    if not added:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı veya zaten mevcut")
    return added

@app.delete("/me/books/{isbn}", tags=["Kullanıcı"])
async def me_delete_book(isbn: str, username: str = Depends(get_current_username)):
    if not isbn or len(isbn.replace('-', '').replace(' ', '')) < 10:
        raise HTTPException(status_code=400, detail="Geçersiz ISBN formatı. ISBN en az 10 karakter olmalıdır.")
    removed = user_manager.remove_user_book(username, isbn)
    if not removed:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı")
    return {"message": "Kitap silindi", "deleted_isbn": isbn}

@app.post("/me/books/{isbn}/read", response_model=UserBookResponse, tags=["Kullanıcı"])
async def me_mark_read(isbn: str, username: str = Depends(get_current_username)):
    updated = user_manager.mark_user_book_read(username, isbn, is_read=True)
    if not updated:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı")
    return updated

@app.post("/me/books/{isbn}/unread", response_model=UserBookResponse, tags=["Kullanıcı"])
async def me_mark_unread(isbn: str, username: str = Depends(get_current_username)):
    updated = user_manager.mark_user_book_read(username, isbn, is_read=False)
    if not updated:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı")
    return updated


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
