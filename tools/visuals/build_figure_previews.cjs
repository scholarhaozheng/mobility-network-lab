// Create bounded, lossless browser previews from released figures.
// NODE_PATH must expose sharp; optimize_site_images.py supplies the task list.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),sharp=require('sharp');
sharp.concurrency(1);sharp.cache({memory:32,files:0,items:16});
const root=path.resolve(__dirname,'../..'),docs=path.join(root,'docs');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
(async()=>{
 const tasks=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),entries={};
 const out=path.join(docs,'assets/performance/previews');fs.mkdirSync(out,{recursive:true});
 for(const source of tasks){
  const original=path.join(docs,source),bytes=fs.readFileSync(original),originalSha=sha(bytes);
  const sibling=original.replace(/\.svg$/i,'.png');
  const input=/\.svg$/i.test(source)&&fs.existsSync(sibling)?sibling:original;
  const inputBytes=fs.readFileSync(input),inputSha=sha(inputBytes),key=sha(Buffer.from(source+originalSha+inputSha)).slice(0,24);
  const meta=await sharp(inputBytes,{limitInputPixels:80000000}).metadata();
  const entry={original:source,sourceSha256:originalSha,originalBytes:bytes.length,rasterSource:path.relative(docs,input).replaceAll('\\','/'),rasterSourceSha256:inputSha,width:meta.width,height:meta.height};
  for(const [variant,size] of [['thumb',960],['reading',1600]]){
   const file=path.join(out,`${key}-${size}.webp`);
   if(!fs.existsSync(file))await sharp(inputBytes,{limitInputPixels:80000000}).resize({width:size,height:size,fit:'inside',withoutEnlargement:true}).webp({lossless:true,effort:5}).toFile(file);
   // Reduce dimensions for unusually large lossless photographs; never crop.
   let result=fs.readFileSync(file),bound=size;
   while(result.length>750000&&bound>480){
    bound=Math.floor(bound*.85);
    await sharp(inputBytes,{limitInputPixels:80000000}).resize({width:bound,height:bound,fit:'inside',withoutEnlargement:true}).webp({lossless:true,effort:5}).toFile(file);
    result=fs.readFileSync(file);
   }
   const m=await sharp(result).metadata();
   entry[variant]={src:path.relative(docs,file).replaceAll('\\','/'),bytes:result.length,sha256:sha(result),width:m.width,height:m.height};
  }
  entries[source]=entry;
 }
 const manifest={schema:'mcl-browser-previews-v1',transform:'Released raster sibling when available; otherwise rasterize the released SVG. Resize without crop, preserve aspect ratio and transparency, encode lossless WebP. Original scientific assets are unchanged.',entries};
 fs.writeFileSync(path.join(docs,'assets/performance/manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({figures:tasks.length,originalBytes:Object.values(entries).reduce((s,e)=>s+e.originalBytes,0),thumbBytes:Object.values(entries).reduce((s,e)=>s+e.thumb.bytes,0)}));
})().catch(e=>{console.error(e);process.exitCode=1;});
