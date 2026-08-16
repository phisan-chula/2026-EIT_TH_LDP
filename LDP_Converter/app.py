from flask import Flask, render_template, request, jsonify
from LDP_Convert import LDPTransformer

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transform', methods=['POST'])
def process_coordinates():
    data = request.get_json()
    input_text = data.get('text', '')
    
    transformer = LDPTransformer(input_text)
    result_text = transformer.transform()
    
    return jsonify({'result': result_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
