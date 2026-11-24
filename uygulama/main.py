import os
import bcrypt
import mysql.connector

from decimal import Decimal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from database.repository import (
    RepositoryValidationError,
    call_procedure,
    get_user_by_email,
    get_user_by_id,
    get_daily_menus,
    get_weekly_menus,
    get_user_reservations,
    get_balance_movements,
    get_user_reviews,
    create_review,
    get_admin_options,
    get_admin_menus,
    create_menu,
    update_menu
)


# --------------------------------------------------
# İSTEK MODELLERİ
# --------------------------------------------------

class GirisIstegi(BaseModel):
    eposta: str
    sifre: str


class RezervasyonIstegi(BaseModel):
    menu_id: int = Field(gt=0)


class DegerlendirmeIstegi(BaseModel):
    menu_id: int = Field(gt=0)
    puan: int = Field(ge=1, le=5)
    yorum: str | None = Field(default=None, max_length=500)


class BakiyeYuklemeIstegi(BaseModel):
    tutar: Decimal = Field(
        ge=10,
        le=1000,
        max_digits=10,
        decimal_places=2
    )


class MenuOlusturmaIstegi(BaseModel):
    yemekhane_id: int = Field(gt=0)
    tarih: str
    ogun_id: int = Field(gt=0)
    ogrenci_fiyati: Decimal = Field(
        ge=0,
        max_digits=8,
        decimal_places=2
    )
    personel_fiyati: Decimal = Field(
        ge=0,
        max_digits=8,
        decimal_places=2
    )
    yemek_idleri: list[int] = Field(min_length=1)


class MenuDuzenlemeIstegi(BaseModel):
    yemekhane_id: int = Field(gt=0)
    tarih: str
    ogun_id: int = Field(gt=0)
    ogrenci_fiyati: Decimal = Field(
        ge=0,
        max_digits=8,
        decimal_places=2
    )
    personel_fiyati: Decimal = Field(
        ge=0,
        max_digits=8,
        decimal_places=2
    )
    yemek_idleri: list[int] = Field(min_length=1)


# --------------------------------------------------
# FASTAPI UYGULAMASI
# --------------------------------------------------

app = FastAPI(
    title="Yemekhane Otomasyonu API",
    description="Yemekhane otomasyonu Web API uygulaması",
    version="1.0.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SESSION_SECRET_KEY"],
    session_cookie="yemekhane_oturum",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=False
)


# --------------------------------------------------
# OTURUM VE YETKİ KONTROLLERİ
# --------------------------------------------------

def kullanici_bilgisi(kullanici):
    return {
        "id": kullanici["id"],
        "ad": kullanici["ad"],
        "soyad": kullanici["soyad"],
        "eposta": kullanici["eposta"],
        "rol": kullanici["rol"],
        "bakiye": str(kullanici["bakiye"])
    }


def aktif_oturum_kullanicisi(request: Request):
    kullanici_id = request.session.get("kullanici_id")

    if not kullanici_id:
        raise HTTPException(
            status_code=401,
            detail="Bu işlem için giriş yapmalısınız."
        )

    kullanici = get_user_by_id(kullanici_id)

    if not kullanici or not kullanici["aktif"]:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="Oturum geçersiz. Tekrar giriş yapmalısınız."
        )

    return kullanici


def yonetici_kontrol(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)

    if kullanici["rol"] != "yonetici":
        raise HTTPException(
            status_code=403,
            detail="Bu işlem yalnızca yöneticilere açıktır."
        )

    return kullanici


def repository_hatasini_http_hatasina_cevir(hata):
    raise HTTPException(
        status_code=hata.status_code,
        detail=hata.message
    )


# --------------------------------------------------
# ANA SAYFA
# --------------------------------------------------

@app.get("/api/")
def ana_sayfa():
    return {
        "mesaj": "Yemekhane Otomasyonu API çalışıyor",
        "durum": "basarili"
    }


# --------------------------------------------------
# MENÜLER
# --------------------------------------------------

@app.get("/api/menuler")
def menu_listesi():
    return get_daily_menus()


@app.get("/api/haftalik-menuler")
def haftalik_menu_listesi():
    return get_weekly_menus()


# --------------------------------------------------
# GİRİŞ / OTURUM / ÇIKIŞ
# --------------------------------------------------

@app.post("/api/giris")
def giris_yap(istek: GirisIstegi, request: Request):
    kullanici = get_user_by_email(istek.eposta)

    if not kullanici or not kullanici["aktif"]:
        raise HTTPException(
            status_code=401,
            detail="E-posta veya şifre hatalı."
        )

    try:
        sifre_dogru = bcrypt.checkpw(
            istek.sifre.encode("utf-8"),
            kullanici["sifre_hash"].encode("utf-8")
        )
    except (ValueError, TypeError):
        sifre_dogru = False

    if not sifre_dogru:
        raise HTTPException(
            status_code=401,
            detail="E-posta veya şifre hatalı."
        )

    request.session.clear()
    request.session["kullanici_id"] = kullanici["id"]

    return {
        "mesaj": "Giriş başarılı.",
        "kullanici": kullanici_bilgisi(kullanici)
    }


@app.get("/api/oturum")
def oturum_kontrol(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)

    return {
        "giris_yapildi": True,
        "kullanici": kullanici_bilgisi(kullanici)
    }


@app.post("/api/cikis")
def cikis_yap(request: Request):
    request.session.clear()

    return {
        "mesaj": "Başarıyla çıkış yapıldı.",
        "giris_yapildi": False
    }


# --------------------------------------------------
# REZERVASYON OLUŞTURMA
# --------------------------------------------------

@app.post("/api/rezervasyonlar")
def rezervasyon_yap(
    istek: RezervasyonIstegi,
    request: Request
):
    kullanici = aktif_oturum_kullanicisi(request)

    try:
        sonuc = call_procedure(
            "sp_rezervasyon_yap",
            (
                kullanici["id"],
                istek.menu_id
            )
        )

        if not sonuc or not sonuc[0]:
            raise HTTPException(
                status_code=500,
                detail="Rezervasyon sonucu alınamadı."
            )

        rezervasyon = sonuc[0][0]

        return {
            "mesaj": "Rezervasyon başarıyla oluşturuldu.",
            "rezervasyon_id": rezervasyon["rezervasyon_id"],
            "ucret": str(rezervasyon["ucret"]),
            "bakiye": str(rezervasyon["bakiye"])
        }

    except mysql.connector.Error as hata:
        if hata.sqlstate == "45000":
            raise HTTPException(
                status_code=400,
                detail=hata.msg
            )

        raise HTTPException(
            status_code=500,
            detail="Rezervasyon işlemi sırasında veritabanı hatası oluştu."
        )


# --------------------------------------------------
# KULLANICININ REZERVASYONLARI
# --------------------------------------------------

@app.get("/api/rezervasyonlarim")
def rezervasyonlarimi_getir(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)

    return {
        "rezervasyonlar": get_user_reservations(kullanici["id"])
    }


# --------------------------------------------------
# REZERVASYON İPTALİ
# --------------------------------------------------

@app.post("/api/rezervasyonlarim/{rezervasyon_id}/iptal")
def rezervasyon_iptal(
    rezervasyon_id: int,
    request: Request
):
    if rezervasyon_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz rezervasyon numarası."
        )

    kullanici = aktif_oturum_kullanicisi(request)

    try:
        sonuc = call_procedure(
            "sp_rezervasyon_iptal",
            (
                kullanici["id"],
                rezervasyon_id
            )
        )

        if not sonuc or not sonuc[0]:
            raise HTTPException(
                status_code=500,
                detail="İptal sonucu alınamadı."
            )

        iptal = sonuc[0][0]

        return {
            "mesaj": "Rezervasyon başarıyla iptal edildi.",
            "rezervasyon_id": iptal["rezervasyon_id"],
            "iade": str(iptal["iade"]),
            "bakiye": str(iptal["bakiye"])
        }

    except mysql.connector.Error as hata:
        if hata.sqlstate == "45000":
            raise HTTPException(
                status_code=400,
                detail=hata.msg
            )

        raise HTTPException(
            status_code=500,
            detail="Rezervasyon iptali sırasında veritabanı hatası oluştu."
        )


# --------------------------------------------------
# BAKİYE VE HAREKET GEÇMİŞİ
# --------------------------------------------------

@app.get("/api/bakiye")
def bakiye_bilgilerini_getir(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)

    return {
        "bakiye": str(kullanici["bakiye"]),
        "hareketler": get_balance_movements(kullanici["id"])
    }


# --------------------------------------------------
# BAKİYE YÜKLEME
# --------------------------------------------------

@app.post("/api/bakiye/yukle")
def bakiye_yukle(
    istek: BakiyeYuklemeIstegi,
    request: Request
):
    kullanici = aktif_oturum_kullanicisi(request)

    try:
        sonuc = call_procedure(
            "sp_bakiye_yukle",
            (
                kullanici["id"],
                istek.tutar
            )
        )

        if not sonuc or not sonuc[0]:
            raise HTTPException(
                status_code=500,
                detail="Bakiye yükleme sonucu alınamadı."
            )

        yukleme = sonuc[0][0]

        return {
            "mesaj": "Bakiye başarıyla yüklendi.",
            "hareket_id": yukleme["hareket_id"],
            "bakiye": str(yukleme["bakiye"])
        }

    except mysql.connector.Error as hata:
        if hata.sqlstate == "45000":
            raise HTTPException(
                status_code=400,
                detail=hata.msg
            )

        raise HTTPException(
            status_code=500,
            detail="Bakiye yükleme sırasında veritabanı hatası oluştu."
        )


# --------------------------------------------------
# KULLANICININ DEĞERLENDİRMELERİ
# --------------------------------------------------

@app.get("/api/degerlendirmelerim")
def degerlendirmelerimi_getir(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)

    return {
        "menuler": get_user_reviews(kullanici["id"])
    }


# --------------------------------------------------
# DEĞERLENDİRME EKLEME
# --------------------------------------------------

@app.post("/api/degerlendirmeler")
def degerlendirme_ekle(
    istek: DegerlendirmeIstegi,
    request: Request
):
    kullanici = aktif_oturum_kullanicisi(request)

    try:
        degerlendirme_id = create_review(
            kullanici["id"],
            istek.menu_id,
            istek.puan,
            istek.yorum
        )

        return {
            "mesaj": "Değerlendirmeniz kaydedildi.",
            "degerlendirme_id": degerlendirme_id
        }

    except RepositoryValidationError as hata:
        repository_hatasini_http_hatasina_cevir(hata)

    except mysql.connector.IntegrityError as hata:
        if hata.errno == 1062:
            raise HTTPException(
                status_code=409,
                detail="Bu menüye daha önce değerlendirme yaptınız."
            )

        raise HTTPException(
            status_code=400,
            detail="Değerlendirme kaydedilemedi."
        )

    except mysql.connector.Error:
        raise HTTPException(
            status_code=500,
            detail="Veritabanı hatası oluştu."
        )


# --------------------------------------------------
# YÖNETİCİ - SEÇENEKLER
# --------------------------------------------------

@app.get("/api/yonetici/secenekler")
def yonetici_secenekleri(request: Request):
    yonetici_kontrol(request)
    return get_admin_options()


# --------------------------------------------------
# YÖNETİCİ - MENÜLER
# --------------------------------------------------

@app.get("/api/yonetici/menuler")
def yonetici_menuleri(request: Request):
    yonetici_kontrol(request)

    return {
        "menuler": get_admin_menus()
    }


# --------------------------------------------------
# YÖNETİCİ - MENÜ OLUŞTURMA
# --------------------------------------------------

@app.post("/api/yonetici/menuler")
def yonetici_menu_olustur(
    istek: MenuOlusturmaIstegi,
    request: Request
):
    yonetici_kontrol(request)

    try:
        menu_id = create_menu(
            istek.yemekhane_id,
            istek.tarih,
            istek.ogun_id,
            istek.ogrenci_fiyati,
            istek.personel_fiyati,
            istek.yemek_idleri
        )

        return {
            "mesaj": "Menü başarıyla oluşturuldu.",
            "menu_id": menu_id
        }

    except RepositoryValidationError as hata:
        repository_hatasini_http_hatasina_cevir(hata)

    except mysql.connector.Error as hata:
        if hata.errno == 1062:
            raise HTTPException(
                status_code=409,
                detail="Bu yemekhane, tarih ve öğün için zaten menü var."
            )

        raise HTTPException(
            status_code=400,
            detail="Menü oluşturulamadı. Girdiğiniz bilgileri kontrol edin."
        )


# --------------------------------------------------
# YÖNETİCİ - MENÜ DÜZENLEME
# --------------------------------------------------

@app.put("/api/yonetici/menuler/{menu_id}")
def yonetici_menu_duzenle(
    menu_id: int,
    istek: MenuDuzenlemeIstegi,
    request: Request
):
    yonetici_kontrol(request)

    if menu_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Geçersiz menü numarası."
        )

    try:
        update_menu(
            menu_id,
            istek.yemekhane_id,
            istek.tarih,
            istek.ogun_id,
            istek.ogrenci_fiyati,
            istek.personel_fiyati,
            istek.yemek_idleri
        )

        return {
            "mesaj": "Menü başarıyla güncellendi.",
            "menu_id": menu_id
        }

    except RepositoryValidationError as hata:
        repository_hatasini_http_hatasina_cevir(hata)

    except mysql.connector.Error as hata:
        if hata.errno == 1062:
            raise HTTPException(
                status_code=409,
                detail="Bu yemekhane, tarih ve öğün için başka bir menü zaten var."
            )

        raise HTTPException(
            status_code=400,
            detail="Menü güncellenemedi. Girdiğiniz bilgileri kontrol edin."
        )