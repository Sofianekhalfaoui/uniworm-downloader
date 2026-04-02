import os, uuid, json
from flask import Flask, request, render_template_string, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

STYLE = '''
<style>
:root { --primary: #7c3aed; --accent: #00ffcc; --bg: #0b0e14; --card: rgba(22, 27, 34, 0.8); }
body { 
    background: radial-gradient(circle at top, #1e1b4b, #0b0e14); 
    color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    direction: rtl; padding: 20px; min-height: 100vh;
}
.card { 
    background: var(--card); backdrop-filter: blur(15px);
    border: 1px solid rgba(124, 58, 237, 0.3); padding: 30px; 
    border-radius: 24px; max-width: 550px; margin: auto; 
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
}
h2 { color: var(--primary); text-shadow: 0 0 10px rgba(124, 58, 237, 0.5); }
input, select { 
    width: 100%; padding: 15px; border-radius: 12px; 
    background: rgba(13, 17, 23, 0.9); border: 1px solid #30363d; 
    color: white; margin-bottom: 15px; outline: none; font-size: 16px;
}
.btn { 
    background: linear-gradient(45deg, var(--primary), #4f46e5); 
    padding: 16px; border: none; color: white; border-radius: 12px; 
    width: 100%; font-weight: bold; cursor: pointer; font-size: 18px;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
}
.preview-box { 
    display: none; background: rgba(0,0,0,0.3); 
    padding: 15px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #333;
}
.preview-img { width: 100%; border-radius: 10px; margin-bottom: 10px; }
.loader { 
    display: none; margin: 20px auto; border: 4px solid #1a1a1a; 
    border-top: 4px solid var(--accent); border-radius: 50%; 
    width: 35px; height: 35px; animation: spin 1s linear infinite; 
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.history { margin-top: 25px; text-align: right; font-size: 14px; color: #8b949e; }
</style>
'''

@app.route('/')
def home():
    return render_template_string(STYLE + '''
    <div class="card">
        <h2>🚀 UNIWORM Downloader</h2>
        <p style="color:#8b949e">TikTok • YouTube • Instagram • Facebook</p>
        
        <input type="text" id="url" placeholder="ضع رابط الفيديو هنا..." oninput="fetchInfo()">
        
        <div id="preview" class="preview-box">
            <img id="thumb" class="preview-img">
            <div id="title" style="font-size:14px; font-weight:bold; margin-bottom:10px"></div>
        </div>

        <select id="format">
            <optgroup label="فيديو (MP4)">
                <option value="1080">1080p (FHD)</option>
                <option value="720" selected>720p (HD)</option>
                <option value="480">480p (SD)</option>
                <option value="360">360p</option>
                <option value="144">144p</option>
            </optgroup>
            <optgroup label="صوت فقط (Audio)">
                <option value="mp3">تحميل بصيغة MP3</option>
            </optgroup>
        </select>

        <button class="btn" onclick="startDownload()">تحميل الآن 🔥</button>
        <div class="loader" id="ld"></div>
        <div id="status" style="margin-top:15px"></div>
        
        <div class="history" id="hist">
            آخر التحميلات: <br> <span id="hist-list">لا يوجد سجل حالياً</span>
        </div>
    </div>

    <script>
    function fetchInfo() {
        let url = document.getElementById("url").value;
        if(url.length < 10) return;
        
        fetch("/get_info", {
            method: "POST",
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: url})
        }).then(r => r.json()).then(data => {
            if(data.success) {
                document.getElementById("preview").style.display = "block";
                document.getElementById("thumb").src = data.thumb;
                document.getElementById("title").innerText = data.title;
            }
        });
    }

    function startDownload() {
        let url = document.getElementById("url").value;
        let fmt = document.getElementById("format").value;
        if(!url) return alert("أدخل الرابط!");

        document.getElementById("ld").style.display = "block";
        document.getElementById("status").innerText = "جاري التحميل... قد يستغرق ذلك دقيقة";

        fetch("/download", {
            method: "POST",
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: url, format: fmt})
        }).then(r => r.json()).then(data => {
            document.getElementById("ld").style.display = "none";
            if(data.success) {
                document.getElementById("status").innerHTML = "✅ تم! <a href='/file/"+data.file+"' style='color:#00ffcc' download>اضغط هنا للحفظ</a>";
                saveToHistory(data.title);
            } else {
                document.getElementById("status").innerText = "❌ فشل: " + data.error;
            }
        });
    }

    function saveToHistory(name) {
        let list = document.getElementById("hist-list");
        if(list.innerText.includes("لا يوجد")) list.innerHTML = "";
        list.innerHTML = "• " + name.substring(0,30) + "...<br>" + list.innerHTML;
    }
    </script>
    ''')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "success": True, 
                "title": info.get('title', 'Video'), 
                "thumb": info.get('thumbnail', '')
            })
    except: return jsonify({"success": False})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url, fmt = data.get('url'), data.get('format')
    uid = str(uuid.uuid4())
    
    # اختيار الجودة
    if fmt == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            'outtmpl': f'{DOWNLOAD_FOLDER}/{uid}.mp3'
        }
    else:
        # جودة محددة (144، 360، 720...)
        ydl_opts = {
            'format': f'bestvideo[height<={fmt}]+bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/{uid}.%(ext)s',
            'merge_output_format': 'mp4'
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = os.path.basename(ydl.prepare_filename(info))
            # في حالة MP3 يتغير الامتداد يدوياً بعد المعالجة
            if fmt == "mp3": filename = uid + ".mp3"
            return jsonify({"success": True, "file": filename, "title": info.get('title')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/file/<f>')
def send_f(f): return send_from_directory(DOWNLOAD_FOLDER, f)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
