from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
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
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)