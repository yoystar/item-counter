# app.py
import os
import uuid
import time
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io

from detector import detect_items, match_template_items

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024  # 128 MB 单次上传上限

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_UPLOADS = 100   # uploads 目录最多保留文件数
MAX_AGE_DAYS = 30   # 超过此天数的文件在下次上传时被清理


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_safe_path(image_path: str) -> bool:
    abs_upload = os.path.abspath(UPLOAD_FOLDER)
    abs_image = os.path.abspath(image_path)
    return abs_image.startswith(abs_upload + os.sep)


def cleanup_uploads():
    """清理 uploads 目录：先删超过 MAX_AGE_DAYS 天的文件，再删最旧的直到剩 MAX_UPLOADS-1 张。"""
    if not os.path.isdir(UPLOAD_FOLDER):
        return
    cutoff = time.time() - MAX_AGE_DAYS * 86400

    files = []
    for fname in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, fname)
        if os.path.isfile(path):
            files.append((os.path.getmtime(path), path))

    remaining = []
    for mtime, path in files:
        if mtime < cutoff:
            try:
                os.remove(path)
            except OSError:
                pass
        else:
            remaining.append((mtime, path))

    # 按修改时间升序，超出上限时从最旧的开始删，保留 MAX_UPLOADS-1 张给新文件留位
    remaining.sort()
    for _, path in remaining[:max(0, len(remaining) - MAX_UPLOADS + 1)]:
        try:
            os.remove(path)
        except OSError:
            pass


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/upload', methods=['POST'])
def upload():
    cleanup_uploads()
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    try:
        with Image.open(save_path) as img:
            img.verify()
        with Image.open(save_path) as img:
            width, height = img.size
    except Exception:
        os.remove(save_path)
        return jsonify({'error': 'Invalid image file'}), 400

    return jsonify({
        'image_url': f'/uploads/{filename}',
        'image_path': save_path,
        'width': width,
        'height': height,
    })


@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'JSON body required'}), 400
    image_path = data.get('image_path', '')
    min_area = data.get('min_area', 500)
    max_area = data.get('max_area', None)
    block_size = data.get('block_size', 11)
    c_value = data.get('c_value', 2)
    morph_iterations = data.get('morph_iterations', 0)

    if not is_safe_path(image_path):
        return jsonify({'error': 'Invalid image path'}), 400

    try:
        items = detect_items(
            image_path,
            min_area=min_area,
            max_area=max_area,
            block_size=block_size,
            c_value=c_value,
            morph_iterations=morph_iterations,
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'items': items})


@app.route('/match', methods=['POST'])
def match():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'JSON body required'}), 400
    image_path = data.get('image_path', '')
    template_box = data.get('template_box', {})
    threshold = float(data.get('threshold', 0.7))

    if not is_safe_path(image_path):
        return jsonify({'error': 'Invalid image path'}), 400

    if not template_box or not all(k in template_box for k in ('x', 'y', 'w', 'h')):
        return jsonify({'error': 'Invalid template_box'}), 400

    try:
        items = match_template_items(image_path, template_box, threshold=threshold)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'items': items})


@app.route('/export', methods=['POST'])
def export():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'JSON body required'}), 400
    image_path = data.get('image_path', '')
    labels = data.get('labels', [])

    if not labels:
        return jsonify({'error': 'No labels provided'}), 400

    if not is_safe_path(image_path):
        return jsonify({'error': 'Invalid image path'}), 400

    try:
        img = Image.open(image_path).convert('RGBA')
    except Exception:
        return jsonify({'error': 'Cannot open image'}), 400

    w, h = img.size
    short_side = min(w, h)
    radius = max(14, min(int(short_side / 40), 28))
    font_size = max(12, int(radius * 1.2))

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except Exception:
        import warnings
        warnings.warn('DejaVuSans-Bold.ttf not found, using default font (quality may degrade)')
        font = ImageFont.load_default()

    for label in labels:
        x, y, number = int(label['x']), int(label['y']), label['number']
        if not (0 <= x < w and 0 <= y < h):
            continue
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=(231, 76, 60, 230)
        )
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text((x - (bbox[0] + bbox[2]) // 2, y - (bbox[1] + bbox[3]) // 2), text, fill=(255, 255, 255, 255), font=font)

    result = Image.alpha_composite(img, overlay).convert('RGB')
    buf = io.BytesIO()
    result.save(buf, format='PNG')
    buf.seek(0)

    return app.response_class(
        buf.read(),
        mimetype='image/png',
        headers={'Content-Disposition': 'attachment; filename=annotated.png'}
    )


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug)
