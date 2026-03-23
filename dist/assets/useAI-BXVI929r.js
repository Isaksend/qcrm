import{B as d,C as h}from"./index-By51Jqdw.js";function f(e){return new Promise(t=>setTimeout(t,e))}async function m(e,t){await f(1e3+Math.random()*1e3);const s=d[t];return s||{id:`ai-${e}-${t}`,entityType:e,entityId:t,category:"analysis",title:`Analysis for ${e} ${t}`,content:"No specific analysis available for this entity yet. Continue tracking engagement metrics and activity patterns to generate actionable insights.",confidence:50,suggestions:["Increase engagement touchpoints","Gather more data for accurate analysis","Check back after more interactions"]}}async function p(e,t,n){var o,r,c,g,l;const s=y(e,t),a=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${n}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts:[{text:s}]}]})});if(!a.ok)throw new Error(`Gemini API error: ${a.status}`);const u=((l=(g=(c=(r=(o=(await a.json()).candidates)==null?void 0:o[0])==null?void 0:r.content)==null?void 0:c.parts)==null?void 0:g[0])==null?void 0:l.text)??"No response generated.";return A(e,t,u)}function y(e,t){const n=JSON.stringify(t,null,2);return`You are a CRM AI assistant. Analyze this ${e} data and provide actionable sales insights.

Data:
${n}

Respond in this exact JSON format:
{
  "title": "Brief insight title",
  "category": "risk|opportunity|coaching|prediction|analysis",
  "content": "2-3 sentence analysis with specific, actionable insights",
  "confidence": 75,
  "suggestions": ["Action item 1", "Action item 2", "Action item 3"]
}`}function A(e,t,n){try{const s=n.match(/\{[\s\S]*\}/);if(s){const a=JSON.parse(s[0]);return{id:`ai-live-${Date.now()}`,entityType:e,entityId:t.id??null,category:a.category??"analysis",title:a.title??"AI Analysis",content:a.content??n,confidence:a.confidence??70,suggestions:a.suggestions??[]}}}catch{}return{id:`ai-live-${Date.now()}`,entityType:e,entityId:t.id??null,category:"analysis",title:"AI Analysis",content:n,confidence:70,suggestions:[]}}function k(){const e=h();async function t(n,s,a){e.openPanel(n,s);try{let i;if(e.mode==="demo")i=await m(n,s);else{if(!e.apiKey){e.showSettingsModal=!0,e.closePanel();return}i=await p(n,a??{id:s},e.apiKey)}e.setPanelInsight(i)}catch(i){e.setPanelInsight({id:`ai-error-${Date.now()}`,entityType:n,entityId:s,category:"analysis",title:"Analysis Error",content:`Failed to generate insight: ${i instanceof Error?i.message:"Unknown error"}. Please try again or switch to demo mode.`,confidence:0,suggestions:["Check your API key","Try demo mode","Retry analysis"]})}}return{analyze:t}}export{k as u};
