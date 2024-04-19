from flask import Flask, request, jsonify, make_response
from extract import extractURL
import gc

app = Flask(__name__)
@app.route('/mk1/trafilatura', methods=['POST'])
def detect_text():
  gc.collect()
  try:
    data = request.get_json()
    url = data['url']
    try:
        extract_data = extractURL(url)
    except Exception as e:
        raise ValueError(f"Forbidden ... {str(e)}")
    return make_response(extract_data, 200)
  except Exception as e:
    return make_response(jsonify({'message': str(e), "code": 403}), 403)
if __name__ == "__main__":
    app.run(debug=True)
