import urllib.request
import urllib.parse
import zlib
import base64
import os
import string

def encode_plantuml(text):
    """PlantUML 编码算法"""
    # PlantUML uses a custom encoding based on deflate
    # First, encode as UTF-8
    data = text.encode('utf-8')

    # Deflate compress
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    compressed = compressor.compress(data) + compressor.flush()

    # PlantUML's custom base64-like encoding
    res = encode6bit(compressed)
    return res

def encode6bit(b):
    """Encode bytes to PlantUML's custom base64"""
    result = ""
    # Process 3 bytes at a time -> 4 characters
    for i in range(0, len(b), 3):
        chunk = b[i:i+3]
        if len(chunk) == 3:
            b1, b2, b3 = chunk
            result += encode6bitChar(b1 >> 2)
            result += encode6bitChar(((b1 & 0x3) << 4) | (b2 >> 4))
            result += encode6bitChar(((b2 & 0xF) << 2) | (b3 >> 6))
            result += encode6bitChar(b3 & 0x3F)
        elif len(chunk) == 2:
            b1, b2 = chunk
            result += encode6bitChar(b1 >> 2)
            result += encode6bitChar(((b1 & 0x3) << 4) | (b2 >> 4))
            result += encode6bitChar((b2 & 0xF) << 2)
        elif len(chunk) == 1:
            b1 = chunk[0]
            result += encode6bitChar(b1 >> 2)
            result += encode6bitChar((b1 & 0x3) << 4)
    return result

def encode6bitChar(b):
    """Map 6-bit value to character"""
    if b < 10:
        return chr(48 + b)  # 0-9
    elif b < 36:
        return chr(65 + b - 10)  # A-Z
    elif b < 62:
        return chr(97 + b - 36)  # a-z
    elif b == 62:
        return '-'
    elif b == 63:
        return '_'
    else:
        return '?'

def render_plantuml(puml_file, output_file):
    """Render a PlantUML file to PNG using the online server"""
    with open(puml_file, 'r', encoding='utf-8') as f:
        text = f.read()

    encoded = encode_plantuml(text)
    url = f"http://www.plantuml.com/plantuml/png/~1{encoded}"

    print(f"Rendering: {puml_file}")
    print(f"URL: {url}")

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            with open(output_file, 'wb') as f:
                f.write(data)
            print(f"  -> Saved to: {output_file} ({len(data)} bytes)")
            return True
    except Exception as e:
        print(f"  -> Error: {e}")
        return False

if __name__ == "__main__":
    uml_dir = r"d:\I J\rag-knowledge-qa\uml"

    files = [
        ("usecase1_user.puml", "usecase1_user.png"),
        ("usecase2_up.puml", "usecase2_up.png"),
        ("activity_watch.puml", "activity_watch.png"),
    ]

    for puml, png in files:
        puml_path = os.path.join(uml_dir, puml)
        png_path = os.path.join(uml_dir, png)
        render_plantuml(puml_path, png_path)
