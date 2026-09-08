/* 考试管理看板数据层 v3：活动/考试/渠道关联（32 活动管理 + 33 活动详情 共用） */
const LS_KEY = 'aise_exam_board_v3';
const PAPER_LIST = ['PY-L1-2026春-A卷','PY-L2-2026春-A卷','图形化-L1-3月卷','图形化-L2-6月卷','C++-L1-基础卷','PY-L3-冲刺卷','图形化-L1-模拟卷','PY-L2-模拟卷'];
const CHANNEL_LIST = [
 {id:'QD001', name:'猿编程'},
 {id:'QD002', name:'核桃编程'},
 {id:'QD003', name:'编程猫'},
 {id:'QD004', name:'小码王'},
];
const GROUPS = { 'QD001':['3月批','6月批'], 'QD002':['2026春季'], 'QD003':[], 'QD004':['常规班'] };
const TAG_POOL = ['Python','图形化','C++','1级','2级','3级'];

function seedActivities(){
 return [
  {id:'ACT2603', name:'2026春季考级（3-4月）', start:'2026-03-01', end:'2026-04-30'},
  {id:'ACT2605', name:'2026年5月图形化专场', start:'2026-05-01', end:'2026-05-31'},
  {id:'ACT2606', name:'2026年6月考级', start:'2026-06-01', end:'2026-06-30'},
  {id:'ACT2609', name:'2026年9月常规考', start:'2026-09-01', end:'2026-09-30'},
  {id:'ACT2612', name:'2026年12月考级（筹备中）', start:'2026-12-01', end:'2026-12-31'},
 ];
}
function seedRows(){
 const mk = (o) => Object.assign({
   fee:300, showStart:'', showEnd:'', show:true, permanent:false, certDate:'首次查看', desc:'',
   pro:{cam:'强制开启',rec:'强制开启',phone:false,photo:'非强制开启',score:true,detail:true,read:true,wait:0,guide:'',pic:''},
   mock:{on:false,paper:'',start:'',end:'',limit:'',submitLimit:'',pro:null},
   status:'已创建', enrolled:0, tags:[]
 }, o, {_k:o.aid+'|'+o.cid});
 return [
  mk({actId:'ACT2603', aid:'HD2501', name:'Python一级·3月考期', cid:'QD001', group:'3月批', paper:'PY-L1-2026春-A卷', examStart:'2026-03-21 09:00', examEnd:'2026-03-21 11:00', duration:120, submitLimit:100, fee:300, showStart:'2026-01-10', enrolled:186, tags:['Python','1级'], desc:'面向零基础学员的 Python 等级认证', certDate:'首次查看'}),
  mk({actId:'ACT2603', aid:'HD2502', name:'图形化一级·3月考期', cid:'QD001', group:'3月批', paper:'图形化-L1-3月卷', examStart:'2026-03-21 14:00', examEnd:'2026-03-21 15:30', duration:90, submitLimit:80, fee:280, showStart:'2026-01-10', enrolled:132, tags:['图形化','1级']}),
  mk({actId:'ACT2606', aid:'HD2503', name:'Python二级·6月考期', cid:'QD001', group:'6月批', paper:'PY-L2-2026春-A卷', examStart:'2026-06-20 09:00', examEnd:'2026-06-20 11:30', duration:150, submitLimit:130, fee:320, showStart:'2026-04-01', enrolled:98, tags:['Python','2级'], mock:{on:true,paper:'PY-L2-模拟卷',start:'2026-06-06 09:00',end:'2026-06-08 18:00',limit:'2次',submitLimit:'',pro:null}}),
  mk({actId:'ACT2606', aid:'HD2504', name:'图形化二级·6月考期', cid:'QD001', group:'6月批', paper:'图形化-L2-6月卷', examStart:'2026-06-20 14:00', examEnd:'2026-06-20 15:30', duration:90, submitLimit:80, fee:300, showStart:'2026-04-01', status:'创建失败', failReason:'爱测评接口超时，创建考试失败', tags:['图形化','2级']}),
  mk({actId:'ACT2609', aid:'HD2505', name:'C++一级·常规', cid:'QD001', group:'默认', paper:'', examStart:'2026-09-19 09:00', examEnd:'2026-09-19 11:00', duration:120, submitLimit:100, fee:300, showStart:'2026-07-01', status:'未关联', tags:['C++','1级'], mock:{on:false,paper:'',start:'',end:'',limit:'',submitLimit:'',pro:null}, pro:{cam:'强制开启',rec:'强制开启',phone:true,photo:'非强制开启',score:true,detail:true,read:true,wait:0,guide:'',pic:''}}),
  mk({actId:'ACT2609', aid:'HD2506', name:'Python一级·常规场', cid:'QD002', group:'2026春季', paper:'PY-L1-2026春-A卷', examStart:'2026-09-26 09:00', examEnd:'2026-09-26 11:00', duration:120, submitLimit:100, fee:300, showStart:'2026-07-15', enrolled:145, tags:['Python','1级']}),
  mk({actId:'ACT2609', aid:'HD2506', name:'Python一级·常规场', cid:'QD003', group:'默认', paper:'PY-L1-2026春-A卷', examStart:'2026-09-26 09:00', examEnd:'2026-09-26 11:00', duration:120, submitLimit:100, fee:260, showStart:'2026-07-15', enrolled:87, tags:['Python','1级']}),
  mk({actId:'ACT2605', aid:'HD2507', name:'图形化一级·5月专场', cid:'QD003', group:'默认', paper:'图形化-L1-3月卷', examStart:'2026-05-16 09:00', examEnd:'2026-05-16 10:30', duration:90, submitLimit:80, fee:280, showStart:'2026-03-01', enrolled:76, tags:['图形化','1级']}),
  mk({actId:'ACT2612', aid:'HD2508', name:'Python二级·12月考期', cid:'QD004', group:'常规班', paper:'PY-L2-2026春-A卷', examStart:'2026-12-19 09:00', examEnd:'2026-12-19 11:30', duration:150, submitLimit:130, fee:320, showStart:'2026-10-01', enrolled:64, tags:['Python','2级'], mock:{on:true,paper:'PY-L2-模拟卷',start:'2026-12-05 09:00',end:'2026-12-07 18:00',limit:'无限次',submitLimit:'90',pro:{cam:'不开启',rec:'不开启',phone:false,photo:'不开启',score:true,detail:true,read:true,wait:0,guide:'',pic:''}}}),
  mk({actId:'ACT2612', aid:'HD2509', name:'Python三级·12月冲刺', cid:'QD004', group:'常规班', paper:'PY-L3-冲刺卷', examStart:'2026-12-20 09:00', examEnd:'2026-12-20 12:00', duration:180, submitLimit:150, fee:360, showStart:'2026-10-01', permanent:true, enrolled:12, status:'创建中', tags:['Python','3级'], certDate:'2026-12-31'}),
 ];
}
let acts = [], rows = [];
function loadData(){
 try{ const s = localStorage.getItem(LS_KEY);
  if(s){ const d = JSON.parse(s);
   if(Array.isArray(d.acts) && Array.isArray(d.rows) && d.acts.length && d.rows.length && d.rows[0]._k && d.rows[0].actId){ acts = d.acts; rows = d.rows; return; } }
 }catch(e){}
 acts = seedActivities(); rows = seedRows();
 try{ localStorage.setItem(LS_KEY, JSON.stringify({acts, rows})); }catch(e){}
}
function saveData(){ try{ localStorage.setItem(LS_KEY, JSON.stringify({acts, rows})); }catch(e){} }
function resetDemo(){ localStorage.removeItem(LS_KEY); location.reload(); }
function chName(cid){ const c = CHANNEL_LIST.find(x=>x.id===cid); return c ? c.name : cid; }
function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function actPhase(a){ const n = Date.now(); const s = Date.parse(a.start), e = Date.parse(a.end + 'T23:59:59'); if(n < s) return 'notstart'; if(n > e) return 'ended'; return 'ongoing'; }
function examPhase(r){ const n = Date.now(); const s = Date.parse(r.examStart.replace(' ','T')), e = Date.parse(r.examEnd.replace(' ','T')); if(n < s) return 'notstart'; if(n > e) return 'ended'; return 'ongoing'; }
function proBrief(p){ if(!p) return '—'; const parts = ['摄像头:'+p.cam, '录屏:'+(p.rec||'不开启')]; if(p.phone) parts.push('手机监考'); parts.push('检录照片:'+p.photo); if(!p.score) parts.push('成绩:关'); if(!p.detail) parts.push('分数:关'); if(!p.read) parts.push('读题:关'); if(p.wait>0) parts.push('候考:'+p.wait+'分'); return parts.join('，'); }
function mockBrief(m){ if(!m||!m.on) return '<span class="text-slate-300">未开启</span>'; const pro = m.pro ? '<span class="text-amber-600">监考:自定义</span>' : '<span class="text-slate-400">监考:同正式考</span>'; const sub = m.submitLimit ? ' · 交卷≤'+esc(m.submitLimit)+'分' : ''; return '<span class="text-emerald-600 font-medium">已开启</span> · '+esc(m.paper)+' · '+esc(m.limit||'')+sub+'<div class="mt-0.5">'+pro+'</div>'; }
function fmtExamTime(r){ const d1=r.examStart.slice(0,10), d2=r.examEnd.slice(0,10); if(d1===d2) return esc(d1)+' '+esc(r.examStart.slice(11))+'-'+esc(r.examEnd.slice(11)); return esc(r.examStart)+' 至 '+esc(r.examEnd); }
function fmtShowTime(r){ if(r.permanent) return esc(r.showStart||'—')+' 起 · 永久有效'; if(!r.showStart && !r.showEnd) return '未设置'; if(r.showStart && !r.showEnd) return esc(r.showStart)+' 起'; if(!r.showStart && r.showEnd) return esc(r.showEnd)+' 止'; return esc(r.showStart)+' ~ '+esc(r.showEnd); }
function fmtCert(r){ if(r.certDate==='首次查看'||!r.certDate) return '用户初次查看时间'; return '指定日期：'+r.certDate; }
function statusPill(s){ const map={'已创建':'bg-emerald-50 text-emerald-600','创建中':'bg-amber-50 text-amber-600','未关联':'bg-slate-100 text-slate-500','创建失败':'bg-red-50 text-red-600'}; return '<span class="pill '+map[s]+'">'+s+'</span>'; }
function lockSetOf(r){ const s = new Set(); if(examPhase(r) !== 'notstart') ['name','examStart','examEnd','duration','submitLimit','paper','pro','mock','tags','desc','certDate'].forEach(x=>s.add(x)); if(r.enrolled > 0){ s.add('examStart'); s.add('examEnd'); } return s; }
function toast(msg, type, box){ const t = document.createElement('div'); t.className = 'bg-white border shadow-popover px-4 py-2.5 rounded-lg text-sm flex items-center gap-2 ' + (type==='error'?'border-red-200 text-red-600':'border-slate-200 text-slate-700'); t.innerHTML = (type==='error'?'<i class="fa-solid fa-circle-exclamation text-red-500"></i>':'<i class="fa-solid fa-circle-check text-emerald-500"></i>') + esc(msg); (box||document.getElementById('toastBox')).appendChild(t); setTimeout(()=>t.remove(), 3200); }
function uniqueGroups(){ return [...new Set(rows.map(r=>r.group))].filter(g=>g!=='默认').concat(['默认']); }
