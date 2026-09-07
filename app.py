"""ForgeOps Industrial Agent Demo - pure Python standard library."""
from __future__ import annotations
import json, re, uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "mock_data.json").read_text(encoding="utf-8-sig"))

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def intent(text):
    if any(x in text for x in ["影响", "批次", "供应商", "追溯"]): return "批次影响追踪"
    if any(x in text for x in ["质量", "检验", "校准", "NCR", "不合格"]): return "质量异常调查"
    if any(x in text for x in ["报警", "告警", "维修", "设备", "停机"]): return "设备异常调查"
    if any(x in text.lower() for x in ["sop", "参数"]): return "知识库问答"
    return "生产异常综合调查"

def entities(text):
    pats = {"incident_id": r"(?:异常|事件|incident)[：:\s]*([A-Z]{2,}-?\d{3,})", "device_sn": r"(?:SN|sn|设备)[:：\s]*([A-Z]{2,}-?\d{3,})", "work_order": r"(?:工单|WO|wo)[:：\s]*([A-Z]{2,}-?\d{3,})", "material_lot": r"(?:批次|LOT|lot)[:：\s]*([A-Z]{2,}-?\d{3,})", "alarm_code": r"(?:报警|告警)[:：\s]*([A-Z]{1,5}-?\d{2,})"}
    out = {}
    for k, p in pats.items():
        m = re.search(p, text)
        if m: out[k] = m.group(1).upper()
    for k,v in {"device_sn":"DVT-24017","work_order":"WO-260901","material_lot":"LOT-AL-8842","alarm_code":"ALM-217","incident_id":"INC-260907-017"}.items(): out.setdefault(k,v)
    return out

def tool(name, title, summary, records, ms):
    return {"tool":name,"title":title,"status":"success","summary":summary,"records":records,"latency_ms":ms,"trace_id":"tr_"+uuid.uuid4().hex[:12]}

def investigate(question):
    inc=DATA["incident"]
    ts=[
      tool("MES.query_work_order","生产副 Agent · MES","找到装配工单及相关工序记录",[{"工单":inc["work_order"],"设备":inc["device_sn"],"工序":"真空调试","状态":"暂停","完成率":"68%"},{"工单":inc["work_order"],"物料批次":inc["material_lot"],"上线时间":"2026-09-07 08:42"}],186),
      tool("EAM.query_alarm_and_repair","设备副 Agent · EAM","定位报警、点检与最近维修记录",[{"报警码":inc["alarm_code"],"描述":"真空压力下降速率超限","首次发生":"2026-09-07 09:16","次数":3},{"设备":inc["device_sn"],"最近维修":"更换密封圈（2026-08-22）","建议":"检查腔体密封与压力传感器"}],241),
      tool("QMS.query_quality_records","质量副 Agent · QMS","发现校准记录与检验结果存在关联",[{"检验单":"IQC-260907-044","结果":"待复核","指标":"漏率","实测":"1.8e-3 Pa·m³/s","上限":"1.0e-3"},{"校准证书":"CAL-260601-008","有效期":"2026-09-01","当前日期":"2026-09-07","规则":"已过期"}],204),
      tool("WMS.query_material_impact","物料副 Agent · WMS","计算受影响批次与在制工单范围",[{"物料批次":inc["material_lot"],"供应商":"华东精密密封件（模拟）","关联工单":4,"在制设备":2},{"影响范围":"2 台设备 / 4 张工单 / 1 个待检批次","冻结建议":"待质量负责人确认"}],227)
    ]
    return {"trace_id":"trace_"+uuid.uuid4().hex[:12],"created_at":now(),"intent":intent(question),"entities":entities(question),"status":"待人工确认","confidence":0.94,"tools":ts,"rules":[{"name":"校准有效期","result":"拦截","detail":"校准证书已于 2026-09-01 过期"},{"name":"漏率参数","result":"超限","detail":"实测 1.8e-3，高于上限 1.0e-3"},{"name":"高风险写操作","result":"需人工确认","detail":"冻结批次 / 创建 NCR 仅生成草稿，不自动执行"}],"evidence":[{"source":"SOP-VAC-003 v2.1","location":"第 4.2 节 · 第 8 页","quote":"真空调试前应确认校准证书处于有效期内。"},{"source":"CAL-260601-008","location":"校准记录","quote":"有效期至 2026-09-01。"},{"source":"ALM-217 报警码表 v1.4","location":"第 3 页","quote":"压力下降速率超限时，检查密封与传感器，并暂停后续标定。"}],"graph":DATA["graph"],"recommendation":"暂停 WO-260901 的最终标定，复核真空腔体密封与压力传感器；对 LOT-AL-8842 生成冻结批次草稿，并创建 NCR 草稿，提交质量负责人审批。","approval":{"action":"冻结物料批次 + 创建 NCR","status":"draft","idempotency_key":"idem_"+uuid.uuid4().hex[:10]},"metrics":{"tool_success":"4/4","evidence_coverage":"92.5%","estimated_time_saved":"约 27 分钟"}}

HTML = """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>ForgeOps · Industrial Agent Demo</title><style>
:root{--bg:#07111f;--panel:#0d1b2e;--panel2:#10243b;--line:#203751;--text:#e8f0f7;--muted:#91a4b8;--cyan:#42d6d1;--amber:#ffc857;--red:#ff6b6b;--green:#75e3a0;--blue:#78a9ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 75% -10%,#143150 0,#07111f 45%);color:var(--text);font:14px/1.55 Arial,'Microsoft YaHei',sans-serif}.wrap{max-width:1440px;margin:auto;padding:28px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}.brand{font-size:23px;font-weight:800;letter-spacing:.5px}.brand span{color:var(--cyan)}.sub{color:var(--muted);margin-top:4px}.badge{border:1px solid #28627a;color:var(--cyan);padding:6px 10px;border-radius:999px;font-size:12px}.grid{display:grid;grid-template-columns:360px 1fr;gap:18px}.panel{background:rgba(13,27,46,.92);border:1px solid var(--line);border-radius:14px;box-shadow:0 14px 36px #02081455}.pad{padding:18px}.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:1.1px}.prompt{min-height:130px;width:100%;resize:vertical;background:#091727;border:1px solid #29445f;color:var(--text);border-radius:10px;padding:12px;margin-top:9px;font:14px/1.6 Arial,'Microsoft YaHei',sans-serif}.btn{cursor:pointer;background:linear-gradient(135deg,#27bdbb,#438de2);border:0;border-radius:9px;color:#06111d;padding:11px 15px;font-weight:800;margin-top:12px;width:100%}.quick{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}.quick button{background:#132a43;border:1px solid #2b4964;color:#b9d5ea;border-radius:7px;padding:7px 9px;cursor:pointer;font-size:12px}.note{color:var(--muted);font-size:12px;margin-top:16px}.main{min-width:0}.hero{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.hero h1{font-size:22px;margin:0 0 3px}.status{color:var(--amber);font-size:13px}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:17px 0}.kpi{background:#0b192b;border:1px solid var(--line);border-radius:10px;padding:12px}.kpi b{font-size:20px}.kpi small{display:block;color:var(--muted);margin-top:2px}.section{margin-top:14px}.section h2{font-size:15px;margin:0 0 10px}.tools{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.tool{background:#0a1829;border:1px solid #1f3853;border-radius:10px;padding:12px}.toolhead{display:flex;justify-content:space-between;gap:8px}.ok{color:var(--green)}.muted{color:var(--muted)}.tool p{color:#b7c9d8;margin:6px 0 9px}.kv{display:grid;grid-template-columns:repeat(2,1fr);gap:5px}.kv div{background:#10243a;border-radius:6px;padding:6px 7px;color:#cbe0ee;font-size:12px}.kv span{color:var(--muted);display:block;font-size:11px}.rules{display:grid;gap:7px}.rule{display:flex;align-items:center;gap:9px;background:#0a1829;padding:9px 11px;border-radius:8px;border-left:3px solid var(--red)}.rule.warn{border-left-color:var(--amber)}.rule b{min-width:112px}.evidence{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.ev{border:1px solid #29445f;border-radius:8px;padding:10px;background:#0a1829}.ev b{color:var(--cyan);font-size:12px}.ev small{display:block;color:var(--muted);margin:3px 0 7px}.graph{display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:#0a1829;border-radius:10px;padding:14px}.node{border:1px solid #32627c;background:#102a40;color:#cceaf0;border-radius:8px;padding:8px 10px}.arrow{color:var(--amber)}.recommend{border:1px solid #69582d;background:#211c10;border-radius:10px;padding:13px;color:#f9df99}.approve{margin-top:9px;display:flex;justify-content:space-between;align-items:center;gap:10px}.approve button{background:#263c58;color:#e8f0f7;border:1px solid #4a6c91;padding:8px 11px;border-radius:7px;cursor:pointer}.footer{color:#667d93;font-size:11px;margin-top:18px}@media(max-width:900px){.grid{grid-template-columns:1fr}.tools,.evidence{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class='wrap'><div class='top'><div><div class='brand'>ForgeOps <span>/ Industrial Agent</span></div><div class='sub'>脱敏模拟 Demo · 一主三副多 Agent · GraphRAG · HITL</div></div><div class='badge'>READ-ONLY SIMULATION</div></div><div class='grid'><aside class='panel pad'><div class='label'>输入异常问题</div><textarea id='q' class='prompt'>设备 SN:DVT-24017 在真空调试时触发 ALM-217，请分析根因、影响范围和处置建议。</textarea><button class='btn' onclick='run()'>运行生产异常分析</button><div class='quick'><button onclick='fill(0)'>真空异常</button><button onclick='fill(1)'>批次影响</button><button onclick='fill(2)'>质量复核</button></div><div class='note'>这是可公开展示的合成数据。Demo 用规则化模拟工具替代真实 MES / QMS / EAM / WMS 接口，不上传企业数据。</div><div class='section'><div class='label'>面试讲解路径</div><p class='muted'>1. 意图与实体抽取<br>2. 四个领域副 Agent 并行只读查询<br>3. 规则引擎拦截越界与过期数据<br>4. 图谱路径 + 文档证据合并<br>5. 高风险动作生成审批草稿</p></div></aside><main class='panel pad main' id='out'></main></div><div class='footer'>ForgeOps demo · Python standard library · no proprietary data · traceable evidence · human approval required for write actions</div></div><script>
var qs=['设备 SN:DVT-24017 在真空调试时触发 ALM-217，请分析根因、影响范围和处置建议。','LOT-AL-8842 关联了哪些设备、工单和检验记录？请给出影响范围。','校准证书已过期且漏率超限，是否可以继续最终标定？'];function fill(i){document.getElementById('q').value=qs[i]}
function esc(s){return String(s).replace(/[&<>\"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]})}
function render(d){var h='<div class="hero"><div><h1>'+esc(d.intent)+'</h1><div class="status">● '+esc(d.status)+' · 置信度 '+Math.round(d.confidence*100)+'%</div></div><div class="muted">'+esc(d.trace_id)+'<br>'+esc(d.created_at)+'</div></div><div class="kpis"><div class="kpi"><b>'+d.metrics.tool_success+'</b><small>只读工具成功</small></div><div class="kpi"><b>'+d.metrics.evidence_coverage+'</b><small>证据完整率</small></div><div class="kpi"><b>'+d.metrics.estimated_time_saved+'</b><small>预计节省时间</small></div><div class="kpi"><b>0</b><small>自动写操作</small></div></div><div class="section"><h2>实体与任务状态</h2><div class="graph">'+Object.keys(d.entities).map(function(k){return '<div class="node"><span class="muted">'+esc(k)+'</span><br>'+esc(d.entities[k])+'</div>'}).join('<span class="arrow">·</span>')+'</div></div><div class="section"><h2>多 Agent 并行查询</h2><div class="tools">'+d.tools.map(function(t){return '<div class="tool"><div class="toolhead"><b>'+esc(t.title)+'</b><span class="ok">✓ '+t.latency_ms+'ms</span></div><p>'+esc(t.summary)+'</p><div class="kv">'+t.records[0] ? '' : ''+'</div>'+t.records.map(function(r){return '<div class="kv">'+Object.keys(r).map(function(k){return '<div><span>'+esc(k)+'</span>'+esc(r[k])+'</div>'}).join('')+'</div>'}).join('')+'</div>'}).join('')+'</div></div><div class="section"><h2>规则校验与安全边界</h2><div class="rules">'+d.rules.map(function(r){return '<div class="rule '+(r.result==='需人工确认'?'warn':'')+'"><b>'+esc(r.result)+'</b><span><strong>'+esc(r.name)+'</strong> · '+esc(r.detail)+'</span></div>'}).join('')+'</div></div><div class="section"><h2>GraphRAG 证据路径</h2><div class="graph">'+d.graph.map(function(n,i){return '<div class="node">'+esc(n)+'</div>'+(i<d.graph.length-1?'<span class="arrow">→</span>':'')}).join('')+'</div></div><div class="section"><h2>可追溯引用</h2><div class="evidence">'+d.evidence.map(function(e){return '<div class="ev"><b>'+esc(e.source)+'</b><small>'+esc(e.location)+'</small><div>'+esc(e.quote)+'</div></div>'}).join('')+'</div></div><div class="section"><h2>处置建议 / HITL</h2><div class="recommend">'+esc(d.recommendation)+'</div><div class="approve"><span class="muted">草稿：'+esc(d.approval.action)+' · 幂等键 '+esc(d.approval.idempotency_key)+'</span><button onclick="alert(\'Demo：已记录人工确认事件，未调用真实写接口。\')">模拟人工确认</button></div></div>';
 document.getElementById('out').innerHTML=h}
function run(){document.getElementById('out').innerHTML='<div class="muted">正在执行意图识别、并行工具查询和证据合并…</div>';fetch('/api/investigate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.getElementById('q').value})}).then(function(r){return r.json()}).then(render)}
run();
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, body, code=200, content_type="text/html; charset=utf-8"):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if urlparse(self.path).path == "/": self._send(HTML)
        elif urlparse(self.path).path == "/health": self._send(json.dumps({"status":"ok","demo":True}), content_type="application/json")
        else: self._send("Not found", 404)
    def do_POST(self):
        if urlparse(self.path).path != "/api/investigate": self._send("Not found", 404); return
        n=int(self.headers.get("Content-Length",0)); body=json.loads(self.rfile.read(n) or b"{}")
        self._send(json.dumps(investigate(body.get("question", "")), ensure_ascii=False), content_type="application/json")
    def log_message(self, fmt, *args): print("[%s] %s" % (now(), fmt % args))

if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    print("ForgeOps demo running at http://%s:%s" % (host, port))
    ThreadingHTTPServer((host, port), Handler).serve_forever()

