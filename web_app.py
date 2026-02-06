from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.agent.command_router import handle_command
from app.utils.sentiment_analysis import analyze_sentiment, generate_word_cloud, generate_pie_chart

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sentiment', methods=['POST'])

def get_sentiment():
    data = request.get_json()
    articles = data.get('articles', [])
    sentiments, words = analyze_sentiment(articles)
    generate_word_cloud(words)
    generate_pie_chart(sentiments)
    return jsonify({'sentiments': sentiments}), 200

@app.route('/api/command', methods=['POST'])
def execute_command():
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'error': 'Command is required'}), 400
        
        if command.lower() in ('quit', 'exit'):
            return jsonify({'message': 'Session ended'}), 200
        
        result = handle_command(command)
        return jsonify({'result': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 VN Stock AI Agent Web Interface")
    print("📊 Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
