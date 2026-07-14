from flask import Flask, render_template, request, redirect, session
import sqlite3
app = Flask(__name__)
app.secret_key = "ozturkiletisim2026"

# -------------------------------
# Veritabanını Oluştur
# -------------------------------
def veritabani_olustur():
    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kayitlar(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT,
        telefon TEXT,
        marka TEXT,
        model TEXT,
        ariza TEXT,
        durum TEXT DEFAULT 'Beklemede',
        ucret INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


veritabani_olustur()


# -------------------------------
# Ana Sayfa
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------
# Servis Kaydı
# -------------------------------
@app.route("/kayit", methods=["POST"])
def kayit():

    ad = request.form["ad"]
    telefon = request.form["telefon"]
    marka = request.form["marka"]
    model = request.form["model"]
    ariza = request.form["ariza"]
    ucret = 0

    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    cursor.execute("""
INSERT INTO kayitlar(ad, telefon, marka, model, ariza, durum, ucret)
VALUES (?,?,?,?,?,?,?)
""", (
    ad,
    telefon,
    marka,
    model,
    ariza,
    "Beklemede",
    ucret
))
    
    
    conn.commit()
    conn.close()

    return redirect("/")



# -------------------------------
# Admin Paneli
# -------------------------------
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    ara = request.args.get("ara", "")

    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    if ara:
        cursor.execute("""
        SELECT * FROM kayitlar
        WHERE ad LIKE ? OR telefon LIKE ? OR marka LIKE ? OR model LIKE ?
        ORDER BY id DESC
        """, (
            "%" + ara + "%",
            "%" + ara + "%",
            "%" + ara + "%",
            "%" + ara + "%"
        ))
    else:
        cursor.execute("SELECT * FROM kayitlar ORDER BY id DESC")

    kayitlar = cursor.fetchall()

    conn.close()

    return render_template("admin.html", kayitlar=kayitlar)


# -------------------------------
# Admin Giriş
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        kullanici = request.form["kullanici"]
        sifre = request.form["sifre"]

        if kullanici == "ozturk" and sifre == "08522580":
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")


# -------------------------------
# Çıkış Yap
# -------------------------------
@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")


# -------------------------------
# Kayıt Sil
# -------------------------------
@app.route("/sil/<int:id>")
def sil(id):

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM kayitlar WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/durum/<int:id>", methods=["POST"])
def durum(id):

    if "admin" not in session:
        return redirect("/login")

    yeni_durum = request.form["durum"]

    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE kayitlar SET durum=? WHERE id=?",
        (yeni_durum, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
@app.route("/whatsapp/<int:id>")
def whatsapp(id):

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ad, telefon, durum, ucret
        FROM kayitlar
        WHERE id=?
    """, (id,))

    kayit = cursor.fetchone()
    conn.close()

    ad = kayit[0]
    telefon = kayit[1]
    durum = kayit[2]
    ucret = kayit[3]

    if telefon.startswith("0"):
        telefon = "90" + telefon[1:]

    if durum == "Beklemede":
        mesaj = f"Merhaba {ad}, cihazınız servisimize alınmıştır. İnceleme işlemi başlamıştır. Öztürk İletişim Teknik"

    elif durum == "Tamirde":
        mesaj = f"Merhaba {ad}, cihazınızın tamiri devam etmektedir. İşlem tamamlandığında size bilgi verilecektir. Öztürk İletişim Teknik"

    elif durum == "Hazır":
        mesaj = f"Merhaba {ad}, cihazınızın tamiri tamamlanmıştır. Tamir Ücreti: {ucret} TL. Cihazınızı teslim alabilirsiniz. Öztürk İletişim Teknik"

    else:
        mesaj = f"Merhaba {ad}, cihazınız teslim edilmiştir. Bizi tercih ettiğiniz için teşekkür ederiz. Öztürk İletişim Teknik"

    return redirect(f"https://wa.me/{telefon}?text={mesaj}")



# -------------------------------
# Kayıt Düzenle
# -------------------------------
@app.route("/duzenle/<int:id>", methods=["GET", "POST"])
def duzenle(id):

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("servis.db")
    cursor = conn.cursor()

    if request.method == "POST":

        ad = request.form["ad"]
        telefon = request.form["telefon"]
        marka = request.form["marka"]
        model = request.form["model"]
        ariza = request.form["ariza"]
        ucret = request.form["ucret"]

        cursor.execute("""
        UPDATE kayitlar
        SET
            ad=?,
            telefon=?,
            marka=?,
            model=?,
            ariza=?,
            ucret=?
        WHERE id=?
        """, (
            ad,
            telefon,
            marka,
            model,
            ariza,
            ucret,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    cursor.execute("SELECT * FROM kayitlar WHERE id=?", (id,))
    kayit = cursor.fetchone()

    conn.close()

    return render_template("edit.html", kayit=kayit)


# -------------------------------
# Programı Çalıştır
# -------------------------------
@app.route("/takip", methods=["GET", "POST"])
def takip():

    sonuc = None

    if request.method == "POST":

        telefon = request.form["telefon"]

        conn = sqlite3.connect("servis.db")
        cursor = conn.cursor()

        cursor.execute(
    "SELECT ad, marka, model, ariza, durum, ucret FROM kayitlar WHERE telefon=?",
    (telefon,)
)
        

        sonuc = cursor.fetchone()

        conn.close()

    return render_template("takip.html", sonuc=sonuc)
if __name__ == "__main__":
    app.run(debug=True)