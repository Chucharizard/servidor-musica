from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User, init_db, get_db_connection, add_song_to_playlist, get_playlist_songs

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Clave secreta para sesiones
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # Limita tamaño a 200MB
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

# Inicializar la base de datos
init_db()

# Configurar el gestor de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

# Callback para cargar un usuario desde la sesión
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# Asegúrate de que la carpeta de uploads exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Formularios
class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class PlaylistForm(FlaskForm):
    title = StringField('Nombre de la Playlist', validators=[DataRequired()])
    submit = SubmitField('Crear Playlist')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Inicio de sesión fallido. Verifica tu nombre de usuario y contraseña.')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.create(form.username.data, form.password.data):
            flash('¡Cuenta creada con éxito! Ya puedes iniciar sesión.')
            return redirect(url_for('login'))
        else:
            flash('El nombre de usuario ya está en uso.')
    
    return render_template('register.html', form=form)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Verifica si la solicitud tiene el archivo
        if 'file' not in request.files:
            flash('No se encontró ningún archivo')
            return redirect(request.url)
        
        file = request.files['file']
        playlist_id = request.form.get('playlist_id')
        
        # Si el usuario no selecciona un archivo
        if file.filename == '':
            flash('No se seleccionó ningún archivo')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Si se seleccionó una playlist, añadir la canción a ella
            if playlist_id:
                add_song_to_playlist(playlist_id, filename)
                flash('¡Archivo subido y añadido a la playlist!')
            else:
                flash('¡Archivo subido correctamente!')
            
            return redirect(url_for('playlist'))
    
    # Obtener las playlists del usuario para el formulario
    playlists = current_user.get_playlists()
    return render_template('upload.html', playlists=playlists)

@app.route('/playlist')
def playlist():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(filename):
            files.append(filename)
    
    # Si el usuario está autenticado, mostrar sus playlists
    playlists = None
    if current_user.is_authenticated:
        playlists = current_user.get_playlists()
    
    return render_template('playlist.html', files=files, playlists=playlists)

@app.route('/play/<filename>')
def play_file(filename):
    files = []
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(f):
            files.append(f)
    
    playlists = None
    if current_user.is_authenticated:
        playlists = current_user.get_playlists()
    
    return render_template('playlist.html', 
                          files=files,
                          playlists=playlists,
                          current_file=filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/create_playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    form = PlaylistForm()
    if form.validate_on_submit():
        current_user.create_playlist(form.title.data)
        flash(f'Playlist "{form.title.data}" creada correctamente.')
        return redirect(url_for('playlist'))
    
    return render_template('create_playlist.html', form=form)

@app.route('/playlist/<int:playlist_id>')
@login_required
def view_playlist(playlist_id):
    # Obtener la información de la playlist
    conn = get_db_connection()
    playlist = conn.execute('SELECT * FROM playlists WHERE id = ?', (playlist_id,)).fetchone()
    conn.close()
    
    if not playlist or playlist['user_id'] != current_user.id:
        flash('Playlist no encontrada o no tienes permisos para verla.')
        return redirect(url_for('playlist'))
    
    # Obtener las canciones de la playlist
    songs = []
    playlist_songs = get_playlist_songs(playlist_id)
    for song in playlist_songs:
        filename = song['filename']
        songs.append(filename)
    
    return render_template('view_playlist.html', 
                          playlist=playlist,
                          files=songs)

@app.route('/add_to_playlist/<filename>', methods=['GET', 'POST'])
@login_required
def add_to_playlist(filename):
    if request.method == 'POST':
        playlist_id = request.form.get('playlist_id')
        if playlist_id:
            add_song_to_playlist(playlist_id, filename)
            flash(f'Canción añadida a la playlist correctamente.')
        
        return redirect(url_for('playlist'))
    
    playlists = current_user.get_playlists()
    return render_template('add_to_playlist.html', filename=filename, playlists=playlists)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)