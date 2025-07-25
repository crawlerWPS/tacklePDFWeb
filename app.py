from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import threading
import webbrowser
from werkzeug.utils import secure_filename
from tackle_tool import process_zip

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        zip_file = request.files['zip_file']
        if zip_file and zip_file.filename.endswith('.zip'):
            filename = secure_filename(zip_file.filename)
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            zip_file.save(zip_path)

            process_zip(zip_path, 
                        extract_dir=zip_path + "_extracted", 
                        output_zip=zip_path.replace('.zip', '_processed.zip'))

            return redirect(url_for('result', 
                                    zipname=os.path.basename(zip_path.replace('.zip', '_processed.zip'))))
    return render_template('index.html')

@app.route('/result/<zipname>')
def result(zipname):
    return render_template('result.html', zipname=zipname)


@app.route('/download/<path:filename>')
def download_file(filename):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(full_path):
        return f"❌ 文件未找到：{full_path}", 404

    return send_file(full_path, as_attachment=True)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run()