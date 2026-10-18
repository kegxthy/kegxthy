import{financial,parseIntent,searchCatalog,tagProduct,skillMarkdown}from"./core.mjs";
const $=s=>document.querySelector(s),panel=$("#panel");let tab=new URLSearchParams(location.search).get("project")||"finance",last=null,image=null,processed=false;
if(location.hostname==="kegxthy.github.io")$("#backend").value="https://kegxthygent-lab-wzhcchgpbj.cn-hangzhou.fcapp.run";
const samples={finance:"revenue=12000\nnet_profit=800\noperating_cash_flow=-200\naccounts_receivable=4500\ncurrent_assets=3000\ncurrent_liabilities=4000\ntotal_assets=15000\ntotal_liabilities=11000",search:"500元以内，通勤用的降噪耳机",tags:JSON.stringify({name:"基础棉质短袖",category:"服装",material:"棉",color:"白"},null,2),skill:"虚构商城的商品管理页面。顶部有商品名称、类目和状态筛选；中间有商品列表，列为名称、价格、库存和状态；支持重置、分页和批量下架。权限、下架前置条件与审批流程待确认。"};
if(!["finance","image","search","tags","skill"].includes(tab))tab="finance";
const descriptions={finance:["财务风险 Agent","明确字段 → 确定性计算 → 规则筛查 → 可选模型解释 → 人工复核","输入统一币种和单位的 key=value 字段，或上传 UTF-8 TXT / CSV。此模块不自动解析 PDF。"],search:["AI 商品搜索","需求 → 意图解析 → 库存与硬条件校验 → 目录检索 → 结果解释","在 6 个合成商品中检索。浏览器模式使用规则解析；开启模型后由 DeepSeek 解析意图，再由工具执行检索。"],tags:["商品标签审核","显式字段 → 受控词表校验 → 拒绝原因 → 人工确认 → 导出","输入商品 JSON。仅从 category、material、color 明确字段生成候选标签；不从名称推断材质或营销功效。"],skill:["产品设计 Skills","脱敏页面证据 → 观察与假设分离 → Skill 草案 → 人工确认 → 导出","文字事实可以直接生成 Skill。截图可本地预览；开启模型并配置视觉模型后，才会发送截图进行识别。"]};
function download(name,data,type="application/json"){const blob=new Blob([typeof data==="string"?data:JSON.stringify(data,null,2)],{type});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function jsonView(value,target){const pre=document.createElement("pre");pre.textContent=typeof value==="string"?value:JSON.stringify(value,null,2);target.append(pre)}
function showError(message){$("#output").replaceChildren();const p=document.createElement("p");p.className="error";p.textContent=message;$("#output").append(p)}
function backend(){const base=$("#backend").value.trim().replace(/\/$/,"");if(base){const url=new URL(base);if(url.protocol!=="https:"&&!["localhost","127.0.0.1"].includes(url.hostname))throw Error("远程后端必须使用 HTTPS");return base}return location.origin}
async function execute(kind,data,local){
 if(!$("#llm").checked)return{mode:"浏览器确定性工具",result:local()};
 if(!$("#access").value)throw Error("请在模型连接设置中填写演示访问口令");
 const res=await fetch(backend()+"/api/"+kind,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+$("#access").value},body:JSON.stringify({...data,use_llm:true}),signal:AbortSignal.timeout(90000)});
 let result;try{result=await res.json()}catch{throw Error("后端未返回 JSON。请检查地址，GitHub Pages 本身不能执行后端。")}if(!res.ok)throw Error(result.error||"请求失败");return result;
}
function render(){
 last=null;image=null;processed=false;
 if(tab==="image"){renderImage();return}
 const [title,flow,hint]=descriptions[tab];
 panel.innerHTML='<h2>'+title+'</h2><div class="track">'+flow+'</div><p class="hint">'+hint+'</p><label for="input">输入内容</label><textarea id="input" spellcheck="false"></textarea><div id="upload-area"></div><div class="row"><button class="primary" id="run">运行工作流</button><button id="sample">恢复示例</button><button id="export" disabled>导出结果</button></div><div id="output" class="result" aria-live="polite"></div>';
 $("#input").value=samples[tab];$("#sample").onclick=()=>{$("#input").value=samples[tab]};
 if(tab==="finance"){const file=document.createElement("input");file.type="file";file.accept=".txt,.csv";file.setAttribute("aria-label","上传结构化财务文本");file.onchange=async()=>{try{const f=file.files[0];if(!f)return;if(f.size>100000)throw Error("财务文本限 100 KB");$("#input").value=await f.text()}catch(e){showError(e.message)}};$("#upload-area").append(file)}
 if(tab==="skill"){$("#upload-area").innerHTML='<label for="shot">已脱敏截图（可选，PNG/JPEG/WebP，最多 800 KB）</label><input type="file" id="shot" accept="image/png,image/jpeg,image/webp"><p class="hint">请先替换真实平台名、人员、订单、金额及内部规则。仅打码部分字段不一定充分。</p><img id="shot-preview" alt="所选脱敏截图预览" style="max-width:100%;max-height:220px" hidden>';$("#shot").onchange=async()=>{try{const f=$("#shot").files[0];if(!f)return;image=null;if(f.size>800000)throw Error("截图限 800 KB");if(!["image/png","image/jpeg","image/webp"].includes(f.type))throw Error("不支持的截图格式");image=await dataURL(f);$("#shot-preview").src=image;$("#shot-preview").hidden=false}catch(e){showError(e.message)}}}
 $("#export").onclick=()=>{if(!last)return;download(tab==="skill"?"SKILL.md":tab+"-result.json",tab==="skill"?last.result.markdown:last,tab==="skill"?"text/markdown":"application/json")};
 $("#run").onclick=async()=>{
  const activeTab=tab,button=$("#run");button.disabled=true;button.textContent="处理中…";$("#output").replaceChildren();
  try{
   const text=$("#input").value;if(text.length>12000)throw Error("输入最多 12000 字符");
   let response;
   if(tab==="finance")response=await execute(tab,{text},()=>financial(text));
   if(tab==="search")response=await execute(tab,{text},()=>{if(!text.trim())throw Error("请输入搜索需求");return searchCatalog(parseIntent(text))});
   if(tab==="tags"){let product;try{product=JSON.parse(text)}catch{throw Error("商品 JSON 格式不正确")}response=await execute(tab,{product},()=>tagProduct(product))}
   if(tab==="skill"){if(!text.trim())throw Error("请先描述页面事实");response=await execute(tab,{text,...(image?{image}:{})},()=>({markdown:skillMarkdown(text),screenshot_processed:false,review_required:true}))}
   if(tab!==activeTab)return;last=response;const target=$("#output");const badge=document.createElement("p");badge.className="hint";badge.textContent="执行模式："+response.mode;target.append(badge);
   if(tab==="search"){
    const grid=document.createElement("div");grid.className="cards";for(const product of response.result.hits){const card=document.createElement("div");card.className="item";const h=document.createElement("h3");h.textContent=product.name;const p=document.createElement("p");p.textContent="¥"+product.price+" · "+product.tags.join(" / ");const small=document.createElement("small");small.textContent=product.evidence+"；库存 "+product.stock;card.append(h,p,small);grid.append(card)}target.append(grid);jsonView({intent:response.result.intent,source:response.result.source,fallback:response.result.fallback},target);
   }else if(tab==="skill"){if(image&&!response.result.screenshot_processed){const hint=document.createElement("p");hint.className="hint";hint.textContent="截图仅本地预览，本次未识别；Skill 依据文字输入生成。";target.append(hint)}jsonView(response.result.markdown,target)}
   else jsonView(response.result,target);
   if(tab==="tags"){const label=document.createElement("label"),check=document.createElement("input");check.type="checkbox";label.append(check,document.createTextNode(" 我已逐项核验候选标签和来源字段"));check.onchange=()=>{$("#export").disabled=!check.checked};target.append(label)}else $("#export").disabled=false;
  }catch(e){if(tab===activeTab)showError(e.message)}
  finally{if(tab===activeTab){button.disabled=false;button.textContent="运行工作流"}}
 };
}
function dataURL(file){return new Promise((resolve,reject)=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error("文件读取失败"));reader.readAsDataURL(file)})}
function renderImage(){
 panel.innerHTML='<h2>商品图生产工作台</h2><div class="track">自有素材 → 手动裁切 → 边缘背景去除 → 白底 / 透底 → 人工验收</div><p class="hint">本地算法，不上传原图。适合背景平整、主体与背景颜色分离的商品图；复杂背景或主体触边可能处理不佳。叠在商品上的 Logo 不会自动移除，需重新提供干净原图。</p><label for="image-file">上传自有或已获授权商品图（最多 5 MB）</label><input id="image-file" type="file" accept="image/png,image/jpeg,image/webp"><label for="tolerance">背景颜色容差 <span id="tol-value">35</span></label><input type="range" id="tolerance" min="5" max="100" value="35"><div class="row"><label><input id="white" type="checkbox" checked> 输出白底，取消则透底 PNG</label></div><div class="two"><div><h3>裁切范围（0—100%）</h3><label for="crop-x">左边距</label><input id="crop-x" type="number" min="0" max="95" value="0"><label for="crop-y">上边距</label><input id="crop-y" type="number" min="0" max="95" value="0"><label for="crop-w">宽度</label><input id="crop-w" type="number" min="5" max="100" value="100"><label for="crop-h">高度</label><input id="crop-h" type="number" min="5" max="100" value="100"></div><div><canvas id="canvas" width="500" height="350" aria-label="商品图片预览"></canvas><p class="hint">仅从画布边缘连通的相近颜色区域移除背景；请检查浅色商品、孔洞和边缘细节。</p></div></div><div class="row"><button class="primary" id="process">裁切并处理</button><button id="image-reset">恢复原图</button><button id="image-save" disabled>下载 PNG</button></div><div id="output" aria-live="polite"></div><details><summary>多角度生成：任务方案（尚未接通生成模型）</summary><p class="hint">需要参考图和独立图像生成服务。此 MVP 不将旋转、镜像或透视变形当成新角度生成，也不推测未展示的商品结构。</p><button id="plan">导出多角度生成与审核任务</button></details>';
 $("#tolerance").oninput=()=>{$("#tol-value").textContent=$("#tolerance").value};
 let bitmap=null;
 function draw(){if(!bitmap)return;const canvas=$("#canvas");canvas.width=bitmap.width;canvas.height=bitmap.height;canvas.getContext("2d").drawImage(bitmap,0,0);processed=false;$("#image-save").disabled=true}
 $("#image-file").onchange=async()=>{try{const f=$("#image-file").files[0];if(!f)return;if(f.size>5000000)throw Error("商品图最多 5 MB");if(!["image/png","image/jpeg","image/webp"].includes(f.type))throw Error("不支持的图片格式");const b=await createImageBitmap(f);if(b.width*b.height>24000000){b.close();throw Error("像素过多，请先缩小到 2400 万像素以下")}const scale=Math.min(1,1400/Math.max(b.width,b.height));const temp=document.createElement("canvas");temp.width=Math.round(b.width*scale);temp.height=Math.round(b.height*scale);temp.getContext("2d").drawImage(b,0,0,temp.width,temp.height);b.close();if(bitmap)bitmap.close();bitmap=await createImageBitmap(temp);draw()}catch(e){showError(e.message)}};
 $("#image-reset").onclick=draw;
 $("#process").onclick=()=>{try{
  if(!bitmap)throw Error("请先上传商品图");const [x,y,w,h]=["x","y","w","h"].map(k=>Number($("#crop-"+k).value));if([x,y,w,h].some(v=>!Number.isFinite(v))||x<0||y<0||w<5||h<5||x+w>100||y+h>100)throw Error("裁切范围必须位于图像内，宽高至少为 5%");
  const canvas=$("#canvas");canvas.width=Math.max(1,Math.round(bitmap.width*w/100));canvas.height=Math.max(1,Math.round(bitmap.height*h/100));const ctx=canvas.getContext("2d");ctx.drawImage(bitmap,bitmap.width*x/100,bitmap.height*y/100,bitmap.width*w/100,bitmap.height*h/100,0,0,canvas.width,canvas.height);
  const pixels=ctx.getImageData(0,0,canvas.width,canvas.height),{data,width,height}=pixels;
  const seeds=[0,width-1,(height-1)*width,width*height-1],colors=seeds.map(i=>Array.from(data.slice(i*4,i*4+3))),threshold=Number($("#tolerance").value),seen=new Uint8Array(width*height),queue=new Int32Array(width*height);let head=0,tail=0,count=0;
  function enqueue(i){if(i<0||i>=seen.length||seen[i])return;seen[i]=1;const p=i*4;if(data[p+3]===0||colors.some(c=>Math.hypot(data[p]-c[0],data[p+1]-c[1],data[p+2]-c[2])<=threshold))queue[tail++]=i}
  for(let px=0;px<width;px++){enqueue(px);enqueue((height-1)*width+px)}for(let py=0;py<height;py++){enqueue(py*width);enqueue(py*width+width-1)}
  while(head<tail){const i=queue[head++],p=i*4;data[p+3]=0;count++;if(i%width)enqueue(i-1);if(i%width<width-1)enqueue(i+1);enqueue(i-width);enqueue(i+width)}
  ctx.putImageData(pixels,0,0);if($("#white").checked){ctx.globalCompositeOperation="destination-over";ctx.fillStyle="white";ctx.fillRect(0,0,width,height);ctx.globalCompositeOperation="source-over"}processed=true;$("#image-save").disabled=false;$("#output").textContent="已处理 "+width+"×"+height+"，背景移除约 "+Math.round(count/(width*height)*100)+"%。请检查商品完整性与边缘；本算法不判断平台 Logo。";
 }catch(e){showError(e.message)}};
 $("#image-save").onclick=()=>{if(!processed)return;$("#canvas").toBlob(blob=>{const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="product-"+($("#white").checked?"white":"transparent")+".png";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)},"image/png")};
 $("#plan").onclick=()=>download("multi-angle-job.json",{status:"awaiting_image_provider",requested_views:["正面","侧面","背面"],references_required:true,checks:["外形、颜色、纹理与规格一致","未知结构必须注明为生成假设","人工审核后才可发布"],note:"当前不会生成新角度图片"});
}
document.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>{tab=b.dataset.tab;document.querySelectorAll("[data-tab]").forEach(x=>x.setAttribute("aria-selected",String(x===b)));render()});
$("#health").onclick=async()=>{try{const res=await fetch(backend()+"/health",{signal:AbortSignal.timeout(90000)});const d=await res.json();if(!res.ok)throw Error("后端连接失败");$("#connection").textContent=d.llm_configured?"后端在线，模型已配置。截图识别："+(d.vision_configured?"已配置":"未配置"):"后端在线，尚未配置模型 Key 与演示口令"}catch{$("#connection").textContent="未连接到后端；浏览器工具模式仍可使用。请检查后端地址，或稍后重试以等待函数冷启动。"}};
$("#llm").onchange=()=>{$("#mode").textContent=$("#llm").checked?"真实 DeepSeek 模式 · 需后端配置":"浏览器工具模式 · 无模型费用"};
document.querySelectorAll("[data-tab]").forEach(x=>x.setAttribute("aria-selected",String(x.dataset.tab===tab)));render();
