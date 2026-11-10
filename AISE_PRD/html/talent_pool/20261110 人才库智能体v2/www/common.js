/* 共享 JS：请求封装、顶栏渲染、登录守卫、雷达图 */
async function api(path, opts) {
  const r = await fetch(path, opts);
  let body = {};
  try { body = await r.json(); } catch (e) { body = {}; }
  if (r.status === 401 && !path.includes('/api/login')) {
    location.href = '/login.html';
    return body;
  }
  if (!r.ok) throw new Error(body.error || ('HTTP ' + r.status));
  return body;
}
function post(path, obj) {
  return api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj || {}) });
}

const ROLE_LABEL = { student: '学员 / 家长', teacher: '教研员' };
const NAVS = {
  student: [
    ['作品上传', '/s_home.html'], ['人才卡', '/s_card.html'],
    ['画像分析', '/s_report.html'], ['问答助手', '/s_qa.html'],
  ],
  teacher: [
    ['审核工作台', '/a_workbench.html'], ['人才库', '/a_library.html'], ['问答助手', '/a_qa.html'],
  ],
};

async function guard(role) {
  let me;
  try { me = await api('/api/me'); } catch (e) { location.href = '/login.html'; return null; }
  if (role && me.role !== role) {
    location.href = me.role === 'teacher' ? '/a_workbench.html' : '/s_home.html';
    return null;
  }
  renderTopbar(me);
  return me;
}

function renderTopbar(me) {
  const el = document.getElementById('topbar');
  if (!el) return;
  const page = location.pathname;
  const links = NAVS[me.role].map(([t, u]) =>
    '<a href="' + u + '" class="' + (page === u ? 'active' : '') + '">' + t + '</a>').join('');
  el.innerHTML =
    '<div class="brand"><img src="/aise-logo.png" alt=""><span>人工智能人才资源库</span></div>' +
    '<span class="role-badge">' + ROLE_LABEL[me.role] + '</span>' +
    '<nav>' + links + '</nav>' +
    '<span class="me">' + me.label + '</span>' +
    '<button class="logout" onclick="logout()">退出</button>';
}
async function logout() { await post('/api/logout'); location.href = '/login.html'; }

/* 雷达图（四维） */
function drawRadar(canvas, dims) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth, H = canvas.clientHeight;
  canvas.width = W * dpr; canvas.height = H * dpr;
  ctx.scale(dpr, dpr);
  const cx = W / 2, cy = H / 2 + 6, R = Math.min(W, H) / 2 - 34;
  const keys = Object.keys(dims), n = keys.length;
  const pt = (i, r) => {
    const ang = -Math.PI / 2 + i * 2 * Math.PI / n;
    return [cx + r * Math.cos(ang), cy + r * Math.sin(ang)];
  };
  ctx.clearRect(0, 0, W, H);
  // 网格
  for (let g = 1; g <= 4; g++) {
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const [x, y] = pt(i, R * g / 4);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = '#e2e6ee'; ctx.stroke();
  }
  for (let i = 0; i < n; i++) {
    const [x, y] = pt(i, R);
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(x, y);
    ctx.strokeStyle = '#e2e6ee'; ctx.stroke();
  }
  // 数据
  ctx.beginPath();
  keys.forEach((k, i) => {
    const [x, y] = pt(i, R * dims[k] / 100);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = 'rgba(0,65,200,.14)'; ctx.fill();
  ctx.strokeStyle = '#0041c8'; ctx.lineWidth = 2; ctx.stroke();
  keys.forEach((k, i) => {
    const [x, y] = pt(i, R * dims[k] / 100);
    ctx.beginPath(); ctx.arc(x, y, 3.5, 0, 7); ctx.fillStyle = '#0041c8'; ctx.fill();
  });
  // 标签
  ctx.font = '12px "PingFang SC", sans-serif'; ctx.fillStyle = '#4a5568';
  keys.forEach((k, i) => {
    const [x, y] = pt(i, R + 18);
    const text = k + ' ' + dims[k];
    const w = ctx.measureText(text).width;
    ctx.fillText(text, x - w / 2, y + 4);
  });
}

/* 通用状态徽标 */
function statusBadge(s) {
  const map = { approved: ['ok', '审核完成'], reviewing: ['warn', '审核中'], rejected: ['bad', '未通过'] };
  const [cls, txt] = map[s] || ['gray', s];
  return '<span class="badge ' + cls + '">' + txt + '</span>';
}
function aiStatusBadge(s) {
  const map = { done: ['blue', '预审完成'], processing: ['warn', '预审中'], failed: ['bad', '预审失败'], none: ['gray', '未预审'] };
  const [cls, txt] = map[s] || ['gray', s];
  return '<span class="badge ' + cls + '">' + txt + '</span>';
}
const TYPE_LABEL = { code: '代码', image: '图片', pdf: 'PDF' };
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
