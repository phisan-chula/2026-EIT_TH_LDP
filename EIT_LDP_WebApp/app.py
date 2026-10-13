"""Thailand LDP Streamlit province explorer."""
import gzip,json,math,re
from pathlib import Path
import folium,streamlit as st
from shapely import wkb
from shapely.geometry import Point,shape
from streamlit_folium import st_folium
HERE=Path(__file__).resolve().parent
DATA=HERE/"data/provinces.geojson"
LOOKUP=HERE/"data/province_lookup.json.gz"
BASE="https://github.com/phisan-chula/2026-EIT_TH_LDP"
st.set_page_config(page_title="Thailand LDP | Province Explorer",page_icon="🗺️",layout="wide")
@st.cache_data
def features():
    return json.loads(DATA.read_text(encoding="utf-8"))["features"]
@st.cache_resource
def spatial_index():
    with gzip.open(LOOKUP,"rt",encoding="utf-8") as f: records=json.load(f)
    return [(r["uid"],r["bbox"],wkb.loads(bytes.fromhex(r["wkb"]))) for r in records]
def locate(lat,lon):
    pt=Point(lon,lat)
    return [uid for uid,(xmin,ymin,xmax,ymax),poly in spatial_index()
            if xmin<=lon<=xmax and ymin<=lat<=ymax and poly.covers(pt)]
def parse_coordinates(s):
    parts=[v for v in re.split(r"[,;\s]+",s.strip()) if v]
    if len(parts)!=2: raise ValueError("Provide latitude longitude (comma optional).")
    try: lat,lon=map(float,parts)
    except ValueError: raise ValueError("Coordinates must be numeric.")
    if not(-90<=lat<=90 and -180<=lon<=180): raise ValueError("Coordinates out of range.")
    return lat,lon
def field(p,k): return str(p.get(k)) if p.get(k) not in (None,"") else "—"
def links(p):
    hasc=str(p.get("HASC_1") or "").strip()
    if not re.fullmatch(r"TH\.[A-Za-z0-9_]+",hasc): return None
    folder=hasc.replace(".","_").upper()
    anchor="-"+folder.lower().replace("th_","th",1)+"--wkt---proj4"
    return (f"{BASE}/blob/main/src/OUTPUT_LDP/{folder}/{folder}_OnePage.pdf",
            f"{BASE}/tree/main/src/OUTPUT_LDP#{anchor}")
st.title("Thailand Low Distortion Projection (LDP)")
st.caption("Click the map or enter coordinates to identify and highlight a province • Hover for details")
if not(DATA.exists() and LOOKUP.exists()):
    st.error("Province data are missing. Run prepare_data.py with the GPKG and commit both files in data/.")
    st.stop()
ftrs=features()
with st.sidebar:
    st.header("Locate a coordinate")
    st.caption("Geographic latitude and longitude (WGS 84, decimal degrees)")
    if "pending_coordinate_text" in st.session_state:
        st.session_state.coordinate_input=st.session_state.pop("pending_coordinate_text")
    with st.form("coordinates"):
        coord=st.text_input("Latitude, Longitude",value="13.862218673831903, 100.53903881302078",
            key="coordinate_input",placeholder="13.862218673831903 100.53903881302078")
        submitted=st.form_submit_button("Find province",use_container_width=True)
    if st.button("Clear selection",use_container_width=True):
        for k in ("selected_uid","selected_coords","last_map_click"): st.session_state.pop(k,None)
        st.rerun()
    st.divider()
    st.metric("Province polygons",len(ftrs))
    st.info("Display boundaries are simplified; coordinate matching uses full-resolution geometries.")
if submitted:
    try: lat,lon=parse_coordinates(coord)
    except ValueError as e: st.error(str(e))
    else:
        matches=locate(lat,lon)
        st.session_state.selected_uid=matches[0] if matches else None
        st.session_state.selected_coords=(lat,lon)
        st.session_state.multiple_matches=len(matches)
uid=st.session_state.get("selected_uid")
selected=next((f for f in ftrs if f["properties"].get("_uid")==uid),None)
if "selected_coords" in st.session_state:
    if selected:
        p=selected["properties"]
        st.success(f"Point-in-polygon: **{field(p,'NAME_1')}**  |  **HASC_1 (String) = {field(p,'HASC_1')}**  |  LDP: {field(p,'LDP')}  |  CM_CP: {field(p,'CM_CP')}")
        ll=links(p)
        if ll: st.markdown(f"**Province resources:** [📄 OpenPage]({ll[0]}) &nbsp; | &nbsp; [📏 TestLine]({ll[1]})")
        if st.session_state.get("multiple_matches",0)>1: st.warning("Multiple matching polygons (boundary or overlap).")
    else: st.warning("No polygon contains the entered coordinate.")
m=folium.Map(location=[15.2,101.0],zoom_start=6,tiles="CartoDB positron",control_scale=True)
for f in ftrs:
    p=f["properties"]; selected_flag=p.get("_uid")==uid
    display=dict(f); dp=dict(p)
    area=p.get("part_area")
    dp["_area_text"]=f"{math.trunc(float(area)):,}" if area is not None else "—"
    display["properties"]=dp
    attrs=["NAME_1","HASC_1","LDP","CM_CP","_area_text","NS_km","EW_km"]
    aliases={"NAME_1":"Province","HASC_1":"HASC","LDP":"Projection","CM_CP":"CM_CP","_area_text":"Area (km²)","NS_km":"N–S (km)","EW_km":"E–W (km)"}
    keys=[k for k in attrs if k in dp]
    folium.GeoJson({"type":"FeatureCollection","features":[display]},
        name=field(p,"NAME_1"),
        style_function=lambda _,sel=selected_flag,ldp=p.get("LDP"):{
          "color":"#d7191c" if sel else "#526581",
          "weight":3.5 if sel else 0.9,
          "fillColor":"#ffb400" if sel else ("#b7d0e3" if ldp=="TM" else "#bfe3cb"),
          "fillOpacity":0.68 if sel else 0.32},
        highlight_function=lambda _:{"color":"#ff7f00","weight":3,"fillOpacity":0.65},
        tooltip=folium.GeoJsonTooltip(fields=keys,aliases=[aliases[k] for k in keys],labels=True,sticky=True)
    ).add_to(m)
    code=str(p.get("HASC_1") or "").strip()
    if code:
        pt=shape(f["geometry"]).representative_point()
        color="#d7191c" if str(p.get("LDP") or "").strip().upper()=="LCC" else "#000000"
        folium.Marker(location=[pt.y,pt.x],icon=folium.DivIcon(icon_size=(100,18),
            icon_anchor=(50,9),html=(f'<div style="width:100px;text-align:center;'
            f'font:600 11px Arial,sans-serif;color:{color};'
            f'text-shadow:0 1px 2px white,1px 0 2px white,-1px 0 2px white;'
            f'pointer-events:none;white-space:nowrap;">{code}</div>'))).add_to(m)
if "selected_coords" in st.session_state:
    y,x=st.session_state.selected_coords
    folium.CircleMarker([y,x],radius=6,weight=2,color="#111827",fill=True,
        fill_color="#ff4646",fill_opacity=1,tooltip=f"Input: {y:.7f}, {x:.7f}").add_to(m)
if selected:
    xmin,ymin,xmax,ymax=shape(selected["geometry"]).bounds
    m.fit_bounds([[ymin,xmin],[ymax,xmax]],padding=[25,25])
resp=st_folium(m,height=650,width=None,returned_objects=["last_clicked"],key="province-map")
clicked=(resp or {}).get("last_clicked")
if clicked is not None:
    y,x=float(clicked["lat"]),float(clicked["lng"])
    if (y,x)!=st.session_state.get("last_map_click"):
        st.session_state.last_map_click=(y,x)
        matches=locate(y,x)
        st.session_state.selected_uid=matches[0] if matches else None
        st.session_state.selected_coords=(y,x)
        st.session_state.multiple_matches=len(matches)
        st.session_state.pending_coordinate_text=f"{y:.9f}, {x:.9f}"
        st.rerun()
if selected:
    p=selected["properties"]
    st.subheader(f"Selected: {field(p,'NAME_1')}")
    columns=st.columns(4)
    for col,(title,key) in zip(columns,[("HASC","HASC_1"),("LDP","LDP"),("CM_CP","CM_CP"),("Area (km²)","part_area")]):
        col.metric(title,field(p,key))
    st.caption(f"Thai name: {field(p,'NL_NAME_1')}  •  Dimensions: {field(p,'EW_km')} km E–W × {field(p,'NS_km')} km N–S")
st.caption("CRS: WGS 84 longitude/latitude (EPSG:4326). Full-resolution lookup; simplified display.")
