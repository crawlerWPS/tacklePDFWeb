import os
import zipfile
import shutil
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from pathlib import Path
import sys

log_lines = []

def log(msg):
    try:
        if not isinstance(msg, str):
            msg = str(msg)
        print(msg)
    except UnicodeEncodeError:
        try:
            # fallback：将无法编码的字符替换掉
            safe_msg = msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace')
            print(safe_msg)
        except Exception:
            print("[警告] 控制台无法显示部分字符。")
    log_lines.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def is_valid_pdf(path):
    try:
        with open(path, 'rb') as f:
            header = f.read(5)
        return header == b'%PDF-'
    except:
        return False

def process_pdf(pdf_path, backup_dir):
    filename = os.path.basename(pdf_path)

    if not is_valid_pdf(pdf_path):
        log(f"[跳过] {filename} 不是合法 PDF 文件")
        return

    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
    except Exception as e:
        log(f"[错误] 无法读取 {filename}，原因：{e}")
        return

    # 创建备份文件
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, filename.replace(".pdf", ".bak.pdf"))
    shutil.copy2(pdf_path, backup_path)
    log(f"[备份] {filename} 已备份至 backup_pdfs/")

    if num_pages <= 1:
        log(f"[保留] {filename} 只有1页，原样保留")
        return

    # 多页 PDF：提取最后一页
    writer = PdfWriter()
    writer.add_page(reader.pages[-1])
    temp_path = pdf_path + ".temp.pdf"
    try:
        with open(temp_path, "wb") as f:
            writer.write(f)
        os.remove(pdf_path)
        os.rename(temp_path, pdf_path)
        log(f"[处理] {filename} 多页截取完成，已保留最后一页")
    except Exception as e:
        log(f"[错误] 写入失败 {filename}，原因：{e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

def process_zip(zip_path, extract_dir="extracted_pdfs", output_zip="processed_output.zip"):
    if not os.path.isfile(zip_path):
        log(f"[错误] 压缩包不存在：{zip_path}")
        return

    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    # 解压并手动处理中文路径
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for zip_info in zip_ref.infolist():
                if zip_info.is_dir():
                    continue

                raw_filename = zip_info.filename.encode('cp437')
                try:
                    filename = raw_filename.decode('utf-8')
                except UnicodeDecodeError:
                    filename = raw_filename.decode('gbk', errors='replace')

                abs_path = os.path.join(extract_dir, filename)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with zip_ref.open(zip_info) as source, open(abs_path, 'wb') as target:
                    shutil.copyfileobj(source, target)

        log(f"[解压] 成功解压至：{extract_dir}")
    except Exception as e:
        log(f"[错误] 解压失败：{e}")
        return

    # 创建备份目录
    backup_dir = os.path.join(extract_dir, "backup_pdfs")

    # 处理 PDF 文件（跳过备份目录）
    for root, _, files in os.walk(extract_dir):
        if os.path.abspath(root).startswith(os.path.abspath(backup_dir)):
            continue
        for file in files:
            if file.lower().endswith(".pdf") and not file.startswith("._"):
                pdf_path = os.path.join(root, file)
                process_pdf(pdf_path, backup_dir)

    # 写入日志
    log_path = os.path.join(extract_dir, "processing_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    log(f"[完成] 日志已保存至：{log_path}")

    # 打包为 zip
    try:
        if os.path.exists(output_zip):
            os.remove(output_zip)
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for foldername, subfolders, filenames in os.walk(extract_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, extract_dir)
                    zipf.write(file_path, arcname)
        log(f"[打包完成] 已生成压缩包：{output_zip}")
    except Exception as e:
        log(f"[错误] 打包失败：{e}")
        
        
        
import re

def custom_secure_filename(filename):
    """
    更宽容地保留中文、常用字符，仅移除危险符号和控制字符。
    """
    filename = os.path.basename(filename)  # 防止路径注入
    # 替换非法字符为下划线（只保留中英文、数字、下划线、点号和括号）
    filename = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9_.()（）-]+", "_", filename)
    # 防止空文件名
    return filename or "unnamed.zip"