from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

# 從環境變數取得 Gist ID 和 GitHub Token
GIST_ID = os.environ.get('GIST_ID')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英雄榜查詢系統</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .search-box {
            margin: 20px 0;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .hero-list {
            margin-top: 20px;
        }
        .hero-item {
            background-color: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 英雄榜查詢系統</h1>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="請輸入姓名查詢...">
            <button onclick="searchHero()">查詢</button>
        </div>
        <div id="result"></div>
        <div class="hero-list" id="heroList"></div>
    </div>

    <script>
        function searchHero() {
            const name = document.getElementById('searchInput').value.trim();
            if (!name) {
                showResult('請輸入姓名', 'error');
                return;
            }
            
            fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({name: name})
            })
            .then(response => response.json())
            .then(data => {
                if (data.found) {
                    showResult(`找到了！${name} 在英雄榜上 🎉`, 'success');
                } else {
                    showResult(`未找到 ${name}`, 'error');
                }
            })
            .catch(error => {
                showResult('查詢時發生錯誤', 'error');
            });
        }

        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.className = 'result ' + type;
            resultDiv.textContent = message;
        }

        function loadHeroes() {
            fetch('/heroes')
            .then(response => response.json())
            .then(data => {
                const listDiv = document.getElementById('heroList');
                if (data.heroes && data.heroes.length > 0) {
                    listDiv.innerHTML = '<h3>目前英雄榜名單：</h3>';
                    data.heroes.forEach(hero => {
                        const div = document.createElement('div');
                        div.className = 'hero-item';
                        div.textContent = hero;
                        listDiv.appendChild(div);
                    });
                }
            });
        }

        // 頁面載入時顯示所有英雄
        loadHeroes();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'found': False, 'message': '請輸入姓名'})
    
    # 從 Gist 讀取資料
    heroes = get_heroes_from_gist()
    
    found = name in heroes
    return jsonify({'found': found})

@app.route('/heroes', methods=['GET'])
def get_heroes():
    heroes = get_heroes_from_gist()
    return jsonify({'heroes': heroes})

def get_heroes_from_gist():
    """從 GitHub Gist 讀取英雄名單"""
    try:
        url = f'https://api.github.com/gists/{GIST_ID}'
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            gist_data = response.json()
            # 假設 Gist 中有一個檔案叫 heroes.json
            for filename, file_content in gist_data['files'].items():
                content = file_content['content']
                import json
                try:
                    data = json.loads(content)
                    return data.get('heroes', [])
                except:
                    # 如果不是 JSON，就當作純文字，一行一個名字
                    return [line.strip() for line in content.split('\n') if line.strip()]
        return []
    except Exception as e:
        print(f'Error reading from Gist: {e}')
        return []

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
