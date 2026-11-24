
from database.connection import (
    get_write_connection,
    get_read_connection
)


# ========================================
# REPOSITORY HATALARI
# ========================================

class RepositoryValidationError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ========================================
# TEMEL VERİTABANI İŞLEMLERİ
# ========================================

def execute_read(query, params=None):
    connection = get_read_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def execute_write(query, params=None):
    connection = get_write_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def call_procedure(name, params):
    connection = get_write_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.callproc(name, params)

        results = []

        for result in cursor.stored_results():
            results.append(result.fetchall())

        connection.commit()
        return results

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ========================================
# KULLANICI İŞLEMLERİ
# ========================================

def get_user_by_email(email):
    connection = get_write_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                ad,
                soyad,
                eposta,
                sifre_hash,
                rol,
                bakiye,
                aktif
            FROM kullanicilar
            WHERE eposta = %s
            LIMIT 1
            """,
            (email,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_user_by_id(user_id):
    connection = get_write_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                ad,
                soyad,
                eposta,
                rol,
                bakiye,
                aktif
            FROM kullanicilar
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


# ========================================
# GÜNÜN MENÜSÜ
# ========================================

def get_daily_menus():
    query = """
        SELECT *
        FROM v_menu_detay
        WHERE tarih = CURDATE()
        ORDER BY
            tarih,
            yemekhane_id,
            ogun_sira,
            kategori_sira
    """

    return execute_read(query)


# ========================================
# HAFTALIK MENÜLER
# ========================================

def get_weekly_menus():
    query = """
        SELECT
            m.*,
            d.kapasite,
            d.rezerve,
            d.bos_yer,
            d.doluluk_yuzde,
            d.rezervasyon_son
        FROM v_menu_detay AS m
        INNER JOIN v_menu_doluluk AS d
            ON m.menu_id = d.menu_id
        WHERE m.tarih BETWEEN
            DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
            AND
            DATE_ADD(
                DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY),
                INTERVAL 6 DAY
            )
        ORDER BY
            m.tarih,
            m.yemekhane_id,
            m.ogun_sira,
            m.kategori_sira
    """

    return execute_read(query)


# ========================================
# REZERVASYONLARIM
# ========================================

def get_user_reservations(user_id):
    query = """
        SELECT
            r.id AS rezervasyon_id,
            r.durum,
            r.ucret,
            r.olusturma,
            r.kullanma_zamani,
            r.iptal_zamani,
            m.id AS menu_id,
            m.tarih,
            yh.ad AS yemekhane,
            o.ad AS ogun,
            TIMESTAMP(m.tarih, o.son_saat) AS rezervasyon_son,
            (
                r.durum = 'aktif'
                AND NOW() < TIMESTAMP(m.tarih, o.son_saat)
            ) AS iptal_edilebilir,
            d.id AS degerlendirme_id,
            d.puan AS degerlendirme_puani,
            d.yorum AS degerlendirme_yorumu
        FROM rezervasyonlar AS r
        INNER JOIN menuler AS m
            ON m.id = r.menu_id
        INNER JOIN yemekhaneler AS yh
            ON yh.id = m.yemekhane_id
        INNER JOIN ogunler AS o
            ON o.id = m.ogun_id
        LEFT JOIN degerlendirmeler AS d
            ON d.menu_id = r.menu_id
            AND d.kullanici_id = r.kullanici_id
        WHERE r.kullanici_id = %s
        ORDER BY r.olusturma DESC, r.id DESC
    """

    return execute_read(query, (user_id,))


# ========================================
# BAKİYE HAREKETLERİ
# ========================================

def get_balance_movements(user_id):
    query = """
        SELECT
            id AS hareket_id,
            tur,
            tutar,
            rezervasyon_id,
            aciklama,
            olusturma
        FROM bakiye_hareketleri
        WHERE kullanici_id = %s
        ORDER BY olusturma DESC, id DESC
    """

    return execute_read(query, (user_id,))


# ========================================
# KULLANICININ DEĞERLENDİRMELERİ
# ========================================

def get_user_reviews(user_id):
    query = """
        SELECT
            m.id AS menu_id,
            m.tarih,
            yh.ad AS yemekhane,
            o.ad AS ogun,
            r.kullanma_zamani,
            d.id AS degerlendirme_id,
            d.puan,
            d.yorum,
            d.olusturma AS degerlendirme_tarihi
        FROM rezervasyonlar AS r
        INNER JOIN menuler AS m
            ON m.id = r.menu_id
        INNER JOIN yemekhaneler AS yh
            ON yh.id = m.yemekhane_id
        INNER JOIN ogunler AS o
            ON o.id = m.ogun_id
        LEFT JOIN degerlendirmeler AS d
            ON d.menu_id = r.menu_id
            AND d.kullanici_id = r.kullanici_id
        WHERE r.kullanici_id = %s
          AND r.durum = 'kullanildi'
        ORDER BY m.tarih DESC, r.kullanma_zamani DESC
    """

    return execute_read(query, (user_id,))


# ========================================
# DEĞERLENDİRME EKLEME
# ========================================

def create_review(user_id, menu_id, puan, yorum):
    connection = get_write_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM rezervasyonlar
            WHERE kullanici_id = %s
              AND menu_id = %s
              AND durum = 'kullanildi'
            LIMIT 1
            FOR UPDATE
            """,
            (user_id, menu_id)
        )

        rezervasyon = cursor.fetchone()

        if not rezervasyon:
            raise RepositoryValidationError(
                "Yalnızca kullanılmış menüler değerlendirilebilir.",
                403
            )

        cursor.execute(
            """
            INSERT INTO degerlendirmeler
                (kullanici_id, menu_id, puan, yorum)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                menu_id,
                puan,
                yorum.strip() if yorum else None
            )
        )

        degerlendirme_id = cursor.lastrowid
        connection.commit()

        return degerlendirme_id

    except RepositoryValidationError:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ========================================
# YÖNETİCİ PANELİ - SEÇENEKLER
# ========================================

def get_admin_options():
    return {
        "yemekhaneler": execute_read(
            """
            SELECT id, ad
            FROM yemekhaneler
            ORDER BY ad
            """
        ),

        "ogunler": execute_read(
            """
            SELECT id, ad
            FROM ogunler
            ORDER BY sira
            """
        ),

        "yemekler": execute_read(
            """
            SELECT id, ad, kalori
            FROM yemekler
            ORDER BY ad
            """
        )
    }


# ========================================
# YÖNETİCİ PANELİ - MENÜLER VE RAPORLAR
# ========================================

def get_admin_menus():
    query = """
        SELECT
            m.id AS menu_id,
            m.tarih,
            m.yemekhane_id,
            yh.ad AS yemekhane,
            m.ogun_id,
            o.ad AS ogun,
            m.ogrenci_fiyati,
            m.personel_fiyati,

            d.kapasite,
            d.rezerve,
            d.bos_yer,
            d.doluluk_yuzde,
            d.rezervasyon_son,

            COALESCE(p.ortalama_puan, 0) AS ortalama_puan,
            COALESCE(p.oy_sayisi, 0) AS oy_sayisi,

            (
                SELECT GROUP_CONCAT(
                    y.ad
                    ORDER BY y.ad
                    SEPARATOR ', '
                )
                FROM menu_yemekleri AS my
                INNER JOIN yemekler AS y
                    ON y.id = my.yemek_id
                WHERE my.menu_id = m.id
            ) AS yemekler,

            (
                SELECT GROUP_CONCAT(
                    my.yemek_id
                    ORDER BY my.yemek_id
                    SEPARATOR ','
                )
                FROM menu_yemekleri AS my
                WHERE my.menu_id = m.id
            ) AS yemek_idleri

        FROM menuler AS m

        INNER JOIN yemekhaneler AS yh
            ON yh.id = m.yemekhane_id

        INNER JOIN ogunler AS o
            ON o.id = m.ogun_id

        INNER JOIN v_menu_doluluk AS d
            ON d.menu_id = m.id

        LEFT JOIN v_menu_puan AS p
            ON p.menu_id = m.id

        ORDER BY
            m.tarih DESC,
            m.yemekhane_id,
            o.sira
    """

    return execute_read(query)


# ========================================
# YÖNETİCİ PANELİ - MENÜ OLUŞTURMA
# ========================================

def create_menu(
    yemekhane_id,
    tarih,
    ogun_id,
    ogrenci_fiyati,
    personel_fiyati,
    yemek_idleri
):
    yemek_idleri = list(dict.fromkeys(yemek_idleri))

    if not yemek_idleri:
        raise RepositoryValidationError(
            "En az bir yemek seçmelisiniz."
        )

    connection = get_write_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM yemekhaneler
            WHERE id = %s
            """,
            (yemekhane_id,)
        )

        if not cursor.fetchone():
            raise RepositoryValidationError(
                "Seçilen yemekhane bulunamadı."
            )

        cursor.execute(
            """
            SELECT id
            FROM ogunler
            WHERE id = %s
            """,
            (ogun_id,)
        )

        if not cursor.fetchone():
            raise RepositoryValidationError(
                "Seçilen öğün bulunamadı."
            )

        placeholders = ",".join(["%s"] * len(yemek_idleri))

        cursor.execute(
            f"""
            SELECT id
            FROM yemekler
            WHERE id IN ({placeholders})
            """,
            tuple(yemek_idleri)
        )

        bulunan_yemekler = cursor.fetchall()

        if len(bulunan_yemekler) != len(yemek_idleri):
            raise RepositoryValidationError(
                "Seçilen yemeklerden biri veya birkaçı bulunamadı."
            )

        cursor.execute(
            """
            INSERT INTO menuler (
                yemekhane_id,
                tarih,
                ogun_id,
                ogrenci_fiyati,
                personel_fiyati
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                yemekhane_id,
                tarih,
                ogun_id,
                ogrenci_fiyati,
                personel_fiyati
            )
        )

        menu_id = cursor.lastrowid

        cursor.executemany(
            """
            INSERT INTO menu_yemekleri (menu_id, yemek_id)
            VALUES (%s, %s)
            """,
            [
                (menu_id, yemek_id)
                for yemek_id in yemek_idleri
            ]
        )

        connection.commit()
        return menu_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ========================================
# YÖNETİCİ PANELİ - MENÜ DÜZENLEME
# ========================================

def update_menu(
    menu_id,
    yemekhane_id,
    tarih,
    ogun_id,
    ogrenci_fiyati,
    personel_fiyati,
    yemek_idleri
):
    yemek_idleri = list(dict.fromkeys(yemek_idleri))

    if not yemek_idleri:
        raise RepositoryValidationError(
            "En az bir yemek seçmelisiniz."
        )

    connection = get_write_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM menuler
            WHERE id = %s
            FOR UPDATE
            """,
            (menu_id,)
        )

        if not cursor.fetchone():
            raise RepositoryValidationError(
                "Düzenlenecek menü bulunamadı.",
                404
            )

        cursor.execute(
            """
            SELECT id
            FROM yemekhaneler
            WHERE id = %s
            """,
            (yemekhane_id,)
        )

        if not cursor.fetchone():
            raise RepositoryValidationError(
                "Seçilen yemekhane bulunamadı."
            )

        cursor.execute(
            """
            SELECT id
            FROM ogunler
            WHERE id = %s
            """,
            (ogun_id,)
        )

        if not cursor.fetchone():
            raise RepositoryValidationError(
                "Seçilen öğün bulunamadı."
            )

        placeholders = ",".join(["%s"] * len(yemek_idleri))

        cursor.execute(
            f"""
            SELECT id
            FROM yemekler
            WHERE id IN ({placeholders})
            """,
            tuple(yemek_idleri)
        )

        bulunan_yemekler = cursor.fetchall()

        if len(bulunan_yemekler) != len(yemek_idleri):
            raise RepositoryValidationError(
                "Seçilen yemeklerden biri veya birkaçı bulunamadı."
            )

        cursor.execute(
            """
            UPDATE menuler
            SET
                yemekhane_id = %s,
                tarih = %s,
                ogun_id = %s,
                ogrenci_fiyati = %s,
                personel_fiyati = %s
            WHERE id = %s
            """,
            (
                yemekhane_id,
                tarih,
                ogun_id,
                ogrenci_fiyati,
                personel_fiyati,
                menu_id
            )
        )

        cursor.execute(
            """
            DELETE FROM menu_yemekleri
            WHERE menu_id = %s
            """,
            (menu_id,)
        )

        cursor.executemany(
            """
            INSERT INTO menu_yemekleri (menu_id, yemek_id)
            VALUES (%s, %s)
            """,
            [
                (menu_id, yemek_id)
                for yemek_id in yemek_idleri
            ]
        )

        connection.commit()
        return menu_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ========================================
# AŞAMA 4: ALERJEN TERCİHLERİ
# ========================================

def get_all_allergens():
    return execute_read("SELECT id, ad FROM alerjenler ORDER BY ad")

def get_user_allergen_ids(user_id):
    rows = execute_read(
        "SELECT alerjen_id FROM kullanici_alerjenleri WHERE kullanici_id = %s ORDER BY alerjen_id",
        (user_id,)
    )
    return [int(row["alerjen_id"]) for row in rows]

def set_user_allergens(user_id, allergen_ids):
    connection = get_write_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM kullanici_alerjenleri WHERE kullanici_id = %s", (user_id,))
        for allergen_id in sorted(set(allergen_ids)):
            cursor.execute(
                "INSERT INTO kullanici_alerjenleri (kullanici_id, alerjen_id) VALUES (%s, %s)",
                (user_id, allergen_id)
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
