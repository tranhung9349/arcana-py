const fs=require('fs');const path=require('path');
try{
const inp=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const nodes=inp.nodes||[],edges=inp.edges||[],layers=inp.layers||[];
const ids=new Set(nodes.map(n=>n.id));const byId={};nodes.forEach(n=>byId[n.id]=n);
const fin={},fout={};nodes.forEach(n=>{fin[n.id]=new Set();fout[n.id]=new Set();});
// map function/class targets to their file via contains edges
const owner={};edges.forEach(e=>{if(e.type==='contains'&&ids.has(e.source))owner[e.target]=e.source;});
const res=x=>ids.has(x)?x:owner[x];
const fe=[];edges.forEach(e=>{const s=res(e.source),t=res(e.target);if(!s||!t||s===t)return;fe.push({s,t,type:e.type});fout[s].add(t);fin[t].add(s);});
const rank=(m,k)=>nodes.map(n=>({id:n.id,[k]:m[n.id].size,name:n.name})).sort((a,b)=>b[k]-a[k]).slice(0,20);
const fanInRanking=rank(fin,'fanIn'),fanOutRanking=rank(fout,'fanOut');
const outs=nodes.map(n=>fout[n.id].size).sort((a,b)=>a-b),ins=nodes.map(n=>fin[n.id].size).sort((a,b)=>a-b);
const p90=outs[Math.floor(outs.length*0.9)]||0,p25=ins[Math.floor(ins.length*0.25)]||0;
const ep=new Set(['index.ts','index.js','main.ts','main.js','app.ts','app.js','server.ts','server.js','mod.rs','main.go','main.py','main.rs','manage.py','app.py','wsgi.py','asgi.py','run.py','__main__.py','Application.java','Main.java','Program.cs','config.ru','index.php','App.swift','Application.kt','main.cpp','main.c']);
const cands=nodes.map(n=>{let s=0;const fp=n.filePath||'';const depth=fp.split('/').length-1;
 if(n.type==='document'){if(/^readme\.md$/i.test(fp))s+=5;else if(depth===0&&fp.endsWith('.md'))s+=2;}
 else if(n.type==='file'){if(ep.has(path.basename(fp)))s+=3;if(depth<=1)s+=1;if(fout[n.id].size>=p90&&p90>0)s+=1;if(fin[n.id].size<=p25)s+=1;}
 return {id:n.id,score:s,name:n.name,summary:n.summary,type:n.type};}).filter(c=>c.score>0).sort((a,b)=>b.score-a.score);
const entryPointCandidates=cands.slice(0,5);
const start=(cands.find(c=>c.type==='file')||{}).id;
const adj={};fe.forEach(e=>{if(e.type==='imports'||e.type==='calls'){(adj[e.s]=adj[e.s]||new Set()).add(e.t);}});
const order=[],depthMap={},byDepth={};
if(start){const q=[start];depthMap[start]=0;while(q.length){const c=q.shift();order.push(c);(byDepth[depthMap[c]]=byDepth[depthMap[c]]||[]).push(c);for(const t of (adj[c]||[]))if(!(t in depthMap)){depthMap[t]=depthMap[c]+1;q.push(t);}}}
const pick=n=>({id:n.id,name:n.name,type:n.type,summary:n.summary});
const nonCodeFiles={documentation:nodes.filter(n=>n.type==='document').map(pick),infrastructure:nodes.filter(n=>['service','pipeline','resource'].includes(n.type)).map(pick),data:nodes.filter(n=>['table','schema','endpoint'].includes(n.type)).map(pick),config:nodes.filter(n=>n.type==='config').map(pick)};
// clusters
const ek={};fe.forEach(e=>{if(e.type==='imports'||e.type==='calls'){ek[e.s+'|'+e.t]=1;}});
const und={};fe.forEach(e=>{(und[e.s]=und[e.s]||new Set()).add(e.t);(und[e.t]=und[e.t]||new Set()).add(e.s);});
const clusters=[];const used=new Set();
Object.keys(ek).forEach(k=>{const [a,b]=k.split('|');if(ek[b+'|'+a]&&a<b){const c=new Set([a,b]);for(const x of nodes.map(n=>n.id)){if(c.size>=5)break;if(c.has(x))continue;let cnt=0;c.forEach(m=>{if(und[x]&&und[x].has(m))cnt++;});if(cnt>=2)c.add(x);}
 const arr=[...c];let ec=0;fe.forEach(e=>{if(c.has(e.s)&&c.has(e.t))ec++;});clusters.push({nodes:arr,edgeCount:ec});}});
// fallback: dense groups by shared neighbors if no bidirectional
if(clusters.length<5){const pairs={};fe.forEach(e=>{const k=[e.s,e.t].sort().join('|');pairs[k]=(pairs[k]||0)+1;});
 Object.entries(pairs).sort((a,b)=>b[1]-a[1]).slice(0,30).forEach(([k,v])=>{const [a,b]=k.split('|');const c=new Set([a,b]);for(const x of nodes.map(n=>n.id)){if(c.size>=5)break;if(c.has(x))continue;let cnt=0;c.forEach(m=>{if(und[x]&&und[x].has(m))cnt++;});if(cnt>=2)c.add(x);}const arr=[...c];let ec=0;fe.forEach(e=>{if(c.has(e.s)&&c.has(e.t))ec++;});clusters.push({nodes:arr,edgeCount:ec,fallback:true});});}
clusters.sort((a,b)=>b.edgeCount-a.edgeCount);
const seen=new Set();const uc=clusters.filter(c=>{const k=[...c.nodes].sort().join(',');if(seen.has(k))return false;seen.add(k);return true;}).slice(0,10);
const nodeSummaryIndex={};nodes.forEach(n=>nodeSummaryIndex[n.id]={name:n.name,type:n.type,summary:n.summary});
fs.writeFileSync(process.argv[3],JSON.stringify({scriptCompleted:true,entryPointCandidates,fanInRanking,fanOutRanking,bfsTraversal:{startNode:start,order,depthMap,byDepth},nonCodeFiles,clusters:uc,layers:{count:layers.length,list:layers},nodeSummaryIndex,totalNodes:nodes.length,totalEdges:edges.length},null,1));
process.exit(0);}catch(err){console.error(err.stack);process.exit(1);}
