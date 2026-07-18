"""合成器助手 — Flask Web 应用"""

import sys, os
from pathlib import Path

if sys.platform == "win32":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"

# 项目根目录
_PROJ = Path(__file__).parent.parent
_ENV_FILE = _PROJ / ".env"

# 加载 .env (如果有)
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from flask import Flask, request, jsonify
from app.retriever import answer

app = Flask(__name__)
app.json.ensure_ascii = False


# ─── 首页 HTML ───
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎛️ 合成器助手</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI","Noto Sans SC",sans-serif;background:#0f0f12;color:#e0e0e0;height:100vh;display:flex;flex-direction:column}
header{background:#1a1a22;padding:12px 20px;border-bottom:1px solid #2a2a35;display:flex;align-items:center;gap:12px;flex-shrink:0}
header h1{font-size:18px;font-weight:600}
header span{color:#888;font-size:12px}
.mode-switcher{display:flex;gap:4px;background:#0f0f12;border-radius:8px;padding:3px;margin:0 12px}
.mode-btn{background:transparent;border:none;color:#666;padding:5px 14px;border-radius:6px;cursor:pointer;font-size:12px;transition:all .15s;white-space:nowrap}
.mode-btn:hover{color:#aaa}
.mode-btn.active{background:#2a2a35;color:#e0e0e0}
.settings-btn{margin-left:auto;background:#2a2a35;border:none;color:#aaa;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px}
.settings-btn:hover{background:#3a3a45;color:#fff}
.main{display:flex;flex:1;overflow:hidden}
#adsrMode{flex:1;display:none;background:#0a0a0f;overflow:hidden}
#adsrMode iframe{width:100%;height:100%;border:none;display:block}

/* 设置面板 */
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:100;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:#1a1a24;border-radius:12px;padding:24px;width:460px;max-width:90vw}
.modal h2{font-size:16px;margin-bottom:16px}
.modal label{display:block;font-size:13px;color:#aaa;margin:10px 0 4px}
.modal input{width:100%;background:#0f0f12;border:1px solid #333;border-radius:6px;padding:8px 12px;color:#e0e0e0;font-size:14px}
.modal input:focus{border-color:#8ab4f8;outline:none}
.modal-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
.modal-actions button{padding:8px 20px;border-radius:6px;border:none;cursor:pointer;font-size:13px}
.btn-primary{background:#8ab4f8;color:#000}
.btn-secondary{background:#2a2a35;color:#aaa}

/* 侧栏 */
.sidebar{width:360px;background:#14141c;border-right:1px solid #2a2a35;display:flex;flex-direction:column;flex-shrink:0;overflow:hidden}
.sidebar-tabs{display:flex;border-bottom:1px solid #2a2a35;flex-shrink:0}
.sidebar-tab{flex:1;padding:10px;text-align:center;font-size:13px;cursor:pointer;color:#666;border-bottom:2px solid transparent}
.sidebar-tab.active{color:#8ab4f8;border-bottom-color:#8ab4f8}
.sidebar-content{flex:1;overflow-y:auto;padding:12px}

/* 引用卡片 */
.ref-card{background:#1a1a24;border-radius:8px;padding:12px;margin-bottom:8px;border-left:3px solid #555}
.ref-card .r-title{font-weight:500;font-size:13px;color:#8ab4f8;margin-bottom:2px}
.ref-card .r-source{font-size:11px;color:#555}
.ref-card .r-snippet{font-size:12px;color:#999;line-height:1.5;margin-top:6px}
.ref-card .r-score{font-size:11px;color:#555;margin-top:4px}

/* 流程日志 */
.log-entry{padding:8px 12px;margin-bottom:6px;border-radius:6px;font-size:12px;line-height:1.5}
.log-search{background:#1a1a28;border-left:3px solid #8ab4f8}
.log-found{background:#1a2428;border-left:3px solid #4a9}
.log-llm{background:#24201a;border-left:3px solid #fa4}
.log-done{background:#1a241a;border-left:3px solid #4a4}
.log-entry .log-time{color:#555;font-size:11px}
.log-entry .log-emoji{margin-right:4px}
.log-context{background:#0f0f12;border-radius:4px;padding:8px;margin-top:6px;font-family:monospace;font-size:11px;color:#888;max-height:200px;overflow-y:auto;white-space:pre-wrap;display:none}
.log-context.show{display:block}
.toggle-context{color:#8ab4f8;cursor:pointer;font-size:11px;margin-top:4px;display:inline-block}
.toggle-context:hover{text-decoration:underline}

/* 聊天区 */
.chat-area{flex:1;display:flex;flex-direction:column}
.messages{flex:1;overflow-y:auto;padding:16px 20px}
.msg{margin-bottom:16px}
.msg-q{color:#8ab4f8;font-size:12px;font-weight:500;margin-bottom:2px}
.msg-q-text{font-size:14px;line-height:1.6}
.msg-a{color:#6abf6a;font-size:12px;font-weight:500;margin-bottom:2px}
.msg-a-text{font-size:14px;line-height:1.7;color:#ccc;white-space:pre-wrap}
.input-area{border-top:1px solid #2a2a35;padding:12px 20px;display:flex;gap:10px;background:#1a1a22}
.input-area input{flex:1;background:#0f0f12;border:1px solid #333;border-radius:8px;padding:10px 14px;color:#e0e0e0;font-size:14px;outline:none}
.input-area input:focus{border-color:#8ab4f8}
.input-area button{background:#8ab4f8;color:#000;border:none;border-radius:8px;padding:10px 20px;font-size:14px;font-weight:500;cursor:pointer}
.input-area button:disabled{opacity:0.4;cursor:not-allowed}
</style>
</head>
<body>

<header>
  <h1>🎛️ 合成器助手</h1>
  <span>RAG 问答 · 知识库 296 条</span>
  <div class="mode-switcher">
    <button class="mode-btn active" data-mode="chat" onclick="switchMode('chat')">💬 问答</button>
    <button class="mode-btn" data-mode="adsr" onclick="switchMode('adsr')">📊 ADSR</button>
  </div>
  <button class="settings-btn" onclick="openSettings()">⚙️ 设置</button>
</header>

<!-- 设置弹窗 -->
<div class="modal-overlay" id="settingsModal">
<div class="modal">
  <h2>⚙️ LLM 配置</h2>
  <label>API Key</label>
  <input id="sApiKey" type="password" placeholder="sk-...">
  <label>API 地址 (Base URL)</label>
  <input id="sBaseUrl" value="https://api.deepseek.com">
  <label>模型名称</label>
  <input id="sModel" value="deepseek-chat">
  <div id="sTestResult" style="font-size:12px;margin-top:8px;padding:6px;border-radius:4px;display:none"></div>
  <div class="modal-actions">
    <button class="btn-secondary" onclick="testKey()">🔌 测试连接</button>
    <button class="btn-secondary" onclick="closeSettings()">取消</button>
    <button class="btn-primary" onclick="saveSettings()">保存</button>
  </div>
</div>
</div>

<div class="main">
<div id="chatMode" style="display:flex;flex:1">
<!-- 侧栏 -->
<div class="sidebar">
  <div class="sidebar-tabs">
    <div class="sidebar-tab active" data-tab="refs" onclick="switchTab('refs')">📄 引用</div>
    <div class="sidebar-tab" data-tab="flow" onclick="switchTab('flow')">⚡ 流程</div>
  </div>
  <div class="sidebar-content" id="refsPanel">
    <div class="sidebar-empty" style="color:#555;text-align:center;padding:40px 20px;font-size:13px">发送问题后<br>相关片段将显示在这里</div>
  </div>
  <div class="sidebar-content" id="flowPanel" style="display:none">
    <div class="sidebar-empty" style="color:#555;text-align:center;padding:40px 20px;font-size:13px">每次问答的完整处理流程<br>将在这里逐步展示</div>
  </div>
</div>

<!-- 聊天区 -->
<div class="chat-area">
  <div class="messages" id="messages">
    <div class="msg">
      <div class="msg-a-text" style="color:#888;font-size:13px;">
        问关于合成器的任何问题。<br>
        例：<em>"ADSR 各阶段的作用"</em> · <em>"怎么做 Pluck 音色"</em> · <em>"滤波器种类"</em>
      </div>
    </div>
  </div>
  <div class="input-area">
    <input type="text" id="queryInput" placeholder="输入问题…" autofocus>
    <button id="sendBtn">发送</button>
  </div>
</div>
</div>

<!-- ADSR 编辑器模式 -->
<div id="adsrMode">
  <iframe src="/static/adsr-editor.html" title="ADSR 包络编辑器" style="width:100%;height:100%;border:none;display:block"></iframe>
</div>
</div>

<script>
// === 设置 ===
async function openSettings() {
  var res=await fetch('/api/env-config');
  var cfg=await res.json();
  document.getElementById('sApiKey').value = cfg.api_key || '';
  document.getElementById('sBaseUrl').value = cfg.base_url || 'https://api.deepseek.com';
  document.getElementById('sModel').value = cfg.model || 'deepseek-chat';
  document.getElementById('settingsModal').classList.add('show');
}
function closeSettings() {
  document.getElementById('settingsModal').classList.remove('show');
}
function saveSettings() {
  var key=document.getElementById('sApiKey').value.trim();
  var url=document.getElementById('sBaseUrl').value.trim();
  var model=document.getElementById('sModel').value.trim();
  fetch('/api/save-env',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({api_key:key,base_url:url,model:model})
  }).then(function(r){return r.json()}).then(function(data){
    var r=document.getElementById('sTestResult');
    r.style.display='block';
    if(data.ok){
      r.style.background='#1a241a';r.style.color='#8c8';
      r.textContent='✅ 已保存到 .env (仅本地, 不会上传Git)';
    }else{
      r.style.background='#2a1a1a';r.style.color='#c88';
      r.textContent='❌ 保存失败: '+data.message;
    }
    setTimeout(function(){r.style.display='none'},4000);
  });
}
async function testKey(){
  var key=document.getElementById('sApiKey').value.trim();
  var url=document.getElementById('sBaseUrl').value.trim();
  var model=document.getElementById('sModel').value.trim();
  if(!key){showTestRes('❌ 请先填写 API Key','#2a1a1a','#c88');return;}
  var r=document.getElementById('sTestResult');
  r.style.display='block';r.style.background='#1a1a28';r.style.color='#888';
  r.textContent='⏳ 测试连接中…';
  try{
    var res=await fetch('/api/test-key',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({api_key:key,base_url:url,model:model})
    });
    var data=await res.json();
    if(data.ok) showTestRes('✅ '+data.message,'#1a241a','#8c8');
    else showTestRes('❌ '+data.message,'#2a1a1a','#c88');
  }catch(e){
    showTestRes('❌ 网络错误: '+e.message,'#2a1a1a','#c88');
  }
}
function showTestRes(text,bg,color){
  var r=document.getElementById('sTestResult');
  r.style.display='block';r.style.background=bg;r.style.color=color;r.textContent=text;
}

// === 模式切换 (问答 / ADSR) ===
function switchMode(mode) {
  document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.remove('active')});
  document.querySelector('.mode-btn[data-mode="'+mode+'"]').classList.add('active');
  document.getElementById('chatMode').style.display = mode === 'chat' ? 'flex' : 'none';
  document.getElementById('adsrMode').style.display = mode === 'adsr' ? 'flex' : 'none';
}

// === Tab 切换 ===
function switchTab(name) {
  document.querySelectorAll('.sidebar-tab').forEach(function(t) { t.classList.remove('active'); });
  document.querySelector('.sidebar-tab[data-tab="'+name+'"]').classList.add('active');
  document.getElementById('refsPanel').style.display = name === 'refs' ? 'block' : 'none';
  document.getElementById('flowPanel').style.display = name === 'flow' ? 'block' : 'none';
}

// === UI 工具 ===
function escapeHtml(t){var d=document.createElement('div');d.textContent=t;return d.innerHTML}
function scrollBottom(){messages.scrollTop=messages.scrollHeight}

// === 消息 ===
function addMsg(type, html){
  var d=document.createElement('div');d.className='msg';
  if(type==='q') d.innerHTML='<div class="msg-q">🧑 你</div><div class="msg-q-text">'+escapeHtml(html)+'</div>';
  else d.innerHTML='<div class="msg-a">🎛️ 助手</div><div class="msg-a-text">'+html+'</div>';
  messages.appendChild(d);scrollBottom();
}

// === 流程日志 ===
function addLog(type,text,context){
  var panel=document.getElementById('flowPanel');
  var empty=panel.querySelector('.sidebar-empty');
  if(empty) empty.remove();
  var emoji={search:'🔍',found:'📄',llm:'🤖',done:'✅'};
  var div=document.createElement('div');
  div.className='log-entry log-'+type;
  var time=new Date().toLocaleTimeString();
  div.innerHTML='<div><span class="log-emoji">'+(emoji[type]||'')+'</span>'+escapeHtml(text)+' <span class="log-time">'+time+'</span></div>';
  if(context){
    div.innerHTML+='<span class="toggle-context" onclick="this.nextElementSibling.classList.toggle(\'show\')">📖 查看上下文</span><div class="log-context">'+escapeHtml(context)+'</div>';
  }
  panel.appendChild(div);panel.scrollTop=panel.scrollHeight;
}

// === 引用渲染 ===
function renderRefs(refs){
  var panel=document.getElementById('refsPanel');
  if(!refs||!refs.length){
    panel.innerHTML='<div style="color:#555;text-align:center;padding:40px 20px;font-size:13px">未找到相关片段</div>';return;
  }
  panel.innerHTML=refs.map(function(r,i){
    return '<div class="ref-card">'+
      '<div class="r-title">['+(i+1)+'] '+escapeHtml(r.title)+'</div>'+
      '<div class="r-source">'+escapeHtml(r.source)+' · 相关度 '+r.score+'</div>'+
      '<div class="r-snippet">'+escapeHtml(r.snippet)+'</div></div>';
  }).join('');
}

// === 主流程 ===
async function ask(){
  var q=input.value.trim();if(!q)return;
  addMsg('q',q);input.value='';sendBtn.disabled=true;

  // 清旧日志
  document.getElementById('flowPanel').innerHTML='';
  document.getElementById('refsPanel').innerHTML='<div style="color:#555;text-align:center;padding:40px 20px;font-size:13px">⏳ 搜索中…</div>';

  addLog('search','正在检索知识库 …');

  try{
    var res=await fetch('/api/search',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:q})
    });
    var data=await res.json();
    var refs=data.references||[];
    addLog('found','检索到 '+refs.length+' 个相关片段');
    renderRefs(refs);

    // 检查是否配了 Key (从服务端 .env 读取)
    addLog('llm','检查 LLM 配置 …');
    var cfgRes=await fetch('/api/env-config');
    var cfg=await cfgRes.json();
    if(cfg.api_key && cfg.api_key.startsWith('sk-')){
      addLog('llm','调用 LLM 生成回答 …');
      var llmRes=await fetch('/api/llm-answer',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({query:q,api_key:cfg.api_key,base_url:cfg.base_url,model:cfg.model})
      });
      var llmData=await llmRes.json();
      if(llmData.answer){
        addMsg('a',llmData.answer);
        addLog('done','回答生成完成');
        addLog('context','发送给 LLM 的上下文',llmData.context_snippet);
      } else {
        addMsg('a','⚠️ LLM 回答失败: '+(llmData.error||'未知错误'));
      }
    } else {
      addMsg('a','在知识库中找到 '+refs.length+' 个相关片段。\n💡 点击右上角 ⚙️ 设置 DeepSeek API Key (保存到 .env, 不会被 Git 提交)');
      if(refs.length===0) addMsg('a','可以换个问法试试。');
    }
  } catch(err){
    addLog('done','❌ 出错: '+err.message);
    addMsg('a','⚠️ 出错: '+err.message);
  }
  sendBtn.disabled=false;input.focus();
}

var input=document.getElementById('queryInput');
var sendBtn=document.getElementById('sendBtn');
var messages=document.getElementById('messages');
sendBtn.addEventListener('click',ask);
input.addEventListener('keydown',function(e){if(e.key==='Enter')ask();});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return INDEX_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/search", methods=["POST"])
def api_search():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "无法解析请求体"}), 400
        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({"error": "请输入问题"}), 400
        result = answer(query, top_k=5)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/llm-answer", methods=["POST"])
def api_llm_answer():
    """前端传 API Key 过来, 临时调 LLM"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "无法解析请求体"}), 400
        query = (data.get("query") or "").strip()
        api_key = (data.get("api_key") or "").strip()
        base_url = (data.get("base_url") or "https://api.deepseek.com").strip()
        model = (data.get("model") or "deepseek-chat").strip()

        if not api_key:
            return jsonify({"error": "请填写 API Key"}), 400

        # 搜索 → 拼上下文 → 调 LLM
        from app.indexer import query_index
        from app.retriever import format_context
        hits = query_index(query, top_k=5)
        context = format_context(hits)

        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的合成器知识助手。请基于提供的资料回答用户问题。用中文回答，标注引用来源编号如[1][2]。如果资料不足以回答就说'资料中没有相关信息'。"},
                {"role": "user", "content": f"资料:\n{context}\n\n问题: {query}"},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        answer_text = resp.choices[0].message.content

        return jsonify({
            "answer": answer_text,
            "context_snippet": context[:2000],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/test-key", methods=["POST"])
def api_test_key():
    """测试 API Key 是否可用"""
    try:
        data = request.get_json(force=True, silent=True)
        api_key = (data.get("api_key") or "").strip()
        base_url = (data.get("base_url") or "https://api.deepseek.com").strip()
        model = (data.get("model") or "deepseek-chat").strip()

        if not api_key:
            return jsonify({"ok": False, "message": "API Key 为空"})

        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=10)

        # 用极简请求测试连通性
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回复OK"}],
            max_tokens=5,
            temperature=0,
        )
        reply = resp.choices[0].message.content.strip()
        return jsonify({"ok": True, "message": f"连接成功！模型返回: {reply}"})

    except Exception as e:
        err = str(e)
        if "401" in err or "unauthorized" in err.lower() or "invalid" in err.lower():
            msg = "API Key 无效或权限不足"
        elif "timeout" in err.lower():
            msg = "连接超时，请检查 API 地址是否正确"
        elif "not found" in err.lower() or "model" in err.lower():
            msg = f"模型名 '{model}' 不存在或不可用"
        else:
            msg = f"连接失败: {err[:100]}"
        return jsonify({"ok": False, "message": msg})


@app.route("/api/save-env", methods=["POST"])
def api_save_env():
    """将 LLM 配置写入 .env 文件 (本地, 不会被 git 提交)"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"ok": False, "message": "请求体为空"})

        lines = []
        # 保留原有的非敏感配置
        old_lines = []
        if _ENV_FILE.exists():
            old_lines = _ENV_FILE.read_text(encoding="utf-8").splitlines()

        seen_keys = set()
        # 写入新配置
        new_config = {
            "LLM_API_KEY": data.get("api_key", "").strip(),
            "LLM_BASE_URL": data.get("base_url", "https://api.deepseek.com").strip(),
            "LLM_MODEL": data.get("model", "deepseek-chat").strip(),
        }
        for k, v in new_config.items():
            lines.append(f"{k}={v}")
            seen_keys.add(k)

        # 保留旧的配置行中不是 LLM 配置的内容
        for line in old_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key = line.split("=", 1)[0].strip()
            if key not in seen_keys:
                lines.append(line)
                seen_keys.add(key)

        _ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # 同步到当前进程环境变量
        for k, v in new_config.items():
            os.environ[k] = v

        return jsonify({"ok": True, "message": "已保存"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})


@app.route("/api/env-config", methods=["GET"])
def api_env_config():
    """返回当前的 LLM 配置 (不返回完整 Key, 只返回前几位用于显示)"""
    key = os.environ.get("LLM_API_KEY", "")
    return jsonify({
        "api_key": key,
        "api_key_preview": key[:8] + "…" + key[-4:] if len(key) > 12 else "",
        "base_url": os.environ.get("LLM_BASE_URL", "https://api.deepseek.com"),
        "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
        "configured": bool(key),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🎛️  合成器助手启动: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
