# app.py
import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io

from detector import detect_items

app = Flask(__name__, static_folder='static', static_url_path='')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/upload', methods=['POST'])
def upload():
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

    with Image.open(save_path) as img:
        width, height = img.size

    return jsonify({
        'image_url': f'/uploads/{filename}',
        'image_path': save_path,
        'width': width,
        'height': height,
    })


@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json()
    image_path = data.get('image_path', '')
    min_area = data.get('min_area', 500)
    max_area = data.get('max_area', None)

    try:
        items = detect_items(image_path, min_area=min_area, max_area=max_area)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'items': items})


@app.route('/export', methods=['POST'])
def export():
    data = request.get_json()
    image_path = data.get('image_path', '')
    labels = data.get('labels', [])

    if not labels:
        return jsonify({'error': 'No labels provided'}), 400

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
        font = ImageFont.load_default()

    for label in labels:
        x, y, number = int(label['x']), int(label['y']), label['number']
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=(231, 76, 60, 230)
        )
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw // 2, y - th // 2), text, fill=(255, 255, 255, 255), font=font)

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
    app.run(debug=True, port=5000)
