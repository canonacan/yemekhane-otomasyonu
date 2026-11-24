// ========================================
// HTML ELEMENTLERİ
// ========================================

const menuListesi = document.getElementById("menu-listesi");
const yukleniyor = document.getElementById("yukleniyor");
const hataMesaji = document.getElementById("hata-mesaji");
const yenileButonu = document.getElementById("yenile-btn");

const yemekhaneSec = document.getElementById("yemekhane-sec");
const ogunSec = document.getElementById("ogun-sec");

const haftalikMenuListesi = document.getElementById("haftalik-menu-listesi");
const haftalikYukleniyor = document.getElementById("haftalik-yukleniyor");
const haftalikHataMesaji = document.getElementById("haftalik-hata-mesaji");
const haftalikYenileButonu = document.getElementById("haftalik-yenile-btn");

const sekmeDugmeleri = document.querySelectorAll(".sekme-dugme");
const sekmeIcerikleri = document.querySelectorAll(".sekme-icerik");
const logo = document.querySelector(".logo");

const girisFormu = document.getElementById("giris-formu");
const girisMesaji = document.getElementById("giris-mesaji");
const girisEmail = document.getElementById("giris-email");
const girisSifre = document.getElementById("giris-sifre");

const kullaniciAlani = document.getElementById("kullanici-alani");
const aktifKullanici = document.getElementById("aktif-kullanici");
const girisCikisButonu = document.getElementById("giris-cikis-btn");

const rezervasyonSekmeButonu = document.getElementById("rezervasyon-sekme-btn");
const rezervasyonListesi = document.getElementById("rezervasyon-listesi");
const rezervasyonYukleniyor = document.getElementById("rezervasyon-yukleniyor");
const rezervasyonHataMesaji = document.getElementById("rezervasyon-hata-mesaji");
const rezervasyonYenileButonu = document.getElementById("rezervasyon-yenile-btn");

const bakiyeSekmeButonu = document.getElementById("bakiye-sekme-btn");
const guncelBakiye = document.getElementById("guncel-bakiye");
const bakiyeYenileButonu = document.getElementById("bakiye-yenile-btn");
const bakiyeYuklemeFormu = document.getElementById("bakiye-yukleme-formu");
const yuklemeTutari = document.getElementById("yukleme-tutari");
const bakiyeYuklemeMesaji = document.getElementById("bakiye-yukleme-mesaji");
const bakiyeYukleniyor = document.getElementById("bakiye-yukleniyor");
const bakiyeHareketListesi = document.getElementById("bakiye-hareket-listesi");
const bakiyeHataMesaji = document.getElementById("bakiye-hata-mesaji");

// ========================================
// YÖNETİCİ PANELİ HTML ELEMANLARI
// ========================================

const yoneticiSekmeButonu = document.getElementById("yonetici-sekme-btn");
const yoneticiMenuFormu = document.getElementById("yonetici-menu-formu");
const yoneticiMenuId = document.getElementById("yonetici-menu-id");
const yoneticiFormBaslik = document.getElementById("yonetici-form-baslik");

const yoneticiYemekhane = document.getElementById("yonetici-yemekhane");
const yoneticiTarih = document.getElementById("yonetici-tarih");
const yoneticiOgun = document.getElementById("yonetici-ogun");
const yoneticiOgrenciFiyati = document.getElementById("yonetici-ogrenci-fiyati");
const yoneticiPersonelFiyati = document.getElementById("yonetici-personel-fiyati");
const yoneticiYemekler = document.getElementById("yonetici-yemekler");

const yoneticiMenuKaydetBtn = document.getElementById("yonetici-menu-kaydet-btn");
const yoneticiFormTemizleBtn = document.getElementById("yonetici-form-temizle-btn");
const yoneticiFormMesaji = document.getElementById("yonetici-form-mesaji");

const yoneticiMenuListesi = document.getElementById("yonetici-menu-listesi");
const yoneticiMenuleriYenileBtn = document.getElementById("yonetici-menuleri-yenile-btn");
const yoneticiYukleniyor = document.getElementById("yonetici-yukleniyor");
const yoneticiHataMesaji = document.getElementById("yonetici-hata-mesaji");

let yoneticiSecenekleriYuklendi = false;
let yoneticiMenuVerileri = [];
let menuGruplari = [];
let haftalikMenuVerileri = [];
let haftalikMenulerYuklendi = false;
let aktifKullaniciBilgisi = null;


// ========================================
// SEKME GEÇİŞLERİ
// ========================================

function sekmeAc(sekmeId) {
    sekmeIcerikleri.forEach((icerik) => {
        icerik.hidden = true;
        icerik.classList.remove("aktif");
    });

    sekmeDugmeleri.forEach((dugme) => {
        if (dugme.dataset.sekme) {
            dugme.classList.remove("aktif");
            dugme.setAttribute("aria-selected", "false");
        }
    });

    const secilenIcerik = document.getElementById(sekmeId);

    if (!secilenIcerik) return;

    secilenIcerik.hidden = false;
    secilenIcerik.classList.add("aktif");

    const secilenDugme = document.querySelector(
        `.sekme-dugme[data-sekme="${sekmeId}"]`
    );

    if (secilenDugme) {
        secilenDugme.classList.add("aktif");
        secilenDugme.setAttribute("aria-selected", "true");
    }

    if (sekmeId === "haftalik-menuler" && !haftalikMenulerYuklendi) {
        haftalikMenuleriGetir();
    }

    if (sekmeId === "rezervasyonlarim" && aktifKullaniciBilgisi) {
        rezervasyonlarimiGetir();
    }

    if (sekmeId === "bakiye" && aktifKullaniciBilgisi) {
        bakiyeBilgileriniGetir();
    }
    if (sekmeId === "yonetici-paneli") {
    yoneticiPaneliniAc();
}
}

sekmeDugmeleri.forEach((dugme) => {
    if (dugme.dataset.sekme) {
        dugme.addEventListener("click", () => {
            sekmeAc(dugme.dataset.sekme);
        });
    }
});

logo.addEventListener("click", (event) => {
    event.preventDefault();
    sekmeAc("menuler");
});


// ========================================
// ORTAK YARDIMCI FONKSİYONLAR
// ========================================

function elemanOlustur(etiket, metin, sinif) {
    const eleman = document.createElement(etiket);
    eleman.textContent = metin ?? "";

    if (sinif) {
        eleman.className = sinif;
    }

    return eleman;
}

function paraBicimlendir(tutar) {
    return Number(tutar || 0).toLocaleString("tr-TR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function menuGrupla(veriler) {
    const gruplar = new Map();

    veriler.forEach((yemek) => {
        const menuId = yemek.menu_id;

        if (!gruplar.has(menuId)) {
            gruplar.set(menuId, {
                menuId: menuId,
                tarih: yemek.tarih,
                yemekhane: yemek.yemekhane,
                ogun: yemek.ogun,
                ogrenciFiyati: yemek.ogrenci_fiyati,
                personelFiyati: yemek.personel_fiyati,
                kapasite: yemek.kapasite,
                rezerve: yemek.rezerve,
                bosYer: yemek.bos_yer,
                dolulukYuzde: yemek.doluluk_yuzde,
                rezervasyonSon: yemek.rezervasyon_son,
                yemekler: []
            });
        }

        gruplar.get(menuId).yemekler.push(yemek);
    });

    return Array.from(gruplar.values());
}

function yemekleriEkle(kart, yemekler) {
    const yemekBaslik = elemanOlustur("h3", "Yemekler");
    const yemekListesi = document.createElement("ul");
    let toplamKalori = 0;

    yemekler.forEach((yemek) => {
        const satir = document.createElement("li");

        const ad = elemanOlustur("strong", yemek.yemek);

        const bilgi = elemanOlustur(
            "p",
            `${yemek.kategori || "Kategori belirtilmemiş"} | ${yemek.kalori ?? 0} kcal`
        );

        const ozellik = elemanOlustur(
            "p",
            `Vejetaryen: ${Number(yemek.vejetaryen) === 1 ? "Evet" : "Hayır"} | ` +
            `Alerjenler: ${yemek.alerjenler || "Belirtilmemiş"}`
        );

        satir.append(ad, bilgi, ozellik);
        yemekListesi.appendChild(satir);

        toplamKalori += Number(yemek.kalori) || 0;
    });

    const kalori = elemanOlustur(
        "p",
        `Toplam kalori: ${toplamKalori} kcal`,
        "toplam-kalori"
    );

    kart.append(yemekBaslik, yemekListesi, kalori);
}


// ========================================
// GÜNÜN MENÜSÜ
// ========================================

async function menuleriGetir() {
    yukleniyor.hidden = false;
    yukleniyor.textContent = "Menüler yükleniyor...";
    hataMesaji.hidden = true;
    menuListesi.replaceChildren();

    try {
        const response = await fetch("/api/menuler");

        if (!response.ok) {
            throw new Error("Menüler alınamadı.");
        }

        const veriler = await response.json();

        if (!Array.isArray(veriler)) {
            throw new Error("API geçerli bir menü listesi döndürmedi.");
        }

        menuGruplari = menuGrupla(veriler);

        secenekleriDoldur();
        menuleriFiltrele();

        yukleniyor.hidden = true;

    } catch (error) {
        yukleniyor.hidden = true;
        hataMesaji.textContent =
            "Menüler yüklenirken hata oluştu: " + error.message;
        hataMesaji.hidden = false;
    }
}

function secenekleriDoldur() {
    const seciliYemekhane = yemekhaneSec.value;
    const seciliOgun = ogunSec.value;

    const yemekhaneler = [
        ...new Set(menuGruplari.map((menu) => menu.yemekhane))
    ];

    const ogunler = [
        ...new Set(menuGruplari.map((menu) => menu.ogun))
    ];

    yemekhaneSec.replaceChildren(
        new Option("Tüm Yemekhaneler", "")
    );

    ogunSec.replaceChildren(
        new Option("Tüm Öğünler", "")
    );

    yemekhaneler.forEach((yemekhane) => {
        yemekhaneSec.add(new Option(yemekhane, yemekhane));
    });

    ogunler.forEach((ogun) => {
        ogunSec.add(new Option(ogun, ogun));
    });

    if (yemekhaneler.includes(seciliYemekhane)) {
        yemekhaneSec.value = seciliYemekhane;
    }

    if (ogunler.includes(seciliOgun)) {
        ogunSec.value = seciliOgun;
    }
}

function menuleriFiltrele() {
    const secilenYemekhane = yemekhaneSec.value;
    const secilenOgun = ogunSec.value;

    const filtrelenmisMenuler = menuGruplari.filter((menu) => {
        const yemekhaneUygun =
            !secilenYemekhane ||
            menu.yemekhane === secilenYemekhane;

        const ogunUygun =
            !secilenOgun ||
            menu.ogun === secilenOgun;

        return yemekhaneUygun && ogunUygun;
    });

    gunlukMenuleriGoster(filtrelenmisMenuler);
}

function gunlukMenuleriGoster(menuler) {
    menuListesi.replaceChildren();

    if (menuler.length === 0) {
        menuListesi.appendChild(
            elemanOlustur(
                "p",
                "Seçilen kriterlere uygun menü bulunamadı."
            )
        );
        return;
    }

    menuler.forEach((menu) => {
        const kart = document.createElement("article");
        kart.className = "menu-karti";

        kart.appendChild(
            elemanOlustur(
                "h2",
                `${menu.yemekhane} - ${menu.ogun}`
            )
        );

        kart.appendChild(
            elemanOlustur("p", `Tarih: ${menu.tarih}`)
        );

        const fiyat = kullaniciFiyatiniGetir(menu);

const fiyatMetni =
    fiyat !== null && fiyat !== undefined
        ? `Menü fiyatı: ${fiyat} TL`
        : "Fiyatı görmek için giriş yapın.";

kart.appendChild(
    elemanOlustur("p", fiyatMetni)
);

        yemekleriEkle(kart, menu.yemekler);
        menuListesi.appendChild(kart);
    });
}


// ========================================
// HAFTALIK MENÜ
// ========================================

async function haftalikMenuleriGetir() {
    haftalikYukleniyor.hidden = false;
    haftalikYukleniyor.textContent = "Haftalık menüler yükleniyor...";
    haftalikHataMesaji.hidden = true;
    haftalikMenuListesi.replaceChildren();

    try {
        const response = await fetch("/api/haftalik-menuler");

        if (!response.ok) {
            throw new Error("Haftalık menüler alınamadı.");
        }

        const veriler = await response.json();

        if (!Array.isArray(veriler)) {
            throw new Error("API geçerli bir haftalık menü listesi döndürmedi.");
        }

        haftalikMenuVerileri = veriler;

        const menuler = menuGrupla(veriler);
        haftalikMenuleriGoster(menuler);

        haftalikMenulerYuklendi = true;
        haftalikYukleniyor.hidden = true;

    } catch (error) {
        haftalikYukleniyor.hidden = true;
        haftalikHataMesaji.textContent =
            "Haftalık menüler yüklenirken hata oluştu: " + error.message;
        haftalikHataMesaji.hidden = false;
    }
}


// ========================================
// REZERVASYON ZAMANI KONTROLÜ
// ========================================

function rezervasyonSuresiAcikMi(rezervasyonSon) {
    if (!rezervasyonSon) return false;

    const tarihMetni = String(rezervasyonSon).replace(" ", "T");
    const sonTarih = new Date(tarihMetni);

    if (Number.isNaN(sonTarih.getTime())) {
        return false;
    }

    return new Date() < sonTarih;
}


// ========================================
// KULLANICIYA GÖRE FİYAT
// ========================================

function kullaniciFiyatiniGetir(menu) {
    if (!aktifKullaniciBilgisi) return null;

    const rol = aktifKullaniciBilgisi.rol;

    if (rol === "ogrenci") {
        return menu.ogrenciFiyati;
    }

    if (rol === "personel" || rol === "yonetici") {
        return menu.personelFiyati;
    }

    return null;
}


// ========================================
// REZERVASYON İŞLEMİ
// ========================================

async function rezervasyonYap(menu, buton, durumMesaji) {
    if (!aktifKullaniciBilgisi) {
        sekmeAc("giris");
        girisMesaji.textContent =
            "Rezervasyon yapmak için önce giriş yapmalısınız.";
        girisMesaji.hidden = false;
        return;
    }

    if (!rezervasyonSuresiAcikMi(menu.rezervasyonSon)) {
        durumMesaji.textContent = "Rezervasyon süresi sona erdi.";
        buton.disabled = true;
        buton.textContent = "Süre Doldu";
        return;
    }

    if (Number(menu.bosYer) <= 0) {
        durumMesaji.textContent = "Yemekhane kapasitesi doldu.";
        buton.disabled = true;
        buton.textContent = "Kapasite Doldu";
        return;
    }

    buton.disabled = true;
    buton.textContent = "İşlem yapılıyor...";
    durumMesaji.textContent = "";

    try {
        const response = await fetch("/api/rezervasyonlar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                menu_id: menu.menuId
            })
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Rezervasyon yapılamadı.");
        }

        durumMesaji.textContent =
            `${veri.mesaj} Ücret: ${veri.ucret} TL. Kalan bakiye: ${veri.bakiye} TL.`;

        if (aktifKullaniciBilgisi) {
            aktifKullaniciBilgisi.bakiye = veri.bakiye;
            kullaniciArayuzunuGuncelle(aktifKullaniciBilgisi);
        }

        haftalikMenulerYuklendi = false;
        await haftalikMenuleriGetir();

        await rezervasyonlarimiGetir();
        await bakiyeBilgileriniGetir();

    } catch (error) {
        durumMesaji.textContent = error.message;

        buton.disabled = false;
        buton.textContent = "Rezervasyon Yap";

        haftalikMenulerYuklendi = false;
    }
}


// ========================================
// HAFTALIK MENÜLERİ EKRANA YAZDIR
// ========================================

function haftalikMenuleriGoster(menuler) {
    haftalikMenuListesi.replaceChildren();

    if (menuler.length === 0) {
        haftalikMenuListesi.appendChild(
            elemanOlustur("p", "Bu hafta için menü bulunamadı.")
        );
        return;
    }

    menuler.forEach((menu) => {
        const kart = document.createElement("article");
        kart.className = "menu-karti";

        kart.appendChild(
            elemanOlustur(
                "h2",
                `${menu.yemekhane} - ${menu.ogun}`
            )
        );

        kart.appendChild(
            elemanOlustur("p", `Tarih: ${menu.tarih}`)
        );

        const fiyat = kullaniciFiyatiniGetir(menu);

        let fiyatMetni;

        if (fiyat !== null && fiyat !== undefined) {
            fiyatMetni = `Size özel menü fiyatı: ${fiyat} TL`;
        } else {
            fiyatMetni = "Fiyatı görmek ve rezervasyon yapmak için giriş yapın.";
        }

        kart.appendChild(elemanOlustur("p", fiyatMetni));

        const dolulukAlani = document.createElement("div");
        dolulukAlani.className = "doluluk-alani";

        dolulukAlani.appendChild(
            elemanOlustur("h3", "Rezervasyon Durumu")
        );

        dolulukAlani.appendChild(
            elemanOlustur("p", `Kapasite: ${menu.kapasite ?? "-"}`)
        );

        dolulukAlani.appendChild(
            elemanOlustur("p", `Rezerve edilen: ${menu.rezerve ?? "-"}`)
        );

        dolulukAlani.appendChild(
            elemanOlustur("p", `Boş yer: ${menu.bosYer ?? "-"}`)
        );

        dolulukAlani.appendChild(
            elemanOlustur(
                "p",
                `Doluluk oranı: ${menu.dolulukYuzde ?? "-"}%`
            )
        );

        dolulukAlani.appendChild(
            elemanOlustur(
                "p",
                `Rezervasyon son tarihi: ${menu.rezervasyonSon ?? "Belirtilmemiş"}`
            )
        );

        kart.appendChild(dolulukAlani);

        const rezervasyonDurum = document.createElement("p");
        rezervasyonDurum.className = "rezervasyon-mesaji";

        const rezervasyonButonu = elemanOlustur(
            "button",
            "Rezervasyon Yap",
            "rezervasyon-btn"
        );

        rezervasyonButonu.type = "button";

        const sureAcik = rezervasyonSuresiAcikMi(
            menu.rezervasyonSon
        );

        const kapasiteMusait = Number(menu.bosYer) > 0;

        if (!sureAcik) {
            rezervasyonButonu.disabled = true;
            rezervasyonButonu.textContent = "Süre Doldu";
            rezervasyonDurum.textContent =
                "Rezervasyon süresi sona erdi.";
        } else if (!kapasiteMusait) {
            rezervasyonButonu.disabled = true;
            rezervasyonButonu.textContent = "Kapasite Doldu";
            rezervasyonDurum.textContent =
                "Bu menü için boş yer kalmadı.";
        } else if (!aktifKullaniciBilgisi) {
            rezervasyonButonu.textContent = "Giriş Yap";
        }

        rezervasyonButonu.addEventListener("click", () => {
            if (!aktifKullaniciBilgisi) {
                sekmeAc("giris");
                girisMesaji.textContent =
                    "Rezervasyon için giriş yapmalısınız.";
                girisMesaji.hidden = false;
                return;
            }

            rezervasyonYap(
                menu,
                rezervasyonButonu,
                rezervasyonDurum
            );
        });

        kart.append(
            rezervasyonButonu,
            rezervasyonDurum
        );

        yemekleriEkle(kart, menu.yemekler);
        haftalikMenuListesi.appendChild(kart);
    });
}


// ========================================
// REZERVASYONLARIM
// ========================================

function tarihSaatBicimlendir(deger) {
    if (!deger) return "-";

    const tarihMetni = String(deger).replace(" ", "T");
    const tarih = new Date(tarihMetni);

    if (Number.isNaN(tarih.getTime())) {
        return String(deger);
    }

    return tarih.toLocaleString("tr-TR");
}

function rezervasyonDurumunuYaz(durum) {
    const durumlar = {
        aktif: "Aktif",
        kullanildi: "Kullanıldı",
        iptal: "İptal"
    };

    return durumlar[durum] || durum || "Bilinmiyor";
}

async function rezervasyonlarimiGetir() {
    if (!aktifKullaniciBilgisi) {
        rezervasyonListesi.replaceChildren();
        return;
    }

    rezervasyonYukleniyor.hidden = false;
    rezervasyonHataMesaji.hidden = true;
    rezervasyonListesi.replaceChildren();

    try {
        const response = await fetch("/api/rezervasyonlarim", {
            method: "GET",
            credentials: "same-origin"
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Rezervasyonlar alınamadı.");
        }

        if (!Array.isArray(veri.rezervasyonlar)) {
            throw new Error("API geçerli bir rezervasyon listesi döndürmedi.");
        }

        rezervasyonlariEkranaYaz(veri.rezervasyonlar);

    } catch (error) {
        rezervasyonHataMesaji.textContent =
            "Rezervasyonlar yüklenirken hata oluştu: " + error.message;
        rezervasyonHataMesaji.hidden = false;

    } finally {
        rezervasyonYukleniyor.hidden = true;
    }
}

function rezervasyonlariEkranaYaz(rezervasyonlar) {
    rezervasyonListesi.replaceChildren();

    if (rezervasyonlar.length === 0) {
        rezervasyonListesi.appendChild(
            elemanOlustur("p", "Henüz rezervasyonunuz bulunmuyor.")
        );
        return;
    }

    rezervasyonlar.forEach((rezervasyon) => {
        const kart = document.createElement("article");
        kart.className = "menu-karti rezervasyon-karti";

        kart.appendChild(
            elemanOlustur(
                "h2",
                `${rezervasyon.yemekhane || "Yemekhane"} - ${rezervasyon.ogun || "Öğün"}`
            )
        );

        kart.appendChild(
            elemanOlustur("p", `Tarih: ${tarihSaatBicimlendir(rezervasyon.tarih)}`)
        );

        kart.appendChild(
            elemanOlustur("p", `Rezervasyon numarası: ${rezervasyon.rezervasyon_id}`)
        );

        kart.appendChild(
            elemanOlustur("p", `Ücret: ${rezervasyon.ucret} TL`)
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Oluşturulma: ${tarihSaatBicimlendir(rezervasyon.olusturma)}`
            )
        );

        const durum = elemanOlustur(
            "p",
            `Durum: ${rezervasyonDurumunuYaz(rezervasyon.durum)}`,
            "rezervasyon-mesaji"
        );

        kart.appendChild(durum);

        if (rezervasyon.durum === "aktif") {
            const iptalEdilebilir =
                rezervasyon.iptal_edilebilir === true ||
                Number(rezervasyon.iptal_edilebilir) === 1;

            if (iptalEdilebilir) {
                const iptalButonu = elemanOlustur(
                    "button",
                    "İptal Et",
                    "rezervasyon-btn"
                );

                iptalButonu.type = "button";

                iptalButonu.addEventListener("click", () => {
                    rezervasyonIptalEt(
                        rezervasyon,
                        iptalButonu,
                        durum
                    );
                });

                kart.appendChild(iptalButonu);

            } else {
                kart.appendChild(
                    elemanOlustur(
                        "p",
                        "İptal süresi dolduğu için bu rezervasyon iptal edilemez."
                    )
                );
            }
        }
                else if (rezervasyon.durum === "kullanildi") {
            if (rezervasyon.degerlendirme_id) {
                kart.appendChild(
                    elemanOlustur(
                        "h3",
                        "Değerlendirmeniz"
                    )
                );

                kart.appendChild(
                    elemanOlustur(
                        "p",
                        `Puanınız: ${rezervasyon.degerlendirme_puani}/5`
                    )
                );

                kart.appendChild(
                    elemanOlustur(
                        "p",
                        `Yorumunuz: ${rezervasyon.degerlendirme_yorumu || "Yorum yazılmamış."}`
                    )
                );

            } else {
                const degerlendirmeBaslik = elemanOlustur(
                    "h3",
                    "Menüyü Değerlendir"
                );

                const form = document.createElement("form");
                form.className = "degerlendirme-formu";

                const puanLabel = elemanOlustur(
                    "label",
                    "Puanınız (1–5)"
                );

                const puanSec = document.createElement("select");
                puanSec.required = true;
                puanSec.className = "degerlendirme-puan";

                const bosSecenek = document.createElement("option");
                bosSecenek.value = "";
                bosSecenek.textContent = "Puan seçin";
                bosSecenek.disabled = true;
                bosSecenek.selected = true;
                puanSec.appendChild(bosSecenek);

                for (let puan = 1; puan <= 5; puan++) {
                    const secenek = document.createElement("option");
                    secenek.value = String(puan);
                    secenek.textContent = `${puan} / 5`;
                    puanSec.appendChild(secenek);
                }

                puanLabel.appendChild(puanSec);

                const yorumLabel = elemanOlustur(
                    "label",
                    "Yorumunuz (isteğe bağlı)"
                );

                const yorumAlani = document.createElement("textarea");
                yorumAlani.className = "degerlendirme-yorum";
                yorumAlani.maxLength = 500;
                yorumAlani.rows = 3;
                yorumAlani.placeholder = "Menü hakkındaki düşüncelerinizi yazın...";

                yorumLabel.appendChild(yorumAlani);

                const gonderButonu = elemanOlustur(
                    "button",
                    "Değerlendirmeyi Gönder",
                    "rezervasyon-btn"
                );
                gonderButonu.type = "submit";

                const mesaj = elemanOlustur(
                    "p",
                    "",
                    "rezervasyon-mesaji"
                );

                form.append(
                    puanLabel,
                    yorumLabel,
                    gonderButonu,
                    mesaj
                );

                form.addEventListener("submit", (event) => {
                    degerlendirmeGonder(
                        event,
                        rezervasyon.menu_id,
                        puanSec,
                        yorumAlani,
                        gonderButonu,
                        mesaj
                    );
                });

                kart.append(
                    degerlendirmeBaslik,
                    form
                );
            }
        }

        rezervasyonListesi.appendChild(kart);
    });
}
async function degerlendirmeGonder(
    event,
    menuId,
    puanSec,
    yorumAlani,
    gonderButonu,
    mesaj
) {
    event.preventDefault();

    const puan = Number(puanSec.value);
    const yorum = yorumAlani.value.trim();

    if (!Number.isInteger(puan) || puan < 1 || puan > 5) {
        mesaj.textContent = "Lütfen 1 ile 5 arasında bir puan seçin.";
        return;
    }

    gonderButonu.disabled = true;
    gonderButonu.textContent = "Gönderiliyor...";
    mesaj.textContent = "";

    try {
        const response = await fetch("/api/degerlendirmeler", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                menu_id: menuId,
                puan: puan,
                yorum: yorum || null
            })
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(
                veri.detail || "Değerlendirme kaydedilemedi."
            );
        }

        mesaj.textContent =
            veri.mesaj || "Değerlendirmeniz kaydedildi.";

        await rezervasyonlarimiGetir();

    } catch (error) {
        mesaj.textContent = error.message;

    } finally {
        gonderButonu.disabled = false;
        gonderButonu.textContent = "Değerlendirmeyi Gönder";
    }
}

async function rezervasyonIptalEt(rezervasyon, buton, durumAlani) {
    const onay = confirm(
        `${rezervasyon.yemekhane} - ${rezervasyon.ogun} rezervasyonunu iptal etmek istiyor musunuz?`
    );

    if (!onay) return;

    buton.disabled = true;
    buton.textContent = "İptal ediliyor...";

    try {
        const response = await fetch(
            `/api/rezervasyonlarim/${rezervasyon.rezervasyon_id}/iptal`,
            {
                method: "POST",
                credentials: "same-origin"
            }
        );

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Rezervasyon iptal edilemedi.");
        }

        if (aktifKullaniciBilgisi) {
            aktifKullaniciBilgisi.bakiye = veri.bakiye;
            kullaniciArayuzunuGuncelle(aktifKullaniciBilgisi);
        }

        durumAlani.textContent =
            `İptal edildi. ${veri.iade} TL hesabınıza iade edildi.`;

        await rezervasyonlarimiGetir();
        await bakiyeBilgileriniGetir();

        haftalikMenulerYuklendi = false;

        if (document.getElementById("haftalik-menuler").classList.contains("aktif")) {
            await haftalikMenuleriGetir();
        }

    } catch (error) {
        durumAlani.textContent = error.message;
        buton.disabled = false;
        buton.textContent = "İptal Et";
    }
}


// ========================================
// BAKİYE VE HESAP HAREKETLERİ
// ========================================

async function bakiyeBilgileriniGetir() {
    if (!aktifKullaniciBilgisi) {
        bakiyeHareketListesi.replaceChildren();
        guncelBakiye.textContent = "0,00 TL";
        return;
    }

    bakiyeYukleniyor.hidden = false;
    bakiyeHataMesaji.hidden = true;
    bakiyeHareketListesi.replaceChildren();

    try {
        const response = await fetch("/api/bakiye", {
            method: "GET",
            credentials: "same-origin"
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Bakiye bilgileri alınamadı.");
        }

        aktifKullaniciBilgisi.bakiye = veri.bakiye;

        guncelBakiye.textContent =
            `${paraBicimlendir(veri.bakiye)} TL`;

        kullaniciArayuzunuGuncelle(aktifKullaniciBilgisi);

        bakiyeHareketleriniGoster(veri.hareketler || []);

    } catch (error) {
        bakiyeHataMesaji.textContent =
            "Bakiye bilgileri yüklenirken hata oluştu: " + error.message;
        bakiyeHataMesaji.hidden = false;

    } finally {
        bakiyeYukleniyor.hidden = true;
    }
}

function bakiyeHareketleriniGoster(hareketler) {
    bakiyeHareketListesi.replaceChildren();

    if (!Array.isArray(hareketler) || hareketler.length === 0) {
        bakiyeHareketListesi.appendChild(
            elemanOlustur("p", "Henüz bakiye hareketiniz bulunmuyor.")
        );
        return;
    }

    const turler = {
        yukleme: "Bakiye Yükleme",
        rezervasyon: "Rezervasyon Ücreti",
        iade: "Rezervasyon İadesi"
    };

    hareketler.forEach((hareket) => {
        const kart = document.createElement("article");
        kart.className = "menu-karti bakiye-hareket-karti";

        const tur = turler[hareket.tur] || hareket.tur;

        kart.appendChild(
            elemanOlustur("h2", tur)
        );

        const tutar = Number(hareket.tutar || 0);
        const tutarMetni =
            `${tutar > 0 ? "+" : ""}${paraBicimlendir(tutar)} TL`;

        kart.appendChild(
            elemanOlustur("p", `Tutar: ${tutarMetni}`)
        );

        if (hareket.aciklama) {
            kart.appendChild(
                elemanOlustur("p", `Açıklama: ${hareket.aciklama}`)
            );
        }

        if (hareket.rezervasyon_id) {
            kart.appendChild(
                elemanOlustur(
                    "p",
                    `Rezervasyon numarası: ${hareket.rezervasyon_id}`
                )
            );
        }

        kart.appendChild(
            elemanOlustur(
                "p",
                `İşlem tarihi: ${tarihSaatBicimlendir(hareket.olusturma)}`
            )
        );

        bakiyeHareketListesi.appendChild(kart);
    });
}

async function bakiyeYukle(event) {
    event.preventDefault();

    if (!aktifKullaniciBilgisi) {
        sekmeAc("giris");
        return;
    }

    const tutar = Number(yuklemeTutari.value);

    if (!Number.isFinite(tutar) || tutar < 10 || tutar > 1000) {
        bakiyeYuklemeMesaji.textContent =
            "Yükleme tutarı 10 TL ile 1000 TL arasında olmalıdır.";
        bakiyeYuklemeMesaji.hidden = false;
        return;
    }

    if (Math.round(tutar * 100) !== tutar * 100) {
        bakiyeYuklemeMesaji.textContent =
            "En fazla iki ondalık basamak girebilirsiniz.";
        bakiyeYuklemeMesaji.hidden = false;
        return;
    }

    const gonderButonu = bakiyeYuklemeFormu.querySelector(
        'button[type="submit"]'
    );

    gonderButonu.disabled = true;
    gonderButonu.textContent = "Yükleniyor...";

    bakiyeYuklemeMesaji.hidden = false;
    bakiyeYuklemeMesaji.textContent = "Bakiye yükleme işlemi yapılıyor...";

    try {
        const response = await fetch("/api/bakiye/yukle", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                tutar: tutar
            })
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Bakiye yüklenemedi.");
        }

        bakiyeYuklemeMesaji.textContent =
            `${veri.mesaj || "Bakiye yükleme başarılı."} Yeni bakiyeniz: ${paraBicimlendir(veri.bakiye)} TL`;

        bakiyeYuklemeMesaji.hidden = false;
        bakiyeYuklemeFormu.reset();

        if (aktifKullaniciBilgisi) {
            aktifKullaniciBilgisi.bakiye = veri.bakiye;
            kullaniciArayuzunuGuncelle(aktifKullaniciBilgisi);
        }

        await bakiyeBilgileriniGetir();

    } catch (error) {
        bakiyeYuklemeMesaji.textContent = error.message;
        bakiyeYuklemeMesaji.hidden = false;

    } finally {
        gonderButonu.disabled = false;
        gonderButonu.textContent = "Bakiye Yükle";
    }
}


// ========================================
// KULLANICI OTURUMU
// ========================================

function kullaniciArayuzunuGuncelle(kullanici) {
    aktifKullaniciBilgisi = kullanici;

    if (kullanici) {
        yoneticiSekmeButonu.hidden = kullanici.rol !== "yonetici";
        rezervasyonSekmeButonu.hidden = false;
        bakiyeSekmeButonu.hidden = false;

        const bakiye = Number(kullanici.bakiye || 0)
            .toLocaleString("tr-TR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });

        aktifKullanici.textContent =
            `${kullanici.ad} ${kullanici.soyad} | ${kullanici.rol} | Bakiye: ${bakiye} TL`;

        kullaniciAlani.hidden = false;

        girisCikisButonu.textContent = "Çıkış Yap";
        girisCikisButonu.dataset.durum = "giris-yapildi";

    } else {
        yoneticiSekmeButonu.hidden = true;
        rezervasyonSekmeButonu.hidden = true;
        bakiyeSekmeButonu.hidden = true;

        rezervasyonListesi.replaceChildren();
        bakiyeHareketListesi.replaceChildren();

        guncelBakiye.textContent = "0,00 TL";

        aktifKullanici.textContent = "";
        kullaniciAlani.hidden = true;

        girisCikisButonu.textContent = "Giriş Yap";
        girisCikisButonu.dataset.durum = "giris-yapilmadi";
    }

    // Günün menüsündeki fiyatları güncel kullanıcı rolüne göre yenile.
menuleriFiltrele();

// Haftalık menüdeki fiyatları güncel kullanıcı rolüne göre yenile.
if (haftalikMenulerYuklendi) {
    haftalikMenuleriGoster(
        menuGrupla(haftalikMenuVerileri)
    );
}
}

async function oturumuKontrolEt() {
    try {
        const response = await fetch("/api/oturum", {
            method: "GET",
            credentials: "same-origin"
        });

        if (!response.ok) {
            kullaniciArayuzunuGuncelle(null);
            return;
        }

        const veri = await response.json();

        if (veri.giris_yapildi && veri.kullanici) {
            kullaniciArayuzunuGuncelle(veri.kullanici);

            await rezervasyonlarimiGetir();
            await bakiyeBilgileriniGetir();

        } else {
            kullaniciArayuzunuGuncelle(null);
        }

    } catch (error) {
        console.error("Oturum kontrol hatası:", error);
        kullaniciArayuzunuGuncelle(null);
    }
}


// ========================================
// GİRİŞ YAP
// ========================================

async function girisYap(event) {
    event.preventDefault();

    if (aktifKullaniciBilgisi) {
        girisMesaji.textContent =
            "Başka bir hesaba geçmek için önce çıkış yapmalısınız.";
        girisMesaji.hidden = false;
        return;
    }

    girisMesaji.hidden = false;
    girisMesaji.textContent = "Giriş yapılıyor...";

    const istek = {
        eposta: girisEmail.value.trim(),
        sifre: girisSifre.value
    };

    try {
        const response = await fetch("/api/giris", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify(istek)
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Giriş yapılamadı.");
        }

        kullaniciArayuzunuGuncelle(veri.kullanici);

        girisMesaji.textContent = veri.mesaj || "Giriş başarılı.";
        girisFormu.reset();

        sekmeAc("menuler");

        await rezervasyonlarimiGetir();
        await bakiyeBilgileriniGetir();

        if (haftalikMenulerYuklendi) {
            haftalikMenuleriGoster(
                menuGrupla(haftalikMenuVerileri)
            );
        }

    } catch (error) {
        girisMesaji.textContent = error.message;
        girisMesaji.hidden = false;
    }
}


// ========================================
// ÇIKIŞ YAP
// ========================================

async function cikisYap() {
    girisCikisButonu.disabled = true;

    try {
        const response = await fetch("/api/cikis", {
            method: "POST",
            credentials: "same-origin"
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Çıkış yapılamadı.");
        }

        kullaniciArayuzunuGuncelle(null);

        girisMesaji.textContent = veri.mesaj || "Çıkış yapıldı.";
        girisMesaji.hidden = false;

        sekmeAc("menuler");

    } catch (error) {
        alert(error.message);

    } finally {
        girisCikisButonu.disabled = false;
    }
}


// ========================================
// GİRİŞ / ÇIKIŞ TEK BUTON
// ========================================

girisCikisButonu.addEventListener("click", async () => {
    if (aktifKullaniciBilgisi) {
        await cikisYap();
    } else {
        sekmeAc("giris");
    }
});


// ========================================
// YÖNETİCİ PANELİ
// ========================================

async function yoneticiSecenekleriniGetir() {
    if (!aktifKullaniciBilgisi ||
        aktifKullaniciBilgisi.rol !== "yonetici") {
        return;
    }

    try {
        const response = await fetch("/api/yonetici/secenekler", {
            credentials: "same-origin"
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Seçenekler alınamadı.");
        }

        yoneticiYemekhane.replaceChildren();
        yoneticiOgun.replaceChildren();
        yoneticiYemekler.replaceChildren();

        yoneticiYemekhane.add(
            new Option("Yemekhane seçin", "")
        );

        veri.yemekhaneler.forEach((item) => {
            yoneticiYemekhane.add(
                new Option(item.ad, item.id)
            );
        });

        yoneticiOgun.add(
            new Option("Öğün seçin", "")
        );

        veri.ogunler.forEach((item) => {
            yoneticiOgun.add(
                new Option(item.ad, item.id)
            );
        });

        veri.yemekler.forEach((item) => {
            const secenek = new Option(
                `${item.ad} (${item.kategori} - ${item.kalori} kcal)`,
                item.id
            );

            yoneticiYemekler.add(secenek);
        });

        yoneticiSecenekleriYuklendi = true;

    } catch (error) {
        yoneticiHataMesaji.textContent = error.message;
        yoneticiHataMesaji.hidden = false;
    }
}


async function yoneticiMenuleriGetir() {
    if (!aktifKullaniciBilgisi ||
        aktifKullaniciBilgisi.rol !== "yonetici") {
        return;
    }

    yoneticiYukleniyor.hidden = false;
    yoneticiHataMesaji.hidden = true;
    yoneticiMenuListesi.replaceChildren();

    try {
        const response = await fetch("/api/yonetici/menuler", {
            credentials: "same-origin"
        });

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Menüler alınamadı.");
        }

        yoneticiMenuVerileri = veri.menuler || [];
        yoneticiMenuleriGoster(yoneticiMenuVerileri);

    } catch (error) {
        yoneticiHataMesaji.textContent = error.message;
        yoneticiHataMesaji.hidden = false;

    } finally {
        yoneticiYukleniyor.hidden = true;
    }
}


function yoneticiMenuleriGoster(menuler) {
    yoneticiMenuListesi.replaceChildren();

    if (!menuler.length) {
        yoneticiMenuListesi.appendChild(
            elemanOlustur("p", "Henüz menü bulunmuyor.")
        );
        return;
    }

    menuler.forEach((menu) => {
        const kart = document.createElement("article");
        kart.className = "menu-karti";

        kart.appendChild(
            elemanOlustur(
                "h2",
                `${menu.yemekhane} - ${menu.ogun}`
            )
        );

        kart.appendChild(
            elemanOlustur("p", `Tarih: ${menu.tarih}`)
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Öğrenci fiyatı: ${paraBicimlendir(menu.ogrenci_fiyati)} TL`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Personel fiyatı: ${paraBicimlendir(menu.personel_fiyati)} TL`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Kapasite: ${menu.kapasite}`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Rezerve edilen: ${menu.rezerve}`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Boş yer: ${menu.bos_yer}`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Doluluk oranı: %${menu.doluluk_yuzde}`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Rezervasyon son saati: ${tarihSaatBicimlendir(menu.rezervasyon_son)}`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Ortalama puan: ${menu.ortalama_puan} / 5`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Değerlendirme sayısı: ${menu.oy_sayisi}`
            )
        );

        kart.appendChild(
            elemanOlustur(
                "p",
                `Yemekler: ${menu.yemekler || "Belirtilmemiş"}`
            )
        );

        const duzenleButonu = elemanOlustur(
            "button",
            "Menüyü Düzenle",
            "dugme"
        );

        duzenleButonu.type = "button";

        duzenleButonu.addEventListener("click", () => {
            yoneticiMenuDuzenlemeyeHazirla(menu);
        });

        kart.appendChild(duzenleButonu);
        yoneticiMenuListesi.appendChild(kart);
    });
}


function yoneticiMenuDuzenlemeyeHazirla(menu) {
    yoneticiMenuId.value = menu.menu_id;

    yoneticiYemekhane.value = String(menu.yemekhane_id);
    yoneticiTarih.value = menu.tarih;
    yoneticiOgun.value = String(menu.ogun_id);

    yoneticiOgrenciFiyati.value = menu.ogrenci_fiyati;
    yoneticiPersonelFiyati.value = menu.personel_fiyati;

    const yemekIdleri = String(menu.yemek_idleri || "")
        .split(",")
        .filter(Boolean);

    Array.from(yoneticiYemekler.options).forEach((secenek) => {
        secenek.selected = yemekIdleri.includes(secenek.value);
    });

    yoneticiFormBaslik.textContent = "Menüyü Düzenle";
    yoneticiMenuKaydetBtn.textContent = "Menüyü Güncelle";

    yoneticiFormMesaji.textContent =
        "Menü bilgilerini düzenleyebilirsiniz.";
    yoneticiFormMesaji.hidden = false;

    yoneticiMenuFormu.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


function yoneticiFormunuTemizle() {
    yoneticiMenuFormu.reset();
    yoneticiMenuId.value = "";

    Array.from(yoneticiYemekler.options).forEach((secenek) => {
        secenek.selected = false;
    });

    yoneticiFormBaslik.textContent = "Yeni Menü Oluştur";
    yoneticiMenuKaydetBtn.textContent = "Menüyü Oluştur";

    yoneticiFormMesaji.hidden = true;
}


async function yoneticiMenuKaydet(event) {
    event.preventDefault();

    if (!aktifKullaniciBilgisi ||
        aktifKullaniciBilgisi.rol !== "yonetici") {
        return;
    }

    const yemekIdleri = Array.from(
        yoneticiYemekler.selectedOptions
    ).map((secenek) => Number(secenek.value));

    if (yemekIdleri.length === 0) {
        yoneticiFormMesaji.textContent =
            "Lütfen menüye en az bir yemek ekleyin.";
        yoneticiFormMesaji.hidden = false;
        return;
    }

    const menuId = yoneticiMenuId.value;

    const istek = {
        yemekhane_id: Number(yoneticiYemekhane.value),
        tarih: yoneticiTarih.value,
        ogun_id: Number(yoneticiOgun.value),
        ogrenci_fiyati: Number(yoneticiOgrenciFiyati.value),
        personel_fiyati: Number(yoneticiPersonelFiyati.value),
        yemek_idleri: yemekIdleri
    };

    yoneticiMenuKaydetBtn.disabled = true;
    yoneticiMenuKaydetBtn.textContent = "Kaydediliyor...";

    try {
        const response = await fetch(
            menuId
                ? `/api/yonetici/menuler/${menuId}`
                : "/api/yonetici/menuler",
            {
                method: menuId ? "PUT" : "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify(istek)
            }
        );

        const veri = await response.json();

        if (!response.ok) {
            throw new Error(veri.detail || "Menü kaydedilemedi.");
        }

        yoneticiFormMesaji.textContent =
            veri.mesaj || "Menü başarıyla kaydedildi.";
        yoneticiFormMesaji.hidden = false;

        yoneticiFormunuTemizle();

        await yoneticiMenuleriGetir();

        // Günün ve haftalık menülerini de yenile.
        await menuleriGetir();

        haftalikMenulerYuklendi = false;

        if (
            document.getElementById("haftalik-menuler")
                .classList.contains("aktif")
        ) {
            await haftalikMenuleriGetir();
        }

    } catch (error) {
        yoneticiFormMesaji.textContent = error.message;
        yoneticiFormMesaji.hidden = false;

    } finally {
        yoneticiMenuKaydetBtn.disabled = false;

        if (yoneticiMenuId.value) {
            yoneticiMenuKaydetBtn.textContent = "Menüyü Güncelle";
        } else {
            yoneticiMenuKaydetBtn.textContent = "Menüyü Oluştur";
        }
    }
}


async function yoneticiPaneliniAc() {
    if (!aktifKullaniciBilgisi ||
        aktifKullaniciBilgisi.rol !== "yonetici") {
        sekmeAc("menuler");
        return;
    }

    if (!yoneticiSecenekleriYuklendi) {
        await yoneticiSecenekleriniGetir();
    }

    await yoneticiMenuleriGetir();
}

// ========================================
// OLAY DİNLEYİCİLERİ
// ========================================

yemekhaneSec.addEventListener("change", menuleriFiltrele);
ogunSec.addEventListener("change", menuleriFiltrele);

yenileButonu.addEventListener("click", menuleriGetir);

haftalikYenileButonu.addEventListener("click", () => {
    haftalikMenulerYuklendi = false;
    haftalikMenuleriGetir();
});

rezervasyonYenileButonu.addEventListener("click", rezervasyonlarimiGetir);

bakiyeYenileButonu.addEventListener("click", bakiyeBilgileriniGetir);
bakiyeYuklemeFormu.addEventListener("submit", bakiyeYukle);
yoneticiMenuFormu.addEventListener(
    "submit",
    yoneticiMenuKaydet
);

yoneticiFormTemizleBtn.addEventListener(
    "click",
    yoneticiFormunuTemizle
);

yoneticiMenuleriYenileBtn.addEventListener(
    "click",
    yoneticiMenuleriGetir
);

girisFormu.addEventListener("submit", girisYap);


// ========================================
// İLK AÇILIŞ
// ========================================

sekmeAc("menuler");
menuleriGetir();
oturumuKontrolEt();