"use strict";

const $ = (id) => document.getElementById(id);
const canvas = $("map"), ctx = canvas.getContext("2d");
const names = {town_hall:"Town Hall",air_defense:"Air Defense",air_sweeper:"Air Sweeper",inferno:"Inferno Tower",eagle:"Eagle Artillery",scattershot:"Scattershot",xbow:"X-Bow",cannon:"Cannon",archer_tower:"Archer Tower",wizard_tower:"Wizard Tower",mortar:"Mortar",bomb_tower:"Bomb Tower",clan_castle:"Clan Castle",wall:"Wall",other:"Other defense",deployment:"Deployment area"};
let state = emptySession(), image = null, imageInfo = null, imageRect = null;
let result = null, selected = 0, drag = null, history = [], revision = 0, pending = null;
let dirty = false, loadGeneration = 0, saving = false;

function emptySession() {
  return {schema_version:1,mode:"friendly",town_hall:13,army_confirmed:false,scene_confirmed:false,center:null,army:[],annotations:[]};
}
function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
function message(text, error = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", error);
}
function controls() {
  $("preview-btn").disabled = !image || !!pending;
  $("cancel-btn").disabled = !pending;
  $("save-btn").disabled = !image || saving;
  $("undo-btn").disabled = !history.length;
  $("clear-btn").disabled = !state.annotations.length && !state.center;
  $("army-confirmed").checked = state.army_confirmed;
  $("scene-confirmed").checked = state.scene_confirmed;
}
function invalidate({army=false, map=false} = {}) {
  revision++;
  if (pending) pending.abort();
  pending = null;
  if (army) state.army_confirmed = false;
  if (map) state.scene_confirmed = false;
  result = null;
  dirty = true;
  renderPlans(); controls(); draw();
  message(image ? "Inputs changed. Confirm them, then preview fresh plans." : "Load a screenshot or try the demo to begin.");
}
function remember() {
  history.push(structuredClone({annotations:state.annotations,center:state.center}));
  if (history.length > 60) history.shift();
}
function tab(name) {
  for (const value of ["setup","plans"]) {
    $("panel-"+value).hidden = name !== value;
    $("tab-"+value).setAttribute("aria-selected", String(name === value));
    $("tab-"+value).tabIndex = name === value ? 0 : -1;
  }
}
function renderArmy() {
  $("army-list").replaceChildren();
  if (!state.army.length) $("army-list").append(node("p", "Add the actual army you selected, or use the demo to explore.", "microcopy"));
  state.army.forEach((unit) => {
    const card = node("div", undefined, "unit");
    const title = node("div", undefined, "unit-title");
    const name = document.createElement("input");
    name.value = unit.name; name.placeholder = "Troop, hero or spell"; name.maxLength = 80;
    name.setAttribute("aria-label", "Unit name");
    name.addEventListener("input", () => {unit.name = name.value; invalidate({army:true});});
    const remove = node("button", "×"); remove.setAttribute("aria-label", "Remove " + (unit.name || "unit"));
    remove.addEventListener("click", () => {state.army = state.army.filter(u => u.id !== unit.id); invalidate({army:true}); renderArmy();});
    title.append(name,remove);
    const options = node("div", undefined, "unit-options");
    for (const [key,label,values] of [["count","Qty"], ["level","Level"], ["role","Role",["main","funnel","cleanup","hero","spell"]], ["domain","Type",["air","ground","both"]]]) {
      const field = node("label", label);
      const input = document.createElement(values ? "select" : "input");
      if (values) values.forEach(v => {const option = node("option", v[0].toUpperCase()+v.slice(1)); option.value = v; input.append(option);});
      else {input.type="number"; input.min="1"; input.max=key === "count" ? "1000" : "200"; input.step="1";}
      input.value = unit[key]; input.setAttribute("aria-label", (unit.name || "Unit") + " " + label);
      input.addEventListener(values ? "change" : "input", () => {unit[key] = values ? input.value : input.valueAsNumber; invalidate({army:true});});
      field.append(input); options.append(field);
    }
    card.append(title,options); $("army-list").append(card);
  });
}
function renderAnnotations() {
  $("annotation-list").replaceChildren();
  if (!state.annotations.length) $("annotation-list").append(node("p", "No map marks yet. Choose a tool and drag on the image.", "microcopy"));
  state.annotations.forEach((mark) => {
    const row = node("div", undefined, "annotation-item");
    const text = node("span", names[mark.kind]);
    const remove = node("button", "×"); remove.setAttribute("aria-label", "Remove " + names[mark.kind]);
    remove.addEventListener("click", () => {remember(); state.annotations = state.annotations.filter(a => a.id !== mark.id); invalidate({map:true}); renderAnnotations();});
    row.append(text,remove); $("annotation-list").append(row);
  });
  $("mark-count").textContent = state.annotations.length + " marks";
  $("center-status").textContent = state.center ? "Center placed" : "Center not set";
  controls();
}
function renderPlans() {
  $("plan-list").replaceChildren(); $("plan-detail").replaceChildren();
  if (!result || result.status !== "preview") {
    $("plan-list").append(node("p", "Confirm your army and map, then preview candidate entry sketches.", "placeholder"));
    return;
  }
  result.candidates.forEach((plan,index) => {
    const card = node("button", undefined, "candidate" + (index === selected ? " selected" : ""));
    card.setAttribute("aria-pressed", String(index === selected));
    card.append(node("strong",plan.clock), node("b", "Cost " + plan.cost.toFixed(1)), node("span", (index === 0 ? "Lowest modeled exposure" : "Alternative entry") + " · not a win probability"));
    card.addEventListener("click", () => {selected=index; renderPlans(); draw();});
    $("plan-list").append(card);
  });
  const detail = $("plan-detail"), plan = result.candidates[selected];
  detail.append(node("h3", "Manual deployment sketch"));
  plan.steps.forEach((step,index) => {
    const row = node("div", undefined, "plan-step");
    row.append(node("strong", `${index+1}. ${step.count} × ${step.name}`), node("p", step.trigger + " Split across " + step.positions.length + " marked point(s)."));
    detail.append(row);
  });
  detail.append(node("h3", "Keep in reserve"));
  detail.append(node("p", plan.reserves.length ? plan.reserves.map(u => `${u.count} × ${u.name}`).join(", ") : "No reserve units recorded.", "microcopy"));
  const limits = node("ul", undefined, "plan-limit");
  result.unknowns.forEach(text => limits.append(node("li",text)));
  detail.append(limits);
}
function drawRect(rect, color, label) {
  const x=imageRect.x+rect.x*imageRect.w, y=imageRect.y+rect.y*imageRect.h;
  const w=rect.w*imageRect.w, h=rect.h*imageRect.h;
  ctx.fillStyle=color+"22"; ctx.fillRect(x,y,w,h);
  ctx.strokeStyle=color; ctx.lineWidth=2; ctx.strokeRect(x,y,w,h);
  if (label) {
    ctx.font="11px Segoe UI, sans-serif";
    const width=ctx.measureText(label).width+10, tx=Math.max(imageRect.x, Math.min(x,imageRect.x+imageRect.w-width));
    const ty=Math.max(imageRect.y,y-18);
    ctx.fillStyle=color; ctx.fillRect(tx,ty,width,18); ctx.fillStyle="#fff"; ctx.fillText(label,tx+5,ty+13);
  }
}
function draw() {
  const bounds = canvas.getBoundingClientRect(), ratio = window.devicePixelRatio || 1;
  canvas.width=Math.round(bounds.width*ratio); canvas.height=Math.round(bounds.height*ratio);
  ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,bounds.width,bounds.height);
  if (!image) {imageRect=null; return;}
  const scale=Math.min(bounds.width/image.width,bounds.height/image.height);
  imageRect={x:(bounds.width-image.width*scale)/2,y:(bounds.height-image.height*scale)/2,w:image.width*scale,h:image.height*scale};
  ctx.drawImage(image,imageRect.x,imageRect.y,imageRect.w,imageRect.h);
  state.annotations.forEach(a => drawRect(a,a.kind === "deployment" ? "#147d72" : "#45769c",names[a.kind]));
  if (state.center) {
    const x=imageRect.x+state.center.x*imageRect.w,y=imageRect.y+state.center.y*imageRect.h;
    ctx.strokeStyle="#fff"; ctx.lineWidth=4; ctx.beginPath();ctx.moveTo(x-9,y);ctx.lineTo(x+9,y);ctx.moveTo(x,y-9);ctx.lineTo(x,y+9);ctx.stroke();
    ctx.strokeStyle="#18364a";ctx.lineWidth=2;ctx.stroke();
  }
  if (result?.status === "preview") {
    const plan=result.candidates[selected], center=state.center;
    const x=imageRect.x+plan.entry.x*imageRect.w,y=imageRect.y+plan.entry.y*imageRect.h;
    ctx.strokeStyle="#f1a75c";ctx.lineWidth=3;ctx.setLineDash([6,5]);ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(imageRect.x+center.x*imageRect.w,imageRect.y+center.y*imageRect.h);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle="#d97732";ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.fill();ctx.strokeStyle="#fff";ctx.lineWidth=2;ctx.stroke();
    plan.steps.forEach(step => step.positions.forEach(p => {
      const px=imageRect.x+p.x*imageRect.w,py=imageRect.y+p.y*imageRect.h;
      ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(px,py,4,0,Math.PI*2);ctx.fill();ctx.strokeStyle="#d97732";ctx.lineWidth=2;ctx.stroke();
    }));
  }
  if (drag) drawRect(rectFromPoints(drag.start,drag.end),"#d97732",null);
}
function mapPoint(event, clamp=false) {
  if (!imageRect) return null;
  const bounds=canvas.getBoundingClientRect();
  let x=(event.clientX-bounds.left-imageRect.x)/imageRect.w, y=(event.clientY-bounds.top-imageRect.y)/imageRect.h;
  if (!clamp && (x<0 || x>1 || y<0 || y>1)) return null;
  return {x:Math.max(0,Math.min(1,x)),y:Math.max(0,Math.min(1,y))};
}
function rectFromPoints(a,b) {return {x:Math.min(a.x,b.x),y:Math.min(a.y,b.y),w:Math.abs(a.x-b.x),h:Math.abs(a.y-b.y)};}
canvas.addEventListener("pointerdown", event => {
  const p=mapPoint(event); if (!p || event.button !== 0) return;
  canvas.focus();
  if ($("draw-kind").value === "center") {remember();state.center=p;invalidate({map:true});renderAnnotations();return;}
  drag={start:p,end:p}; canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", event => {if (drag) {drag.end=mapPoint(event,true);draw();}});
canvas.addEventListener("pointerup", event => {
  if (!drag) return;
  const area=rectFromPoints(drag.start,mapPoint(event,true));drag=null;
  if (area.w >= .008 && area.h >= .008) {
    if (state.annotations.length >= 250) {message("Maximum 250 marks per session.",true);draw();return;}
    remember();state.annotations.push({id:crypto.randomUUID(),kind:$("draw-kind").value,...area});invalidate({map:true});renderAnnotations();
  } else {draw();message("Drag a larger rectangle to mark a building or area.");}
});
canvas.addEventListener("pointercancel", () => {drag=null;draw();});
canvas.addEventListener("keydown", event => {if (event.key === "Escape") {drag=null;draw();} if ((event.ctrlKey || event.metaKey) && event.key === "z") {event.preventDefault();undo();}});

function undo() {
  if (!history.length) return;
  const prev=history.pop();state.annotations=prev.annotations;state.center=prev.center;invalidate({map:true});renderAnnotations();
}
$("undo-btn").addEventListener("click",undo);
$("clear-btn").addEventListener("click",() => {if (!confirm("Clear the map marks? Your army will stay.")) return;remember();state.annotations=[];state.center=null;invalidate({map:true});renderAnnotations();});
$("add-unit").addEventListener("click",() => {if (state.army.length >= 60) {message("Maximum 60 army entries.",true);return;}state.army.push({id:crypto.randomUUID(),name:"",count:1,level:1,role:"main",domain:"ground"});invalidate({army:true});renderArmy();});
$("battle-mode").addEventListener("change",() => {state.mode=$("battle-mode").value;invalidate({army:true,map:true});});
$("town-hall").addEventListener("input",() => {state.town_hall=$("town-hall").valueAsNumber;invalidate({army:true});});
$("army-confirmed").addEventListener("change",() => {state.army_confirmed=$("army-confirmed").checked;invalidate();});
$("scene-confirmed").addEventListener("change",() => {state.scene_confirmed=$("scene-confirmed").checked;invalidate();});
for (const name of ["setup","plans"]) $("tab-"+name).addEventListener("click",()=>tab(name));
document.querySelector(".tabs").addEventListener("keydown",event=>{if (["ArrowLeft","ArrowRight"].includes(event.key)) {event.preventDefault();const next=$("panel-plans").hidden ? "plans" : "setup";tab(next);$("tab-"+next).focus();}});

async function callPlanner(payload, signal) {
  const response=await fetch("/api/plan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),signal});
  const data=await response.json(); if (!response.ok) throw new Error(data.error || "Cannot preview this session.");return data;
}
$("preview-btn").addEventListener("click",async() => {
  if (!image) return;
  const current=new AbortController(), version=revision;pending=current;controls();message("Checking your inputs and comparing entry sketches…");
  try {
    const data=await callPlanner(state,current.signal);
    if (revision !== version || pending !== current) return;
    result=data;selected=0;renderPlans();draw();
    if (data.status === "needs_input") {tab("setup");message(data.issues.join("\n"),true);}
    else {tab("plans");message(`${data.candidates.length} entry sketches · planner ${data.planning_ms.toFixed(1)} ms. This is not capture/model latency.`);}
  } catch (error) {if (error.name !== "AbortError") message(error.message + " Check that the local app is running.",true);}
  finally {if (pending === current) {pending=null;controls();}}
});
$("cancel-btn").addEventListener("click",()=>{if (pending) pending.abort();pending=null;revision++;controls();message("Preview cancelled. No game actions were sent.");});

function mayReplace() {return !dirty || confirm("Replace this session? Use Save session first if you want to keep your work.");}
function readDataURL(file) {return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error("Cannot read this file."));reader.readAsDataURL(file);});}
function decodeImage(data) {
  return new Promise((resolve,reject)=>{
    if (typeof data !== "string" || data.length > 15_000_000 || !/^data:image\/(png|jpeg|webp);base64,[a-zA-Z0-9+/=\r\n]+$/.test(data)) {reject(new Error("Use a PNG, JPG or WebP image smaller than 10 MB."));return;}
    const img=new Image();img.onload=()=>{if (img.width*img.height > 24_000_000 || !img.width || !img.height) reject(new Error("Use an image with at most 24 million pixels.")); else resolve(img);};img.onerror=()=>reject(new Error("This image could not be decoded."));img.src=data;
  });
}
function installSession(next,img,info) {
  invalidate();state=next;state.army_confirmed=false;state.scene_confirmed=false;
  image=img;imageInfo=info;history=[];drag=null;dirty=false;
  $("battle-mode").value=state.mode;$("town-hall").value=state.town_hall;
  $("image-title").textContent=info.demo ? "Synthetic practice layout" : info.name;
  $("image-detail").textContent=info.demo ? "Demo fixture, not an in-game screenshot. Review the marks and confirm the example army." : `${img.width} × ${img.height} · saved screenshot · mark the visible state manually`;
  $("mode-tag").textContent=info.demo ? "Synthetic demo" : "Saved screenshot";
  $("empty-state").hidden=true;renderArmy();renderAnnotations();renderPlans();tab("setup");controls();draw();
  message("Review the army and map, then check both confirmation boxes.");
}
function finishLoad(next,img,info,generation,version) {
  if (generation !== loadGeneration) return;
  if (version !== revision) {
    message("Load not applied: inputs changed while loading. Your edits were kept; choose the file again to replace them.",true);
    return;
  }
  installSession(next,img,info);
}
$("open-btn").addEventListener("click",()=>$("image-file").click());
$("import-btn").addEventListener("click",()=>$("session-file").click());
$("image-file").addEventListener("change",async event => {
  const file=event.target.files[0];event.target.value="";if (!file || !mayReplace()) return;
  const generation=++loadGeneration, version=revision;
  try {if (file.size > 10*1024*1024) throw new Error("Use an image smaller than 10 MB.");const data=await readDataURL(file),img=await decodeImage(data);finishLoad(emptySession(),img,{name:file.name,data_url:data,demo:false},generation,version);}
  catch(error) {message(error.message,true);}
});
$("session-file").addEventListener("change",async event => {
  const file=event.target.files[0];event.target.value="";if (!file || !mayReplace()) return;
  const generation=++loadGeneration, version=revision;
  try {
    if (file.size > 16*1024*1024) throw new Error("Session exceeds 16 MB.");
    const data=JSON.parse(await file.text());
    if (!data || !data.image || typeof data.image.name !== "string" || data.image.name.length > 255 || typeof data.image.demo !== "boolean") throw new Error("Not a Scouting Lab session. Choose a session exported by this app.");
    const info=data.image;delete data.image;
    if (JSON.stringify(data).length > 250_000) throw new Error("Session annotations are too large.");
    await callPlanner(data);
    const img=await decodeImage(info.data_url);
    finishLoad(data,img,info,generation,version);
  } catch(error) {message("Cannot load session: " + error.message,true);}
});
$("save-btn").addEventListener("click",async()=>{
  if (!imageInfo || saving) return;
  const payload=structuredClone(state), info=imageInfo, version=revision;
  saving=true;controls();
  try {
    await callPlanner(payload);
    if (version !== revision || info !== imageInfo) throw new Error("Inputs changed while saving. Review them and save again.");
    const blob=new Blob([JSON.stringify({...payload,image:info},null,2)],{type:"application/json"});
    const link=document.createElement("a"), url=URL.createObjectURL(blob);link.href=url;link.download="scouting-session.json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);dirty=false;message("Session exported with its image and annotations.");
  } catch(error) {message("Cannot save session: " + error.message,true);}
  finally {saving=false;controls();}
});

async function demo() {
  if (!mayReplace()) return;
  const generation=++loadGeneration, version=revision, sample=emptySession();sample.center={x:.5,y:.48};
  sample.army=[{id:"demo-edrag",name:"Electro Dragon",count:7,level:4,role:"main",domain:"air"},{id:"demo-balloon",name:"Balloon",count:6,level:9,role:"funnel",domain:"air"},{id:"demo-king",name:"Barbarian King",count:1,level:65,role:"hero",domain:"ground"},{id:"demo-rage",name:"Rage",count:3,level:6,role:"spell",domain:"both"}];
  sample.annotations=[{id:"demo-th",kind:"town_hall",x:.46,y:.42,w:.08,h:.10},{id:"demo-ad1",kind:"air_defense",x:.68,y:.32,w:.05,h:.07},{id:"demo-ad2",kind:"air_defense",x:.67,y:.60,w:.05,h:.07},{id:"demo-inf",kind:"inferno",x:.54,y:.28,w:.05,h:.07},{id:"demo-eagle",kind:"eagle",x:.44,y:.66,w:.06,h:.08},{id:"demo-cannon",kind:"cannon",x:.27,y:.45,w:.05,h:.06},{id:"demo-west",kind:"deployment",x:.07,y:.29,w:.08,h:.39},{id:"demo-east",kind:"deployment",x:.85,y:.29,w:.08,h:.39},{id:"demo-south",kind:"deployment",x:.3,y:.84,w:.4,h:.06}];
  const board=document.createElement("canvas");board.width=1000;board.height=750;const c=board.getContext("2d");
  c.fillStyle="#d7e3dd";c.fillRect(0,0,1000,750);c.fillStyle="#b7cec0";c.beginPath();c.moveTo(500,55);c.lineTo(875,360);c.lineTo(500,675);c.lineTo(125,360);c.closePath();c.fill();
  c.strokeStyle="#cadbd1";c.lineWidth=1;for(let i=-500;i<1200;i+=44){c.beginPath();c.moveTo(i,0);c.lineTo(i+900,750);c.stroke();c.beginPath();c.moveTo(i,750);c.lineTo(i+900,0);c.stroke();}
  c.strokeStyle="#839d90";c.lineWidth=12;c.strokeRect(360,240,290,295);c.strokeRect(235,310,125,140);c.strokeRect(650,310,120,140);
  sample.annotations.filter(a=>a.kind!=="deployment").forEach(a=>{const x=a.x*1000,y=a.y*750,w=a.w*1000,h=a.h*750;c.fillStyle=a.kind==="town_hall"?"#285b70":"#647f87";c.fillRect(x,y,w,h);c.fillStyle="#e8f1f3";c.fillRect(x+6,y+6,w-12,h-12);c.fillStyle="#294757";c.font="bold 11px Segoe UI";c.textAlign="center";c.fillText(a.kind==="town_hall"?"TH13":a.kind==="air_defense"?"AIR":a.kind.toUpperCase(),x+w/2,y+h/2+4);});
  c.textAlign="left";c.fillStyle="#49655a";c.font="18px Segoe UI";c.fillText("Synthetic layout · annotation demo",28,35);c.font="13px Segoe UI";c.fillText("Not a game screenshot or validated attack strategy",28,724);
  const data=board.toDataURL("image/png"),img=await decodeImage(data);finishLoad(sample,img,{name:"Synthetic practice layout",demo:true,data_url:data},generation,version);
}
$("demo-btn").addEventListener("click",()=>demo().catch(e=>message(e.message,true)));
$("empty-demo").addEventListener("click",()=>demo().catch(e=>message(e.message,true)));
window.addEventListener("beforeunload",event=>{if(dirty){event.preventDefault();event.returnValue="";}});
new ResizeObserver(draw).observe($("canvas-shell"));
renderArmy();renderAnnotations();renderPlans();tab("setup");controls();
