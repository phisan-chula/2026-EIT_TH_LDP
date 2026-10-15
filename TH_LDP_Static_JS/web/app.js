'use strict';
const GH='https://github.com/phisan-chula/2026-EIT_TH_LDP';
const map=L.map('map',{preferCanvas:true}).setView([15.3,101],6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(map);
const info=document.getElementById('info'),input=document.getElementById('location');
let features=[],geoLayer=null,selectedLayer=null,locationMarker=null;
function escapeHTML(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function onSegment(p,a,b){const cross=(p[1]-a[1])*(b[0]-a[0])-(p[0]-a[0])*(b[1]-a[1]);if(Math.abs(cross)>1e-10)return false;return p[0]>=Math.min(a[0],b[0])-1e-10&&p[0]<=Math.max(a[0],b[0])+1e-10&&p[1]>=Math.min(a[1],b[1])-1e-10&&p[1]<=Math.max(a[1],b[1])+1e-10;}
function inRing(p,ring){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const a=ring[i],b=ring[j];if(onSegment(p,a,b))return true;if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;}return inside;}
function inPolygon(p,poly){return poly.length>0&&inRing(p,poly[0])&&!poly.slice(1).some(r=>inRing(p,r));}
function containsPoint(p,g){if(!g)return false;if(g.type==='Polygon')return inPolygon(p,g.coordinates);if(g.type==='MultiPolygon')return g.coordinates.some(poly=>inPolygon(p,poly));return false;}
function findRegion(lat,lng){const p=[lng,lat];return features.find(f=>containsPoint(p,f.geometry))||null;}
function style(f){return{color:'#486478',weight:1,fillColor:String(f.properties?.LDP??'').toUpperCase()==='LCC'?'#d15e42':'#328ab9',fillOpacity:.38};}
function links(f){const code=String(f.properties?.HASC_1||'');const slug=code.replaceAll('.','_');if(!/^TH_[A-Z0-9_]+$/.test(slug))return '';
const anchor=slug.toLowerCase().replace(/^th_/,'th');
const doc=`${GH}/tree/main/src/OUTPUT_LDP#-${anchor}--wkt---proj4`;
const pdf=`${GH}/blob/main/src/OUTPUT_LDP/${encodeURIComponent(slug)}/${encodeURIComponent(slug)}_OnePage.pdf`;
return `<div class="popup-links"><a class="link" target="_blank" rel="noopener noreferrer" href="${doc}" title="TestLine documentation">📏 TestLine ↗</a><a class="link" target="_blank" rel="noopener noreferrer" href="${pdf}" title="OnePage PDF">📄 OnePage ↗</a></div>`;
}
function popup(f){const p=f.properties||{};return `<div class="popup-code">${escapeHTML(p.HASC_1)}</div><div>${escapeHTML(p.NAME_1)}</div><div>${escapeHTML(p.LDP)}</div>${links(f)}`;}
function selectFeature(f,latlng){if(selectedLayer)geoLayer.resetStyle(selectedLayer);selectedLayer=geoLayer?.getLayers().find(l=>l.feature===f)||null;if(selectedLayer){selectedLayer.setStyle({weight:2,color:'#122e44',fillOpacity:.70});selectedLayer.bringToFront();}L.popup().setLatLng(latlng).setContent(popup(f)).openOn(map);info.textContent=`Selected: ${f.properties.HASC_1} · ${f.properties.NAME_1||''}`;}
async function init(){try{const res=await fetch('./data/provinces.geojson');if(!res.ok)throw Error(`GeoJSON HTTP ${res.status}`);const fc=await res.json();features=fc.features||[];if(!features.length)throw Error('No province polygons. Run the simplification script first.');geoLayer=L.geoJSON(fc,{style,onEachFeature(f,l){l.bindTooltip(escapeHTML(f.properties?.HASC_1),{sticky:true});l.on('click',e=>{L.DomEvent.stopPropagation(e);selectFeature(findRegion(e.latlng.lat,e.latlng.lng)||f,e.latlng);});}}).addTo(map);map.fitBounds(geoLayer.getBounds(),{padding:[20,20]});info.textContent=`${features.length} regions loaded · click a polygon`;}
catch(e){console.error(e);info.textContent=`Map data missing: ${e.message}`;}}
function locate(){const vals=input.value.trim().split(/[ ,;]+/).map(Number);if(vals.length!==2||!vals.every(Number.isFinite)||Math.abs(vals[0])>90||Math.abs(vals[1])>180){info.textContent='Enter a valid latitude, longitude';return;}const [lat,lng]=vals;map.setView([lat,lng],10);if(locationMarker)map.removeLayer(locationMarker);locationMarker=L.circleMarker([lat,lng],{radius:5,color:'#c11',fillColor:'#e33',fillOpacity:1}).addTo(map);const f=findRegion(lat,lng);if(f)selectFeature(f,L.latLng(lat,lng));else info.textContent='No region found at this coordinate';}
document.getElementById('locate').addEventListener('click',locate);input.addEventListener('keydown',e=>{if(e.key==='Enter')locate();});map.on('click',e=>{const f=findRegion(e.latlng.lat,e.latlng.lng);if(f)selectFeature(f,e.latlng);else info.textContent=`Outside polygons: ${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;});
init();