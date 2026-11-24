const $ = id => document.getElementById(id);
const socket = io();
let packetHistory = [];
let trafficValues = Array(32).fill(0);
const colors = ["#56d5d0","#689cff","#f3a65a","#a58bff","#ed6d7a","#69bd89","#88a0b8"];
const fmt = n => Number(n || 0).toLocaleString("en-IN");

function drawDoughnut(data) {
  const canvas=$("protocolChart"), ctx=canvas.getContext("2d");
  const entries=Object.entries(data || {}).sort((a,b)=>b[1]-a[1]);
  const total=entries.reduce((sum,item)=>sum+item[1],0);
  ctx.clearRect(0,0,canvas.width,canvas.height);
  if(!total) {
    ctx.beginPath();ctx.arc(110,110,78,0,Math.PI*2);ctx.strokeStyle="#25374b";ctx.lineWidth=22;ctx.stroke();
    ctx.fillStyle="#8092a9";ctx.font="12px Segoe UI";ctx.textAlign="center";ctx.fillText("NO DATA",110,114);
    $("protocolLegend").innerHTML='<div class="empty">Waiting for packets…</div>';return;
  }
  let angle=-Math.PI/2;
  entries.forEach((item,i)=>{const next=angle+item[1]/total*Math.PI*2;ctx.beginPath();ctx.arc(110,110,78,angle,next);ctx.strokeStyle=colors[i%colors.length];ctx.lineWidth=23;ctx.stroke();angle=next;});
  ctx.fillStyle="#e8eff8";ctx.font="bold 22px Consolas";ctx.textAlign="center";ctx.fillText(fmt(total),110,107);
  ctx.fillStyle="#8293a8";ctx.font="10px Segoe UI";ctx.fillText("PACKETS",110,124);
  $("protocolLegend").innerHTML=entries.slice(0,7).map((item,i)=>'<div class="legend-row"><i class="legend-swatch" style="background:'+colors[i%colors.length]+'"></i>'+item[0]+'<strong>'+Math.round(item[1]/total*100)+'%</strong></div>').join("");
}

function drawTraffic() {
  const c=$("trafficChart"),ctx=c.getContext("2d"),w=c.width,h=c.height;
  ctx.clearRect(0,0,w,h);
  for(let i=0;i<4;i++){const y=15+i*(h-30)/3;ctx.strokeStyle="#26364a";ctx.beginPath();ctx.moveTo(30,y);ctx.lineTo(w-8,y);ctx.stroke();}
  const max=Math.max(5,...trafficValues);
  const pts=trafficValues.map((v,i)=>({x:30+i*(w-42)/(trafficValues.length-1),y:h-18-(v/max)*(h-42)}));
  ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle="#56d5d0";ctx.lineWidth=2;ctx.stroke();
  ctx.lineTo(pts[pts.length-1].x,h-18);ctx.lineTo(pts[0].x,h-18);ctx.closePath();ctx.fillStyle="rgba(86,213,208,.09)";ctx.fill();
}

function renderPackets() {
  const rows=packetHistory.slice(0,30);$("packetCount").textContent=rows.length+" shown";
  $("packetRows").innerHTML=rows.length?rows.map(p=>'<tr><td>'+p.time+'</td><td class="proto">'+p.protocol+'</td><td>'+p.source+'</td><td>'+p.destination+'</td><td class="port">'+(p.source_port??"—")+' → '+(p.destination_port??"—")+'</td><td>'+p.length+' B</td><td>'+p.flags+'</td></tr>').join(""):'<tr><td colspan="7" class="empty">No packets captured yet.</td></tr>';
}
function renderEndpoints(id,items) {
  $(id).innerHTML=items&&items.length?items.map(item=>'<div class="endpoint-row"><span>'+item[0]+'</span><span>'+fmt(item[1])+'</span></div>').join(""):'—';
}
function renderAlerts(items) {
  $("alertList").innerHTML=items&&items.length?items.map(a=>'<div class="alert-item '+a.severity+'"><span class="alert-time">'+a.time+'</span><div class="alert-title">'+a.title+'</div><div class="alert-detail">'+a.detail+'</div></div>').join(""):'<div class="empty">No heuristic alerts. This does not guarantee that the network is threat-free.</div>';
}
function updateStats(s) {
  $("totalPackets").textContent=fmt(s.total_packets);
  $("pps").innerHTML=(s.pps||0).toFixed(1)+' <em>pps</em>';
  $("kbps").innerHTML=(s.kbps||0).toFixed(2)+' <em>kbps</em>';
  $("alertCount").textContent=fmt(s.alerts_total);
  drawDoughnut(s.protocols||{});
  renderEndpoints("topSources",s.top_sources);
  renderEndpoints("topDestinations",s.top_destinations);
  renderAlerts(s.alerts);
  if(s.recent&&packetHistory.length===0){packetHistory=s.recent;renderPackets();}
  const up=s.uptime||0;
  $("uptime").textContent="UPTIME "+[Math.floor(up/3600),Math.floor(up%3600/60),up%60].map(v=>String(v).padStart(2,"0")).join(":");
}
function setStatus(running,message) {
  $("statusPill").textContent=running?"● CAPTURING":"● STOPPED";
  $("statusPill").className="pill "+(running?"running":"idle");
  $("startBtn").disabled=running;$("stopBtn").disabled=!running;$("interfaceSelect").disabled=running;
  $("notice").textContent=message||(running?"Live capture active. Only traffic visible to the selected adapter is shown.":"Capture stopped.");
}
async function loadInterfaces() {
  $("interfaceSelect").innerHTML='<option>Loading interfaces…</option>';
  try {
    const data=await fetch("/api/interfaces").then(r=>r.json());
    const list=data.interfaces||[];
    $("interfaceSelect").innerHTML=list.map(i=>'<option value="'+i.id.replace(/&/g,"&amp;").replace(/"/g,"&quot;")+'">'+i.name+' · '+i.ip+'</option>').join("")||'<option value="">No interfaces found</option>';
  } catch(error) {$("interfaceSelect").innerHTML='<option value="">Unable to load interfaces</option>';}
}
async function post(url,body) {
  const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})});
  const data=await response.json();if(!response.ok||!data.ok)throw new Error(data.message||"Request failed");return data;
}
$("refreshBtn").onclick=loadInterfaces;
$("startBtn").onclick=async()=>{try{const result=await post("/api/start",{interface:$("interfaceSelect").value});setStatus(true,result.message);}catch(error){$("notice").textContent=error.message;}};
$("stopBtn").onclick=async()=>{try{const result=await post("/api/stop");setStatus(false,result.message);}catch(error){$("notice").textContent=error.message;}};
socket.on("connect",()=>{$("notice").textContent="Dashboard connected. Choose an adapter and start capture.";});
socket.on("stats",updateStats);
socket.on("packet",packet=>{packetHistory.unshift(packet);if(packetHistory.length>120)packetHistory.pop();renderPackets();trafficValues.push(trafficValues[trafficValues.length-1]+1);if(trafficValues.length>32)trafficValues.shift();drawTraffic();});
socket.on("alert",alert=>{renderAlerts([alert].concat([]));});
socket.on("capture_status",status=>setStatus(!!status.running,status.message));
setInterval(()=>$("clock").textContent=new Date().toLocaleTimeString("en-GB"),1000);
loadInterfaces();drawDoughnut({});drawTraffic();
