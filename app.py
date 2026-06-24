
import os
import sqlite3
import requests

from datetime import date
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "my_secret_key_123"
TOKEN = "8725956965:AAGGM_LZA1IGT1WKe7sBCdrvHHz-pUlqf4s"
CHAT_ID = "7780318857"


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        print(request.form)

        name = request.form["name"]
        phone = request.form["phone"]
        service = request.form["service"]
        date = request.form["date"]
        time = request.form["time"]
        comment = request.form["comment"]


        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM clients WHERE date = ? AND time = ?",
            (date, time)
        )

        busy = cursor.fetchone()

        if busy:
            connection.close()

            return f"""
            <h2 style='color:red;text-align:center;margin-top:50px;'>
                ❌ Dieses Datum und diese Uhrzeit sind bereits belegt.
            </h2>

            <div style="text-align:center;margin-top:30px;">
                <a href="/booking">
                    Zurück
                </a>
            </div>
            """

        cursor.execute("""
            INSERT INTO clients
            (name, phone, service, date, time, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, service, date, time, comment))

        connection.commit()
        message = f"""
        🆕 Новая запись!

        👤 Имя: {name}
        📞 Телефон: {phone}
        💅 Услуга: {service}
        📅 Дата: {date}
        🕒 Время: {time}
        💬 Комментарий: {comment}
        """

        send_telegram_message(message)
        connection.close()

        return render_template(
            "success.html",
            name=name,
            phone=phone,
            service=service,
            date=date,
            time=time
        )
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM reviews
        ORDER BY id DESC
    """)

    reviews = cursor.fetchall()

    connection.close()

    photos = os.listdir("static/gallery")

    return render_template(
        "index.html",
        reviews=reviews,
        photos=photos
    )


@app.route("/booking")
def booking():
    return render_template("booking.html")


@app.route("/reviews", methods=["GET", "POST"])
def reviews():

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    if request.method == "POST":

        name = request.form["name"]
        rating = request.form["rating"]
        comment = request.form["comment"]

        cursor.execute("""
            INSERT INTO reviews (name, rating, comment)
            VALUES (?, ?, ?)
        """, (name, rating, comment))

        connection.commit()
        print("Отзыв сохранён!")

        return redirect("/reviews")

    cursor.execute("""
        SELECT * FROM reviews
        ORDER BY id DESC
    """)

    reviews = cursor.fetchall()

    connection.close()

    return render_template(
        "reviews.html",
        reviews=reviews
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "120119":
            session["admin"] = True
            return redirect("/admin")

        return "Неверный логин или пароль"

    return render_template("login.html")


@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Клиенты
    cursor.execute("SELECT * FROM clients ORDER BY id DESC")
    clients = cursor.fetchall()

    # Отзывы
    cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
    reviews = cursor.fetchall()

    connection.close()

    return render_template(
        "admin.html",
        clients=clients,
        reviews=reviews
    )

@app.route("/delete/<int:id>")
def delete(id):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM clients WHERE id = ?",
        (id,)
    )

    connection.commit()
    connection.close()

    return redirect("/admin")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        service = request.form["service"]
        date = request.form["date"]
        time = request.form["time"]
        comment = request.form["comment"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE clients
            SET
                name = ?,
                phone = ?,
                service = ?,
                date = ?,
                time = ?,
                comment = ?
            WHERE id = ?
        """, (name, phone, service, date, time, comment, id))

        connection.commit()
        connection.close()

        return redirect("/admin")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM clients WHERE id = ?",
        (id,)
    )

    client = cursor.fetchone()

    connection.close()

    return render_template("edit.html", client=client)


@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")

@app.route("/delete_review/<int:id>")
def delete_review(id):

    if "admin" not in session:
        return redirect("/login")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM reviews WHERE id = ?",
        (id,)
    )

    connection.commit()
    connection.close()

    return redirect("/admin")
from flask import jsonify


@app.route("/get_busy_times")
def get_busy_times():

    date = request.args.get("date")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT time FROM clients WHERE date = ?",
        (date,)
    )

    rows = cursor.fetchall()

    connection.close()

    busy = [row[0] for row in rows]

    return jsonify(busy)

@app.route("/calendar")
def calendar():

    if "admin" not in session:
        return redirect("/login")

    selected_date = request.args.get("date")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    if selected_date:

        cursor.execute("""
            SELECT *
            FROM clients
            WHERE date = ?
            ORDER BY time ASC
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT *
            FROM clients
            ORDER BY date ASC, time ASC
        """)

    clients = cursor.fetchall()

    connection.close()

    return render_template(
        "calendar.html",
        clients=clients,
        selected_date=selected_date
    )
import os
from werkzeug.utils import secure_filename


@app.route("/gallery_admin")
def gallery_admin():

    if "admin" not in session:
        return redirect("/login")

    photos = os.listdir("static/gallery")

    return render_template(
        "gallery_admin.html",
        photos=photos
    )

@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    if "admin" not in session:
        return redirect("/login")

    photo = request.files["photo"]

    if photo.filename == "":
        return redirect("/gallery_admin")

    filename = secure_filename(photo.filename)

    photo.save(
        os.path.join("static", "gallery", filename)
    )

    return redirect("/gallery_admin")

@app.route("/delete_photo/<filename>")
def delete_photo(filename):

    if "admin" not in session:
        return redirect("/login")

    path = os.path.join("static", "gallery", filename)

    if os.path.exists(path):
        os.remove(path)

    return redirect("/gallery_admin")
if __name__ == "__main__":
    app.run(debug=True)


