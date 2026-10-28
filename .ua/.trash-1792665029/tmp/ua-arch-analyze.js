const fs=require('fs');
try{
const inp=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const nodes=inp.fileNodes, imp=inp.importEdges||[], all=inp.allEdges||[];
const ids=new Set(nodes.map(n=>n.id)); const byId={}; nodes.forEach(n=>byId[n.id]=n);
const paths=nodes.map(n=>n.filePath||'');
let pre=paths[0].split('/').slice(0,-1);
for(const p of paths){const s=p.split('/').slice(0,-1);let i=0;while(i<pre.length&&i<s.length&&pre[i]===s[i])i++;pre=pre.slice(0,i);}
const prefix=pre.length?pre.join('/')+'/':'';
const grp=id=>{const p=(byId[id].filePath||'').slice(prefix.length).split('/');return p.length>1?p[0]:'root';};
const directoryGroups={},nodeTypeGroups={};
nodes.forEach(n=>{(directoryGroups[grp(n.id)]??=[]).push(n.id);(nodeTypeGroups[n.type]??=[]).push(n.id);});
const fanIn={},fanOut={};const ig={};const dens={};
for(const g in directoryGroups)dens[g]={internalEdges:0,totalEdges:0};
for(const e of imp){if(!ids.has(e.source)||!ids.has(e.target))continue;fanOut[e.source]=(fanOut[e.source]||0)+1;fanIn[e.target]=(fanIn[e.target]||0)+1;
 const a=grp(e.source),b=grp(e.target);if(a===b){dens[a].internalEdges++;dens[a].totalEdges++;}else{dens[a].totalEdges++;dens[b].totalEdges++;const k=a+'->'+b;ig[k]=(ig[k]||0)+1;}}
for(const g in dens)dens[g].density=dens[g].totalEdges?+(dens[g].internalEdges/dens[g].totalEdges).toFixed(2):0;
const interGroupImports=Object.entries(ig).map(([k,c])=>{const[f,t]=k.split('->');return{from:f,to:t,count:c}}).sort((a,b)=>b.count-a.count);
const cc={};for(const e of all){if(!byId[e.source]||!byId[e.target])continue;const k=byId[e.source].type+'|'+byId[e.target].type+'|'+e.type;cc[k]=(cc[k]||0)+1;}
const crossCategoryEdges=Object.entries(cc).map(([k,c])=>{const[a,b,t]=k.split('|');return{fromType:a,toType:b,edgeType:t,count:c}});
const pm={routes:'api',api:'api',controllers:'api',services:'service',core:'service',lib:'service',models:'data',db:'data',data:'data',components:'ui',views:'ui',pages:'ui',ui:'ui',web:'ui',utils:'utility',helpers:'utility',common:'utility',shared:'utility',tools:'utility',config:'config',settings:'config',tests:'test',test:'test',types:'types',schemas:'types',assets:'assets',static:'assets',public:'assets',docs:'documentation',documentation:'documentation',scripts:'infrastructure',bin:'entry'};
const patternMatches={};for(const g in directoryGroups)if(pm[g])patternMatches[g]=pm[g];
const infra=paths.filter(p=>/Dockerfile|docker-compose|\.tf$|\.github\/|Makefile|\.sh$/.test(p));
const deploymentTopology={hasDockerfile:paths.some(p=>/Dockerfile/.test(p)),hasCompose:paths.some(p=>/docker-compose/.test(p)),hasK8s:false,hasTerraform:paths.some(p=>/\.tf$/.test(p)),hasCI:paths.some(p=>/\.github\/workflows/.test(p)),infraFiles:infra};
const dataPipeline={schemaFiles:[...new Set(paths.filter(p=>/schema\.json$|\.sql$/.test(p)))],migrationFiles:paths.filter(p=>/migrations\//.test(p)),dataModelFiles:paths.filter(p=>/models\.py$|storage\.py$/.test(p)).filter((v,i,a)=>a.indexOf(v)===i),apiHandlerFiles:[...new Set(nodes.filter(n=>n.type==='endpoint').map(n=>n.filePath))]};
const withDocs=Object.keys(directoryGroups).filter(g=>directoryGroups[g].some(id=>/README\.md$/.test(byId[id].filePath)));
const tg=Object.keys(directoryGroups).length;
const docCoverage={groupsWithDocs:withDocs.length,totalGroups:tg,coverageRatio:+(withDocs.length/tg).toFixed(2),undocumentedGroups:Object.keys(directoryGroups).filter(g=>!withDocs.includes(g))};
const dependencyDirection=[];const seen=new Set();for(const {from,to,count} of interGroupImports){const k=[from,to].sort().join('|');if(seen.has(k))continue;seen.add(k);const rev=ig[to+'->'+from]||0;if(count>=rev)dependencyDirection.push({dependent:from,dependsOn:to});else dependencyDirection.push({dependent:to,dependsOn:from});}
const filesPerGroup={};for(const g in directoryGroups)filesPerGroup[g]=directoryGroups[g].length;
const nodeTypeCounts={};for(const t in nodeTypeGroups)nodeTypeCounts[t]=nodeTypeGroups[t].length;
fs.writeFileSync(process.argv[3],JSON.stringify({scriptCompleted:true,commonPrefix:prefix,directoryGroups,nodeTypeGroups,crossCategoryEdges,interGroupImports,intraGroupDensity:dens,patternMatches,deploymentTopology,dataPipeline,docCoverage,dependencyDirection,fileStats:{totalFileNodes:nodes.length,filesPerGroup,nodeTypeCounts},fileFanIn:fanIn,fileFanOut:fanOut},null,1));
}catch(e){console.error(e.stack);process.exit(1);}
