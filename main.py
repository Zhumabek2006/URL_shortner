from flask import Flask, request, jsonify, redirect
from urllib.parse import urlparse
import threading

app = Flask(__name__)

BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class URLShortener:
    def __init__(self):
        self.counter = 0
        self.short_to_data = {}
        self.long_to_short = {}
        self.lock = threading.Lock()

    def encode_base62(self, num):
        if num == 0:
            return "0"

        result = []

        while num > 0:
            result.append(BASE62[num % 62])
            num //= 62

        return ''.join(reversed(result))

    def generate_short_code(self):
        self.counter += 1
        return self.encode_base62(self.counter)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return parsed.scheme and parsed.netloc

    def shorten(self, original_url):
        with self.lock:
            if original_url in self.long_to_short:
                return self.long_to_short[original_url]

            short_code = self.generate_short_code()

            self.short_to_data[short_code] = {
                "original_url": original_url,
                "clicks": 0
            }

            self.long_to_short[original_url] = short_code

            return short_code

    def get_original_url(self, short_code):
        return self.short_to_data.get(short_code)

    def increment_clicks(self, short_code):
        with self.lock:
            if short_code in self.short_to_data:
                self.short_to_data[short_code]["clicks"] += 1


shortener = URLShortener()


@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({"error": "URL required"}), 400

    original_url = data['url']

    if not shortener.is_valid_url(original_url):
        return jsonify({"error": "Invalid URL"}), 400

    short_code = shortener.shorten(original_url)

    return jsonify({
        "short_url": f"http://localhost:5000/{short_code}"
    }), 201


@app.route('/stats/<short_code>')
def stats(short_code):
    data = shortener.get_original_url(short_code)

    if not data:
        return jsonify({"error": "Not found"}), 404

    return jsonify(data)


@app.route('/<short_code>')
def redirect_url(short_code):
    data = shortener.get_original_url(short_code)

    if not data:
        return jsonify({"error": "URL not found"}), 404

    shortener.increment_clicks(short_code)

    return redirect(data["original_url"], code=302)


@app.route('/')
def home():
    return jsonify({
        "message": "URL Shortener API",
        "endpoints": {
            "POST /shorten": "Create short URL",
            "GET /<code>": "Redirect",
            "GET /stats/<code>": "Get stats"
        }
    })


if __name__ == '__main__':
    app.run(debug=True)