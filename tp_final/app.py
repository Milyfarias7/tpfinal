from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Carpeta donde se guardarán las imágenes

# Función para conectar a la base de datos de SQLite
def conectar_bd():
    conn = sqlite3.connect('db.sqlite')
    return conn

# Decorador para verificar si el usuario ha iniciado sesión
def login_requerido(func):
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('registro'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Página de inicio / catálogo
@app.route('/')
@login_requerido
def catalogo():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM zapatillas")
    productos = cursor.fetchall()
    conn.close()
    return render_template('catalogo.html', productos=productos)

# Página del carrito de compras
@app.route('/carrito')
@login_requerido
def carrito():
    return render_template('carrito.html')

# Página de pago
@app.route('/pago')
@login_requerido
def pago():
    return render_template('pago.html')

# Página para agregar productos
@app.route('/agregar_producto', methods=['GET', 'POST'])
@login_requerido
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']

        # Manejo de la imagen subida
        imagen = request.files['imagen']
        if imagen:
            imagen_filename = imagen.filename
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename))
            imagen_url = f"uploads/{imagen_filename}"

            # Guardar en la base de datos
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO zapatillas (nombre, precio, imagen) VALUES (?, ?, ?)", (nombre, precio, imagen_url))
            conn.commit()
            conn.close()
            return redirect(url_for('catalogo'))

    return render_template('agregar_producto.html')

# Página de registro de usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        contraseña_hash = generate_password_hash(contraseña)

        # Guardar el nuevo usuario en la base de datos
        conn = conectar_bd()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nombre, correo, contraseña) VALUES (?, ?, ?)", (nombre, correo, contraseña_hash))
            conn.commit()
            usuario_id = cursor.lastrowid
            session['usuario_id'] = usuario_id  # Guarda el ID del usuario en la sesión
            conn.close()
            return redirect(url_for('catalogo'))
        except sqlite3.IntegrityError:
            conn.close()
            return "El correo ya está registrado, por favor utiliza otro."

    return render_template('registro.html')

# Página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Verificar el usuario en la base de datos
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT id, contraseña FROM usuarios WHERE correo = ?", (correo,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario[1], contraseña):
            session['usuario_id'] = usuario[0]  # Guarda el ID del usuario en la sesión
            return redirect(url_for('catalogo'))
        else:
            return "Correo o contraseña incorrectos."

    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
