/* Blue Express optional Lovelace card. All data comes from Home Assistant. */
const CARD_NAME="blueexpress-tracking-card";
const blueEntities=h=>Object.entries(h?.states||{}).filter(([id,x])=>id.startsWith("sensor.")&&x?.attributes?.carrier==="Blue Express"&&/^[0-9]{8,10}$/.test(String(x.attributes.tracking_number||"")));
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const txt=h=>(h?.language||"es").startsWith("es")?{choose:"Elige un envío Blue Express",title:"Título opcional",missing:"Agrega un paquete desde la integración Blue Express",date:"Fecha máxima de entrega",number:"Seguimiento",last:"Último movimiento",history:"Recorrido",empty:"Sin movimientos descritos",open:"Ver en Blue Express",stale:"Datos anteriores · consulta fallida",updated:"Actualizado"}:{choose:"Choose a Blue Express shipment",title:"Optional title",missing:"Add a shipment from Blue Express Tracking",date:"Carrier delivery deadline",number:"Tracking number",last:"Latest movement",history:"Timeline",empty:"No described events",open:"Open Blue Express",stale:"Cached information · refresh failed",updated:"Updated"};
const dateTime=(value,h)=>{const d=new Date(value);return value&&Number.isFinite(d.getTime())?new Intl.DateTimeFormat((h?.language||"es").startsWith("es")?"es-CL":"en-US",{timeZone:"America/Santiago",day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"}).format(d):""};
const promised=(v,h)=>{const m=/^([0-9]{4})-([0-9]{2})-([0-9]{2})$/.exec(String(v||""));if(!m)return "";const d=new Date(+m[1],+m[2]-1,+m[3],12);if(d.getFullYear()!==+m[1]||d.getMonth()!==+m[2]-1||d.getDate()!==+m[3])return "";return new Intl.DateTimeFormat((h?.language||"es").startsWith("es")?"es-CL":"en-US",{day:"numeric",month:"long",year:"numeric"}).format(d)};
const official=(v,n)=>{const fallback="https://www.blue.cl/enviar/seguimiento?n_seguimiento="+encodeURIComponent(n);try{const u=new URL(v);return u.protocol==="https:"&&u.hostname==="www.blue.cl"&&u.pathname==="/enviar/seguimiento"&&u.searchParams.get("n_seguimiento")===n?u.href:fallback}catch{return fallback}};
class BlueExpressCard extends HTMLElement{
 constructor(){super();this.attachShadow({mode:"open"});}
 static getStubConfig(h){const first=blueEntities(h)[0]?.[0];return {type:"custom:blueexpress-tracking-card",...(first?{entity:first}:{})};}
 static getConfigElement(){return document.createElement("blueexpress-tracking-card-editor")}
 setConfig(c){if(!c||typeof c!=="object")throw Error("Invalid config");this.config={...c};this.render();}
 set hass(h){this.h=h;this.render();}
 getCardSize(){return 3;}getGridOptions(){return {columns:6,rows:"auto"};}
 render(){
  if(!this.config)return;
  const h=this.h,t=txt(h),id=this.config.entity||blueEntities(h)[0]?.[0],x=h?.states?.[id],a=x?.attributes||{},valid=a.carrier==="Blue Express"&&/^[0-9]{8,10}$/.test(String(a.tracking_number||"")),num=String(a.tracking_number||"");
  const open=Boolean(this.shadowRoot.querySelector("details")?.open);
  const list=(Array.isArray(a.events)?a.events:[]).filter(e=>e&&typeof e.title==="string"&&e.title.trim()&&Number.isFinite(new Date(e.time).getTime())).sort((x,y)=>new Date(y.time)-new Date(x.time)).slice(0,70);
  const last=list[0],title=this.config.title||String(a.friendly_name||"Blue Express").replace(/ (Status|Estado)$/,"");
  this.shadowRoot.innerHTML=`<style>
  :host{display:block;min-width:0;color:var(--primary-text-color);font:inherit}*{box-sizing:border-box}
  ha-card{display:block;padding:16px;border:1px solid var(--divider-color);border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color))}
  header{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:13px}
  .brand{display:flex;gap:8px;align-items:center;min-width:0}.brand ha-icon{--mdc-icon-size:21px;color:var(--primary-color)}
  h2{font-size:16px;margin:0;line-height:1.3;overflow-wrap:anywhere}.badge{font-size:10px;padding:4px 8px;border:1px solid var(--divider-color);border-radius:30px;color:var(--secondary-text-color)}
  .status{font-size:20px;font-weight:700;margin:6px 0 13px;line-height:1.35}
  .fields{display:grid;grid-template-columns:1fr 1fr;gap:12px;border-block:1px solid var(--divider-color);padding:11px 0}
  .muted{font-size:11px;color:var(--secondary-text-color);line-height:1.5}.value{font-size:13px;font-weight:600;margin-top:4px;overflow-wrap:anywhere}
  .latest{display:flex;gap:9px;margin:14px 0 11px}.latest ha-icon{--mdc-icon-size:17px;color:var(--secondary-text-color)}.latest p{font-size:13px;margin:4px 0}.latest strong{font-size:12px}
  details{border-top:1px solid var(--divider-color)}summary{padding:11px 0 6px;cursor:pointer;font-size:12px;font-weight:600;list-style:none;display:flex;justify-content:space-between}
  summary:after{content:"+";font-size:17px;font-weight:400}details[open] summary:after{content:"−"}
  ol{margin:7px 0 8px 6px;padding:0 0 0 17px;border-left:1px solid var(--divider-color);list-style:none}
  li{position:relative;margin:0 0 13px;font-size:12px;line-height:1.5}li:before{content:"";width:6px;height:6px;position:absolute;left:-20px;top:6px;border-radius:50%;background:var(--primary-color)}
  footer{display:flex;gap:8px;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-top:9px;border-top:1px solid var(--divider-color);padding-top:12px}
  a{font-size:12px;color:var(--primary-color);text-decoration:underline}.warn{font-size:12px;color:var(--warning-color,#ad750a);margin-bottom:10px}
  @media(max-width:440px){ha-card{padding:14px}.status{font-size:18px}}:focus-visible{outline:2px solid var(--primary-color);outline-offset:2px}
  </style><ha-card>
  <header><div class="brand"><ha-icon icon="mdi:truck-fast-outline"></ha-icon><h2>${esc(title)}</h2></div><span class="badge">Blue Express</span></header>
  ${valid?`<div class="status">${esc(x.state==="unavailable"?t.empty:x.state)}</div>
    ${a.stale||x.state==="unavailable"?`<div class="warn">⚠ ${esc(t.stale)}</div>`:""}
    <div class="fields"><div><div class="muted">${esc(t.date)}</div><div class="value">${esc(promised(a.promise_date,h)||"—")}</div></div>
    <div><div class="muted">${esc(t.number)}</div><div class="value">${esc(num)}</div></div></div>
    <div class="latest"><ha-icon icon="mdi:map-marker-path"></ha-icon><div><strong>${esc(t.last)}</strong>
    <p>${esc(last?.title||t.empty)}</p><div class="muted">${esc(dateTime(last?.time,h))}${last?.location?" · "+esc(last.location):""}</div></div></div>
    <details ${open?"open":""}><summary>${esc(t.history)} · ${list.length}</summary><ol>
    ${list.map(e=>`<li>${esc(e.title)}<div class="muted">${esc(dateTime(e.time,h))}${e.location?" · "+esc(e.location):""}</div></li>`).join("")||`<li>${esc(t.empty)}</li>`}</ol></details>
    <footer><a href="${esc(official(a.source_url,num))}" target="_blank" rel="noopener noreferrer">${esc(t.open)} ↗</a>
    <span class="muted">${esc(t.updated)}: ${esc(dateTime(a.fetched_at,h)||"—")}</span></footer>
  `:`<div class="muted">${esc(t.missing)}</div>`}</ha-card>`;
 }
}
class BlueExpressEditor extends HTMLElement{
 constructor(){super();this.attachShadow({mode:"open"});}
 setConfig(c){this.config={...c};this.render();}
 set hass(h){this.h=h;this.render();}
 render(){
  if(!this.config)return;const t=txt(this.h);
  this.shadowRoot.innerHTML=`<style>:host{display:block;padding:8px;color:var(--primary-text-color)}label{font-size:13px;display:block;margin:10px 0 5px;font-weight:600}select,input{width:100%;min-height:40px;border:1px solid var(--divider-color);border-radius:7px;padding:8px;background:var(--card-background-color);color:var(--primary-text-color)}</style>
   <label for="be-entity">${esc(t.choose)}</label><select id="be-entity"><option value="">—</option>
   ${blueEntities(this.h).map(([id,x])=>`<option value="${esc(id)}" ${this.config.entity===id?"selected":""}>${esc(x.attributes.friendly_name||id)}</option>`).join("")}</select>
   <label for="be-title">${esc(t.title)}</label><input id="be-title" maxlength="80" value="${esc(this.config.title||"")}">`;
  const change=patch=>{this.config={...this.config,...patch};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:this.config},bubbles:true,composed:true}))};
  this.shadowRoot.querySelector("select").addEventListener("change",e=>change({entity:e.target.value}));
  this.shadowRoot.querySelector("input").addEventListener("change",e=>change({title:e.target.value.trim()}));
 }
}
if(!customElements.get("blueexpress-tracking-card"))customElements.define("blueexpress-tracking-card",BlueExpressCard);
if(!customElements.get("blueexpress-tracking-card-editor"))customElements.define("blueexpress-tracking-card-editor",BlueExpressEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type==="blueexpress-tracking-card"))window.customCards.push({type:"blueexpress-tracking-card",name:"Blue Express Tracking",preview:true,description:"Compact shipment tracking · Chile"});
