
import os
import mysql.connector


def get_write_connection():
    """Yazma işlemleri için kaynak MySQL bağlantısı."""
    return mysql.connector.connect(
        host=os.getenv("DB_YAZMA_HOST", "mysql-primary"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_ADI", "yemekhane"),
        user=os.getenv("DB_KULLANICI", "yemekhane_app"),
        password=os.getenv("DB_SIFRE", "Uyg_2026")
    )


def get_read_connection():
    """Okuma işlemleri için replika MySQL bağlantısı."""
    return mysql.connector.connect(
        host=os.getenv("DB_OKUMA_HOST", "mysql-replica"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_ADI", "yemekhane"),
        user=os.getenv("DB_KULLANICI", "yemekhane_app"),
        password=os.getenv("DB_SIFRE", "Uyg_2026")
    )
