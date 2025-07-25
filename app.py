from flask import Flask, render_template, request, redirect, url_for,send_from_directory, abort
from werkzeug.utils import safe_join
import os
import sys
import threading
import webbrowser
from tackle_tool import process_zip
from tackle_tool import custom_secure_filename

app = Flask(__name__)
# 判断是否是 PyInstaller 打包的可执行文件
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 真正可用的上传和输出目录
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        zip_file = request.files['zip_file']
        if zip_file and zip_file.filename.endswith('.zip'):
            filename = custom_secure_filename(zip_file.filename)
            print("--------------------")
            print(f"上传的文件名: {zip_file.filename}")
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
    try:
        full_path = safe_join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(full_path):
            abort(404)
        directory = os.path.dirname(full_path)
        file = os.path.basename(full_path)
        return send_from_directory(directory, file, as_attachment=True)
    except:
        abort(404)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run()