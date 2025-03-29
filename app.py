from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, send_file
import os
import io
import zipfile
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User, init_db, get_db_connection, add_song_to_playlist, get_playlist_songs, is_playlist_public, is_playlist_owner

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Clave secreta para sesiones
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # Limita tamaño a 200MB
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}


# Filtro para formatear fechas
@app.template_filter('datetime')
def format_datetime(value):
    if value is None:
        return ""
    # Formatear la fecha como "día/mes/año hora:minuto"
    return value.strftime('%d/%m/%Y %H:%M')

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
        # Verificar si hay archivos en la solicitud
        if 'files[]' not in request.files:
            flash('No se encontraron archivos')
            return redirect(request.url)
        
        # Obtener la lista de archivos
        files = request.files.getlist('files[]')
        
        # Verificar si hay archivos seleccionados
        if not files or files[0].filename == '':
            flash('No se seleccionaron archivos')
            return redirect(request.url)
        
        # Determinar la playlist basado en la opción seleccionada
        playlist_id = None
        playlist_option = request.form.get('playlist_option', 'none')
        
        if playlist_option == 'existing':
            playlist_id = request.form.get('playlist_id')
        elif playlist_option == 'new':
            # Crear una nueva playlist
            new_playlist_title = request.form.get('new_playlist_title')
            if new_playlist_title and new_playlist_title.strip():
                # Crea la playlist
                current_user.create_playlist(new_playlist_title.strip())
                
                # Obtener el ID de la playlist recién creada
                conn = get_db_connection()
                new_playlist = conn.execute(
                    'SELECT id FROM playlists WHERE user_id = ? AND title = ? ORDER BY created_at DESC LIMIT 1',
                    (current_user.id, new_playlist_title.strip())
                ).fetchone()
                conn.close()
                
                if new_playlist:
                    playlist_id = new_playlist['id']
                    flash(f'¡Playlist "{new_playlist_title}" creada correctamente!')
        
        # Variables para contar resultados
        uploaded_count = 0
        error_count = 0
        added_to_playlist = 0
        
        # Procesar cada archivo
        for file in files:
            if file and allowed_file(file.filename):
                try:
                    # Asegurar el nombre del archivo
                    filename = secure_filename(file.filename)
                    
                    # Guardar el archivo
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    uploaded_count += 1
                    
                    # Si se seleccionó una playlist, añadir la canción a ella
                    if playlist_id:
                        add_song_to_playlist(playlist_id, filename)
                        added_to_playlist += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error al subir el archivo {file.filename}: {str(e)}")
            else:
                error_count += 1
        
        # Mostrar mensaje de resultado
        if uploaded_count > 0:
            if error_count > 0:
                flash(f'Se subieron {uploaded_count} archivos. Hubo problemas con {error_count} archivos.')
            else:
                if playlist_id and added_to_playlist > 0:
                    flash(f'¡Se subieron {uploaded_count} archivos y se añadieron a la playlist!')
                else:
                    flash(f'¡Se subieron {uploaded_count} archivos correctamente!')
        else:
            flash('No se pudo subir ningún archivo. Verifica que los formatos sean correctos.')
        
        # Redirigir a la playlist si se creó o seleccionó una
        if playlist_id:
            return redirect(url_for('view_playlist', playlist_id=playlist_id))
        else:
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
    
    # Verificar si se está reproduciendo desde una playlist específica
    playlist_id = request.args.get('playlist_id')
    
    if playlist_id:
        # Si hay un playlist_id en la URL, mostrar la vista de esa playlist
        try:
            playlist_id = int(playlist_id)
            conn = get_db_connection()
            playlist = conn.execute('SELECT * FROM playlists WHERE id = ?', (playlist_id,)).fetchone()
            conn.close()
            
            # Comprobar si el usuario puede ver la playlist
            can_view = False
            if current_user.is_authenticated and playlist and playlist['user_id'] == current_user.id:
                can_view = True
            elif playlist and is_playlist_public(playlist_id):
                can_view = True
            
            if not can_view:
                flash('Playlist no encontrada o no tienes permisos para verla.')
                return redirect(url_for('playlist'))
            
            songs = []
            playlist_songs = get_playlist_songs(playlist_id)
            for song in playlist_songs:
                songs.append(song['filename'])
            
            # Redireccionar según si es una playlist pública o privada
            if current_user.is_authenticated and playlist['user_id'] == current_user.id:
                return render_template('view_playlist.html', 
                                    playlist=playlist,
                                    files=songs,
                                    current_file=filename)
            else:
                # Es una playlist pública
                conn = get_db_connection()
                playlist_info = conn.execute('''
                    SELECT p.*, u.username
                    FROM playlists p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.id = ?
                ''', (playlist_id,)).fetchone()
                conn.close()
                
                return render_template('public_playlist.html', 
                                    playlist=playlist_info,
                                    files=songs,
                                    current_file=filename)
        except Exception as e:
            print(f"Error al cargar playlist: {str(e)}")
            # Si hay un error, mostrar la vista normal
            return render_template('playlist.html', 
                                  files=files,
                                  playlists=playlists,
                                  current_file=filename)
    else:
        # Si no hay playlist_id, mostrar la vista normal
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
    
    # Obtener la canción actual si hay una
    current_file = request.args.get('current_file')
    
    return render_template('view_playlist.html', 
                          playlist=playlist,
                          files=songs,
                          current_file=current_file)

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

@app.route('/share_playlist/<int:playlist_id>', methods=['POST'])
@login_required
def share_playlist(playlist_id):
    # Verificar que el usuario es propietario de la playlist
    conn = get_db_connection()
    playlist = conn.execute('SELECT * FROM playlists WHERE id = ?', (playlist_id,)).fetchone()
    
    if not playlist or playlist['user_id'] != current_user.id:
        flash('No tienes permisos para compartir esta playlist.')
        conn.close()
        return redirect(url_for('playlist'))
    
    # Verificar si ya está compartida
    shared = conn.execute('SELECT * FROM shared_playlists WHERE playlist_id = ?', (playlist_id,)).fetchone()
    
    if shared:
        # Actualizar estado de compartir
        is_public = 1 if request.form.get('is_public') else 0
        conn.execute('UPDATE shared_playlists SET is_public = ? WHERE playlist_id = ?', (is_public, playlist_id))
    else:
        # Crear nuevo registro de compartir
        is_public = 1 if request.form.get('is_public') else 0
        conn.execute('INSERT INTO shared_playlists (playlist_id, is_public) VALUES (?, ?)', (playlist_id, is_public))
    
    conn.commit()
    conn.close()
    
    flash('¡Tu playlist ahora está compartida!')
    return redirect(url_for('view_playlist', playlist_id=playlist_id))

@app.route('/public_playlists')
def public_playlists():
    conn = get_db_connection()
    
    # Obtener todas las playlists públicas con información del usuario
    public_playlists = conn.execute('''
        SELECT p.id, p.title, p.created_at, u.username, 
               (SELECT COUNT(*) FROM playlist_songs WHERE playlist_id = p.id) as song_count
        FROM playlists p
        JOIN shared_playlists sp ON p.id = sp.playlist_id
        JOIN users u ON p.user_id = u.id
        WHERE sp.is_public = 1
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('public_playlists.html', playlists=public_playlists)

@app.route('/public_playlist/<int:playlist_id>')
def public_playlist(playlist_id):
    conn = get_db_connection()
    
    # Verificar que la playlist existe y es pública
    playlist_check = conn.execute('''
        SELECT p.*, u.username
        FROM playlists p
        JOIN shared_playlists sp ON p.id = sp.playlist_id
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ? AND sp.is_public = 1
    ''', (playlist_id,)).fetchone()
    
    if not playlist_check:
        flash('Esta playlist no existe o no es pública.')
        conn.close()
        return redirect(url_for('public_playlists'))
    
    # Obtener las canciones de la playlist
    songs = []
    playlist_songs = get_playlist_songs(playlist_id)
    for song in playlist_songs:
        filename = song['filename']
        songs.append(filename)
    
    # Obtener los comentarios de la playlist
    comments = conn.execute('''
        SELECT c.comment, c.created_at, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.playlist_id = ?
        ORDER BY c.created_at DESC
    ''', (playlist_id,)).fetchall()
    
    conn.close()
    
    # Obtener la canción actual si hay una
    current_file = request.args.get('current_file')
    
    return render_template('public_playlist.html', 
                          playlist=playlist_check,
                          files=songs,
                          current_file=current_file,
                          comments=comments)

@app.route('/add_comment/<int:playlist_id>', methods=['POST'])
@login_required
def add_comment(playlist_id):
    comment_text = request.form.get('comment')
    
    if not comment_text or not comment_text.strip():
        flash('El comentario no puede estar vacío.')
        return redirect(url_for('public_playlist', playlist_id=playlist_id))
    
    conn = get_db_connection()
    
    # Verificar que la playlist existe y es pública
    playlist_check = conn.execute('''
        SELECT p.*
        FROM playlists p
        JOIN shared_playlists sp ON p.id = sp.playlist_id
        WHERE p.id = ? AND sp.is_public = 1
    ''', (playlist_id,)).fetchone()
    
    if not playlist_check:
        flash('Esta playlist no existe o no es pública.')
        conn.close()
        return redirect(url_for('public_playlists'))
    
    # Añadir el comentario
    conn.execute('''
        INSERT INTO comments (user_id, playlist_id, comment)
        VALUES (?, ?, ?)
    ''', (current_user.id, playlist_id, comment_text.strip()))
    
    conn.commit()
    conn.close()
    
    flash('¡Comentario añadido correctamente!')
    return redirect(url_for('public_playlist', playlist_id=playlist_id))

@app.route('/download_playlist/<int:playlist_id>')
def download_playlist(playlist_id):
    conn = get_db_connection()
    
    # Verificar que la playlist existe y es accesible
    if current_user.is_authenticated:
        # El usuario puede descargar sus propias playlists
        playlist_check = conn.execute('''
            SELECT p.*
            FROM playlists p
            WHERE p.id = ? AND (p.user_id = ? OR EXISTS (SELECT 1 FROM shared_playlists sp WHERE sp.playlist_id = p.id AND sp.is_public = 1))
        ''', (playlist_id, current_user.id)).fetchone()
    else:
        # Solo playlists públicas para usuarios no autenticados
        playlist_check = conn.execute('''
            SELECT p.*
            FROM playlists p
            JOIN shared_playlists sp ON p.id = sp.playlist_id
            WHERE p.id = ? AND sp.is_public = 1
        ''', (playlist_id,)).fetchone()
    
    if not playlist_check:
        flash('Esta playlist no existe o no tienes acceso a ella.')
        conn.close()
        return redirect(url_for('playlist'))
    
    # Obtener las canciones de la playlist
    songs = []
    playlist_songs = get_playlist_songs(playlist_id)
    for song in playlist_songs:
        filename = song['filename']
        songs.append(filename)
    
    conn.close()
    
    # Si no hay canciones, redirigir
    if not songs:
        flash('Esta playlist está vacía.')
        return redirect(url_for('view_playlist', playlist_id=playlist_id))
    
    # Crear un archivo ZIP en memoria
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for song in songs:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], song)
            if os.path.exists(file_path):
                zf.write(file_path, song)
    
    memory_file.seek(0)
    
    # Obtener título seguro para el archivo
    playlist_title = secure_filename(playlist_check['title'])
    zip_filename = f"{playlist_title}_playlist.zip"
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@app.route('/community')
def community():
    return redirect(url_for('public_playlists'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)