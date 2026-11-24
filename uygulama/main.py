
import os
import json
import secrets
import redis

from datetime import datetime, date, timedelta
import bcrypt
import mysql.connector

from decimal import Decimal

from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


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
    update_menu,
    get_all_allergens,
    get_user_allergen_ids,
    set_user_allergens
)


# --------------------------------------------------
# İSTEK MODELLERİ
# --------------------------------------------------

class GirisIstegi(BaseModel):
    eposta: str
    sifre: str


class RezervasyonIstegi(BaseModel):
    menu_id: int = Field(gt=0)
    yarim_porsiyon: bool = False


class AlerjenTercihiIstegi(BaseModel):
    alerjen_idleri: list[int] = Field(default_factory=list)


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

# --------------------------------------------------
# REDIS BAĞLANTISI
# --------------------------------------------------

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
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
    token = request.cookies.get("yemekhane_oturum")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Bu işlem için giriş yapmalısınız."
        )

    oturum_key = f"oturum:{token}"
    kullanici_id = redis_client.get(oturum_key)

    if not kullanici_id:
        raise HTTPException(
            status_code=401,
            detail="Oturum geçersiz. Tekrar giriş yapmalısınız."
        )

    # Her istekte oturum süresini 30 dakika yenile
    redis_client.expire(oturum_key, 1800)

    kullanici = get_user_by_id(int(kullanici_id))

    if not kullanici or not kullanici["aktif"]:
        redis_client.delete(oturum_key)
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

def menu_onbellek_suresi():
    simdi = datetime.now()
    yarin = date.today() + timedelta(days=1)
    gun_sonu = datetime.combine(yarin, datetime.min.time())
    return max(1, int((gun_sonu - simdi).total_seconds()))


def menu_onbellegini_temizle():
    anahtarlar = list(redis_client.scan_iter(match="menu:*"))
    if anahtarlar:
        redis_client.delete(*anahtarlar)
    print("ONBELLEK SIL - Menü önbelleği temizlendi.")


@app.get("/api/menuler")
def menu_listesi():
    bugun = date.today().isoformat()
    liste_key = f"menu:liste:{bugun}"

    menu_keyleri = redis_client.smembers(liste_key)

    if menu_keyleri:
        onbellek_verileri = redis_client.mget(list(menu_keyleri))

        if all(veri is not None for veri in onbellek_verileri):
            sonuc = [
                satir
                for veri in onbellek_verileri
                for satir in json.loads(veri)
            ]
            sonuc.sort(
                key=lambda satir: (
                    str(satir["tarih"]),
                    satir["yemekhane_id"],
                    satir["ogun_sira"],
                    satir["kategori_sira"]
                )
            )
            print("ONBELLEK HIT - Menüler Redis'ten getirildi.")
            return sonuc

    print("ONBELLEK MISS - Menüler veritabanından getirildi.")

    menuler = get_daily_menus()
    gruplar = {}

    for menu in menuler:
        tarih = str(menu["tarih"])
        yemekhane_id = menu["yemekhane_id"]
        ogun_id = menu["ogun_id"]
        key = f"menu:{yemekhane_id}:{tarih}:{ogun_id}"
        gruplar.setdefault(key, []).append(menu)

    ttl = menu_onbellek_suresi()

    if gruplar:
        redis_client.delete(liste_key)
        for key, satirlar in gruplar.items():
            veri = json.dumps(
                jsonable_encoder(satirlar),
                ensure_ascii=False
            )
            redis_client.setex(key, ttl, veri)

        redis_client.sadd(liste_key, *gruplar.keys())
        redis_client.expire(liste_key, ttl)

    return menuler


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

    # Önceki oturumu varsa sil
    eski_token = request.cookies.get("yemekhane_oturum")
    if eski_token:
        redis_client.delete(f"oturum:{eski_token}")

    # Yeni oturum oluştur
    token = secrets.token_urlsafe(32)
    redis_client.setex(
        f"oturum:{token}",
        1800,
        str(kullanici["id"])
    )

    yanit = JSONResponse(content={
        "mesaj": "Giriş başarılı.",
        "kullanici": kullanici_bilgisi(kullanici)
    })

    yanit.set_cookie(
        key="yemekhane_oturum",
        value=token,
        max_age=1800,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return yanit


@app.get("/api/oturum")
def oturum_kontrol(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)

    return {
        "giris_yapildi": True,
        "kullanici": kullanici_bilgisi(kullanici)
    }


@app.post("/api/cikis")
def cikis_yap(request: Request):
    token = request.cookies.get("yemekhane_oturum")

    if token:
        redis_client.delete(f"oturum:{token}")

    yanit = JSONResponse(content={
        "mesaj": "Başarıyla çıkış yapıldı.",
        "giris_yapildi": False
    })

    yanit.delete_cookie("yemekhane_oturum")

    return yanit


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
                istek.menu_id,
                int(istek.yarim_porsiyon)
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
            "bakiye": str(rezervasyon["bakiye"]),
            "yarim_porsiyon": bool(rezervasyon.get("yarim_porsiyon", istek.yarim_porsiyon))
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

@app.get("/api/alerjen-tercihleri")
def alerjen_tercihlerini_getir(request: Request):
    kullanici = aktif_oturum_kullanicisi(request)
    return {
        "alerjenler": get_all_allergens(),
        "secili_alerjen_idleri": get_user_allergen_ids(kullanici["id"])
    }


@app.put("/api/alerjen-tercihleri")
def alerjen_tercihlerini_kaydet(istek: AlerjenTercihiIstegi, request: Request):
    kullanici = aktif_oturum_kullanicisi(request)
    mevcut = {int(a["id"]) for a in get_all_allergens()}
    secilen = set(istek.alerjen_idleri)
    if not secilen.issubset(mevcut):
        raise HTTPException(status_code=400, detail="Geçersiz alerjen seçimi.")
    try:
        set_user_allergens(kullanici["id"], secilen)
    except mysql.connector.Error:
        raise HTTPException(status_code=500, detail="Alerjen tercihleri kaydedilemedi.")
    return {"mesaj": "Alerjen tercihleriniz kaydedildi.", "secili_alerjen_idleri": sorted(secilen)}


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

        menu_onbellegini_temizle()

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

        menu_onbellegini_temizle()

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
