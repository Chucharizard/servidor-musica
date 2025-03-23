from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Limita tamaño a 32MB
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

# Asegúrate de que la carpeta de uploads exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Verifica si la solicitud tiene el archivo
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        # Si el usuario no selecciona un archivo
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('playlist'))
    
    return render_template('upload.html')

@app.route('/playlist')
def playlist():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if allowed_file(filename):
            files.append(filename)
    return render_template('playlist.html', files=files)

@app.route('/play/<filename>')
def play_file(filename):
    return render_template('playlist.html', 
                          files=os.listdir(app.config['UPLOAD_FOLDER']),
                          current_file=filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)