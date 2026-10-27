/* Node tests for the optional frontend; no browser or live shipments needed. */
const assert=require("node:assert/strict");
const {test}=require("node:test");
const registered=new Map();
global.window={customCards:[]};
global.customElements={get:n=>registered.get(n),define:(n,x)=>registered.set(n,x)};
global.HTMLElement=class {
  constructor(){this.listeners={};}
  attachShadow(){
    const self=this;
    this.shadowRoot={
      innerHTML:"",
      querySelector(selector){
        if(selector==="details")return {open:false};
        return {addEventListener:(kind,callback)=>{self.listeners[selector+":"+kind]=callback}};
      }
    };
  }
  dispatchEvent(){}
};
global.document={createElement:n=>new (registered.get(n))()};
global.CustomEvent=class{constructor(name,opts){this.type=name;this.detail=opts.detail}};
require("../custom_components/blueexpress_tracking/frontend/blueexpress-tracking-card.js");
const C=registered.get("blueexpress-tracking-card");
const Editor=registered.get("blueexpress-tracking-card-editor");
const sensor={
  state:"En reparto",
  attributes:{carrier:"Blue Express",tracking_number:"12345678",
    friendly_name:"Ampolletas E14 Status",
    promise_date:"2026-10-29",fetched_at:"2026-10-27T14:00:00Z",
    source_url:"https://www.blue.cl/enviar/seguimiento?n_seguimiento=12345678",
    events:[{title:"En reparto",time:"2026-10-27T12:00:00-03:00",location:"Santiago"},
      {title:null,time:"2026-10-27T13:00:00-03:00",location:"Santiago"},
      {title:"Liberado por Aduanas",time:"2026-10-26T16:00:00-03:00",location:"Santiago"}]
  }
};
const hass={language:"es-CL",states:{"sensor.ampolletas_e14_status":sensor}};
test("card registration and automatic shipment stub",()=>{
  assert.equal(typeof C,"function");
  assert.deepEqual(C.getStubConfig(hass),{type:"custom:blueexpress-tracking-card",entity:"sensor.ampolletas_e14_status"});
  assert.equal(window.customCards.filter(x=>x.type==="blueexpress-tracking-card").length,1);
  assert.ok(C.getConfigElement() instanceof Editor);
});
test("compact card renders provider state, deadlines and named history",()=>{
  const c=new C();c.setConfig({entity:"sensor.ampolletas_e14_status"});c.hass=hass;
  const ui=c.shadowRoot.innerHTML;
  assert.match(ui,/Ampolletas E14/);
  assert.match(ui,/En reparto/);
  assert.match(ui,/29 de octubre/);
  assert.match(ui,/Liberado por Aduanas/);
  assert.match(ui,/Recorrido · 2/);
  assert.doesNotMatch(ui,/null/);
  assert.doesNotMatch(ui,/Evento sin descripci/);
  assert.match(ui,/var\(--card-background-color\)/);
  assert.match(ui,/https:\/\/www.blue.cl\/enviar\/seguimiento\?n_seguimiento=12345678/);
});
test("escapes hostile strings, rejects forged tracking site and flags stale source",()=>{
  const c=new C();c.setConfig({entity:"sensor.ampolletas_e14_status",title:'<img src=x onerror=alert(1)>'});
  c.hass={language:"es",states:{"sensor.ampolletas_e14_status":{
    state:"En reparto",attributes:{...sensor.attributes,
      stale:true,
      source_url:"https://evil.example/track?x=1",
      events:[{title:"<script>alert(1)</script>",time:"2026-10-27T12:00:00-03:00",location:"Santiago"}]
    }}}};
  const ui=c.shadowRoot.innerHTML;
  assert.doesNotMatch(ui,/<script>|<img src=x/);
  assert.match(ui,/&lt;script&gt;/);
  assert.match(ui,/&lt;img src=x/);
  assert.doesNotMatch(ui,/evil\.example/);
  assert.match(ui,/Datos anteriores/);
});
test("editor offers only actual Blue Express tracking sensors",()=>{
  const e=new Editor();e.setConfig({entity:"sensor.ampolletas_e14_status"});e.hass={...hass,states:{...hass.states,
    "sensor.unrelated":{state:"hi",attributes:{friendly_name:"Another sensor"}}}};
  const html=e.shadowRoot.innerHTML;
  assert.match(html,/sensor.ampolletas_e14_status/);
  assert.doesNotMatch(html,/sensor.unrelated/);
});
