# -*- coding: utf-8 -*-
"""  
PROGRAM : Constr_LDP (Refactored for Batch Province Processing)
***Design of a Low Distortion Projection for a Construction Project***</br>  
"""
import warnings
warnings.filterwarnings(
    "ignore",
    message="You will likely lose important projection information"
)
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import sys, re, json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.affinity import scale
from shapely.geometry import Point, LineString, MultiPoint
import pygeodesy as pgd
import pyproj
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
import argparse

TM =( '+proj=tmerc +lat_0=0.0 +lon_0={lon_0:.8f} +k_0={k_0:.6f} '
      '+x_0={x_0} +y_0={y_0} +ellps=WGS84 +units=m +no_defs' )

LCC =( '+proj=lcc +lat_1={lat_0:.8f} +lat_0={lat_0:.8f} +lon_0={lon_0:.8f} '
       '+k_0={k_0:.6f} +x_0={x_0} +y_0={y_0} +ellps=WGS84 +units=m +no_defs' )

COL_LDP = ['UNDUL', 'h','HSF','PSF','CSF', 'CSF_ppm', 'LDP_E', 'LDP_N']

def dd2DMS( dd, PREC=7, POS=''  ):
    '''convert degree to DMS string'''
    return pgd.dms.toDMS( dd, prec=PREC, pos=POS )

def dd2DM( dd ): 
    ''' truncate degree to degree-minute DDD:MM '''
    # F_DM explicitly formats as Degrees and Minutes, using ':' separator
    return pgd.dms.toDMS(dd, form=pgd.dms.F_DM, prec=0, sep='')

def parse_dms( dms ):
    return pgd.parseDMS( dms, sep=':')

class LDP_Design:
    @staticmethod
    def _safe_code(code: str) -> str:
        """Convert HASC_1 to a filesystem-safe code: TH.KK -> TH_KK."""
        return code.strip().upper().replace(".", "_")

    def __init__(self, args, prov_code, prov_data):
        self.ARGS = args
        self.PROV_CODE = prov_code.strip().upper()  # logical GADM/TOML key
        self.FILE_CODE = self._safe_code(self.PROV_CODE)
        self.DATA = pd.Series(prov_data)
        
        # Filesystem outputs use underscores, e.g. TH.KK -> TH_KK.
        self.STEM = f"{self.FILE_CODE}_LDP"
        self.RESULT = Path('./OUTPUT_LDP') / self.FILE_CODE
        self.RESULT.mkdir(parents=True, exist_ok=True)
        
        self.GetOFFSET_PP()
        self.ELLPS  = pgd.datums.Ellipsoids.WGS84
        
        ###########################################################
        TGM_2017 = "/usr/share/GeographicLib/geoids/tgm2017-1.pgm"
        base_dir = Path(__file__).resolve().parent
        tgm_path = base_dir / "tgm2017-1.pgm" # side-car file
        if Path( TGM_2017 ).is_file():
            self.GEOID = pgd.geoids.GeoidKarney( TGM_2017 )
        else:
            self.GEOID = pgd.geoids.GeoidKarney( str(tgm_path) )
            
        self.dfPP = self.LoadTestPoint()

        # Capture population and points from ALL initial points before filtering
        if 'POP' in self.dfPP.columns:
            self.INITIAL_POP = self.dfPP['POP'].sum()
        else:
            self.INITIAL_POP = 0.0
        self.INITIAL_POINTS = len(self.dfPP)

        # Apply MSL Outlier Filter unless explicitly bypassed
        if not self.ARGS.bypass:
            self.dfPP = self.RemoveOutliers(self.dfPP)
            
        # Handle LDP = 'AUTO' to automatically set TM projection via centroid
        if self.DATA['LDP'] == 'AUTO':
            cen_lng = self.dfPP.lng.mean()
            cm_str = pgd.dms.toDMS(cen_lng, prec=5, sep=':')
            self.DATA['LDP'] = ['TM', cm_str]
            print(f" -> AUTO detected: using TM with Central Meridian {cm_str}")

        UNDUL = self.GEOID.height( self.dfPP.lat.mean(),self.dfPP.lng.mean() )
        
        # Handle PP_MSL overrides for the base MSL
        if 'PP_MSL' not in self.DATA or self.DATA['PP_MSL'] == 'AUTO':
            base_msl = self.dfPP.MSL.mean()
            print(f" -> AUTO detected PP_MSL: using average MSL {base_msl:.3f}m")
        else:
            base_msl = float(self.DATA['PP_MSL'])
            print(f" -> Using user-defined PP_MSL: {base_msl:.3f}m")

        self.MSL_PP = base_msl + self.DATA.OFFSET_PP[0]
        self.HAE_PP = UNDUL + self.MSL_PP                 # h = N + H
        RG = self.ELLPS.rocGauss( self.dfPP.lat.mean() )  # RG = sqrt(MN)
        self.k0 = np.round(1 + self.HAE_PP/RG, 6)         # M.Dennis 2016  6 digits
        self.CTR_PAR = self.dfPP.lat.mean() 
        
        ##########################################################
        if self.DATA['FALSE_EN'] == 'AUTO':
            self.CreateLDP( 0, 0 )
            self.dfPP[COL_LDP] = self.dfPP.apply( self.CalcLDP, axis=1, result_type='expand' )
            FalseE, FalseN = self._FindFalse(self.dfPP.LDP_E), self._FindFalse(self.dfPP.LDP_N)
            self.dfPP[['LDP_E','LDP_N']] = self.dfPP[['LDP_E','LDP_N']] + [FalseE, FalseN]
            self.CreateLDP( FalseE, FalseN )
            print(f" -> AUTO detected FALSE_EN: E: {FalseE}, N: {FalseN}")
        else:
            FalseE, FalseN = self.DATA['FALSE_EN'] # user defined
            self.CreateLDP( FalseE, FalseN )
            self.dfPP[COL_LDP] = self.dfPP.apply( self.CalcLDP, axis=1, result_type='expand' )

    def Spatial_Thinning(self, df, decimals=2):
        """
        Reduces point density by snapping to a pseudo-grid.
        decimals=2 -> ~1.1 km spacing (EPSG:4326)
        decimals=3 -> ~111 m spacing
        """
        print(f" -> THINNING: Snapping points to {decimals} decimal grid for visualization...")
        
        df_temp = df.copy()
        # Round the geometry X and Y to the specified precision
        df_temp['grid_x'] = df_temp.geometry.x.round(decimals)
        df_temp['grid_y'] = df_temp.geometry.y.round(decimals)
        
        # Drop duplicates that fall into the exact same grid cell
        df_thinned = df_temp.drop_duplicates(subset=['grid_x', 'grid_y'], keep='first')
        
        # Clean up temporary columns
        df_thinned = df_thinned.drop(columns=['grid_x', 'grid_y'])
        
        print(f" -> THINNING: Plot points reduced from {len(df)} to {len(df_thinned)}.")
        return df_thinned

    def RemoveOutliers(self, df):
        # 1. Hard filter for absolute NoData flags (e.g., -9999)
        nodata_mask = df['MSL'] == -9999
        df_nodata = df[nodata_mask]
        df_clean = df[~nodata_mask].copy()
        
        dropped_nodata = df_nodata['MSL'].tolist() if not df_nodata.empty else []
        dropped_stat = []
        
        # 2. Statistical Filter (LOF or 5% Quantile)
        if len(df_clean) > 5:  # Need minimum points for statistics
            try:
                from sklearn.neighbors import LocalOutlierFactor
                from sklearn.preprocessing import StandardScaler
                
                features = np.column_stack((df_clean.geometry.x, df_clean.geometry.y, df_clean['MSL']))
                features_scaled = StandardScaler().fit_transform(features)
                
                neighbors = min(20, len(df_clean) - 1)
                lof = LocalOutlierFactor(n_neighbors=neighbors, contamination=0.02)
                outlier_labels = lof.fit_predict(features_scaled)
                
                df_inliers = df_clean[outlier_labels == 1].copy()
                df_outliers = df_clean[outlier_labels == -1].copy()
                dropped_stat = df_outliers['MSL'].tolist() if not df_outliers.empty else []
                
            except (ImportError, Exception):
                print(" -> WARNING: LOF filtering unavailable or failed. Using 5% head/tail cutoff for MSL outlier detection.")
                #### QUANTILE , PSN ####
                # Calculate the 5th and 95th percentiles
                lower_bound = df_clean['MSL'].quantile(0.05)
                upper_bound = df_clean['MSL'].quantile(0.95)
                
                # Mask values outside this 5% to 95% range
                outlier_mask = (df_clean['MSL'] < lower_bound) | (df_clean['MSL'] > upper_bound)

                df_inliers = df_clean[~outlier_mask].copy()
                df_outliers = df_clean[outlier_mask].copy()
                dropped_stat = df_outliers['MSL'].tolist() if not df_outliers.empty else []
        else:
            df_inliers = df_clean
        all_dropped = dropped_nodata + dropped_stat
        
        if all_dropped:
            print(f" -> OUTLIER FILTER: Dropped {len(all_dropped)} points.")
            print(f" -> Dropped MSL values: {all_dropped}")
        else:
            print(" -> OUTLIER FILTER: No MSL outliers detected.")
            
        # Fallback to original dataframe if filtering removed everything
        if df_inliers.empty:
            print(" -> ERROR: Filter removed all valid points. Proceeding with original data.")
            return df
            
        return df_inliers

    def GetOFFSET_PP(self):
        if 'OFFSET_PP' in self.DATA.keys():
            self.DATA['OFFSET_PP'] = [ self.DATA['OFFSET_PP'], 'defined in TOML']
        else:
            self.DATA['OFFSET_PP'] = [0.0, 'default hPP from average topo or pnts']
        if self.ARGS.OFFSET_PP is not None:  # most prioritized
            self.DATA['OFFSET_PP'] = [ self.ARGS.OFFSET_PP, 'defined by CLI args' ]
        print( f'{self.DATA}' )

    def CalcLDP(self, row):
        UNDUL = self.GEOID.height( row.lat,row.lng )
        RG  = self.ELLPS.rocGauss( row.lat )
        h   = UNDUL + row.MSL
        HSF = RG/(RG+h)
        ldp_crs = pyproj.Proj(self.DATA.LDP_CRS)
        PSF = ldp_crs.get_factors( row.lng, row.lat ).meridional_scale
        CSF = PSF*HSF
        CSF_ppm = (CSF-1)*1E6
        TR = pyproj.Transformer.from_crs( 'epsg:4326', self.DATA.LDP_CRS ) 
        LDP_E, LDP_N = TR.transform( row.lat, row.lng )
        return [UNDUL, h, HSF, PSF, CSF, CSF_ppm, LDP_E, LDP_N]

    def CreateLDP(self, FalseE, FalseN):
        if self.DATA.LDP[0] == 'TM':
            LDP_STR = TM.format( lon_0=parse_dms(self.DATA.LDP[1]), k_0=self.k0, x_0=FalseE, y_0=FalseN )
        elif self.DATA.LDP[0] == 'LCC':
            # Mathematically round to the nearest minute as pure decimal degrees for pyproj
            lat_0_dd = round(self.dfPP.lat.mean() * 60) / 60.0
            lon_0_dd = round(self.dfPP.lng.mean() * 60) / 60.0
            LDP_STR = LCC.format(lat_0=lat_0_dd, lon_0=lon_0_dd, k_0=self.k0, x_0=FalseE, y_0=FalseN )
        else:
            print( f'UNKNOWN***LDP_TYPE = {self.DATA.LDP} ...'); raise Exception('***ERROR***')
        self.LDP_PROJ_STRING = LDP_STR
        self.DATA['LDP_CRS'] = pyproj.CRS( LDP_STR )

    def _FindFalse(self, dfEN):
        digits = int( np.log10(np.ptp(dfEN))) 
        lo = np.round( dfEN.min(), -(digits-1) ) ; up = np.round( dfEN.max(), -(digits-1) )
        mid = (lo+up)/2
        target = 5*(10**digits)
        return int( np.round( target-mid, -digits) )

    def _resolve_gpkg_path(self, configured_path):
        """Resolve old dotted paths and new underscore-normalised paths.

        This keeps existing TOML files usable. For example, when TOML contains
        OUTPUT_SAMPL/TH.KK/TH.KK_SAMPL.gpkg but the new output is stored as
        OUTPUT_SAMPL/TH_KK/TH_KK_SAMPL.gpkg, the latter is selected.
        """
        original = Path(configured_path).expanduser()
        normalised = Path(str(original).replace(self.PROV_CODE, self.FILE_CODE))

        if normalised.exists():
            if normalised != original:
                print(f" -> Normalised GPKG path: {original} -> {normalised}")
            return normalised
        if original.exists():
            return original

        raise FileNotFoundError(
            f"Input GPKG not found. Checked: {normalised} and {original}"
        )

    def LoadTestPoint( self ):
        if 'GPKG' in self.DATA.keys():
            gdfs = list()
            gpkg_path = self._resolve_gpkg_path(self.DATA['GPKG'][0])
            for lay in self.DATA['GPKG'][1].split('|'):
                # Read the configured layer from the resolved sample GeoPackage.
                gdf = gpd.read_file(gpkg_path, layer=lay)
                gdfs.append( gdf )
            gdf = pd.concat( gdfs, ignore_index=True, copy=True )
            
            # Reproject to 4326 if not already
            dfPP = gdf.to_crs('EPSG:4326')
            dfPP['lng'] = dfPP.geometry.x
            dfPP['lat'] = dfPP.geometry.y
            
            # Ensure MSL column exists or provide a default (fallback to 0)
            if 'MSL' not in dfPP.columns:
                print(" -> WARNING: 'MSL' column not found in GPKG. Defaulting to 0.0")
                dfPP['MSL'] = 0.0
                
            # If the point name column doesn't exist, use the sampl_point or an index
            if 'Point' not in dfPP.columns:
                if 'sampl_point' in dfPP.columns:
                    dfPP['Point'] = dfPP['sampl_point']
                else:
                    dfPP['Point'] = dfPP.index.astype(str)
                    
        else:
            print("ERROR: GPKG not defined in the TOML configuration.")
            sys.exit(1)
            
        return dfPP

    def Print_Defintion(self):
        parm = self.DATA.LDP_CRS.to_dict()
        LDP_DEF = self.DATA.LDP_CRS.to_string()
        
        # Extract direct parameters for exact matching output
        if self.DATA.LDP[0] == 'TM':
            ll_dm = dd2DM(parm['lon_0'])
            LDP_DEF_ = re.sub(r'\+lon_0=[^\s]+', f'+lon_0={ll_dm}', LDP_DEF)
        elif self.DATA.LDP[0] == 'LCC':
            lat_dm = dd2DM(parm['lat_0'])
            lon_dm = dd2DM(parm['lon_0'])
            LDP_DEF_ = re.sub(r'\+lat_0=[^\s]+', f'+lat_0={lat_dm}', LDP_DEF)
            LDP_DEF_ = re.sub(r'\+lat_1=[^\s]+', f'+lat_1={lat_dm}', LDP_DEF_)
            LDP_DEF_ = re.sub(r'\+lon_0=[^\s]+', f'+lon_0={lon_dm}', LDP_DEF_)
            
        # Transform 2 lines of definition into a single JSONL object
        ldp_json = {
            "meta": "LDP_Definition",
            "PROJ_String_Decimal": LDP_DEF,
            "PROJ_String_DMS": LDP_DEF_
        }
        # ensure_ascii=False ensures correct printing of ° and ′
        print(json.dumps(ldp_json, ensure_ascii=False))
        
        WKT = self.DATA.LDP_CRS.to_wkt( pretty=True )
        
        # Save WKT locally inside province output directory
        with open( self.RESULT / f'{self.STEM}_CRS.WKT', 'w' ) as f:
            f.write( WKT+'\n' )
            
        if self.DATA.LDP[0]=='TM':
            cm_sp = LineString( [ [ parm['lon_0'], self.dfPP.lat.min() ],
                                  [ parm['lon_0'], self.dfPP.lat.max() ] ] )
        elif self.DATA.LDP[0]=='LCC':
            cm_sp = LineString( [ [ self.dfPP.lng.min(), parm['lat_0'] ],
                                  [ self.dfPP.lng.max(), parm['lat_0'] ] ] )
        
        self.dfCMSP = gpd.GeoDataFrame( 
                {'geometry':[ scale(cm_sp,xfact=1.25,yfact=1.25,origin='centroid'),] },
                                 crs='EPSG:4326' )

    def Plot_Definition(self): 
        # 1. Grab the full dataset for export
        gdf_all = self.dfPP.copy()

        # 2. Save ALL points to the output GPKG
        DEF_GPKG = Path( self.RESULT / f'{self.STEM}.gpkg' )
        print( f'Writing definition GPKG : {DEF_GPKG} ...' ) 
        if DEF_GPKG.exists(): DEF_GPKG.unlink()   # delete file
        self.dfCMSP.to_file( DEF_GPKG, driver='GPKG', layer='CM_SP' )
        gdf_all.to_file( DEF_GPKG, driver='GPKG', layer='Point' )

        # 3. Apply thinning strictly for visual plotting efficiency
        gdf_pt = self.Spatial_Thinning(gdf_all, decimals=2)

        # 4. Recalculate plotting coordinates on the THINNED dataset
        ldp_proj = pyproj.Proj(self.LDP_PROJ_STRING)
        gdf_pt['LDP_E'], gdf_pt['LDP_N'] = ldp_proj(
            pd.to_numeric(gdf_pt['lng'], errors='raise').to_numpy(),
            pd.to_numeric(gdf_pt['lat'], errors='raise').to_numpy()
        )

        fig, ax = plt.subplots(figsize=(7, 7))
        
        # The scale is now -100 to +100 (range of 200). We normalize this to fractions between 0.0 and 1.0.
        color_stops = [
            (0.0, "darkred"),   # -100
            (0.1, "darkred"),   # -80
            (0.2, "red"),       # -60
            (0.3, "yellow"),    # -40
            (0.4, "green"),     # -20
            (0.5, "green"),     #   0
            (0.6, "green"),     # +20
            (0.7, "yellow"),    # +40
            (0.8, "red"),       # +60
            (0.9, "darkred"),   # +80
            (1.0, "darkred")    # +100
        ]
        cmap = mcolors.LinearSegmentedColormap.from_list("csf_map", color_stops)
        
        # Values beyond -100 and +100 will remain dark red
        cmap.set_under("darkred")
        cmap.set_over("darkred")
        
        # Plot points based on CSF_ppm for continuous shading
        sc = ax.scatter(
            gdf_pt['LDP_E'], gdf_pt['LDP_N'],
            c=gdf_pt['CSF_ppm'],
            cmap=cmap,
            vmin=-100, vmax=100,     # Extended limits
            s=55,                    # Increased size for overlapping
            marker='s',              # Square markers to eliminate white gaps
            alpha=1.0,               
            edgecolors='none',       
            antialiased=False,       # Prevents faint grid lines between squares
            zorder=5
        )

        # --- Add CM / SP Line and Label ---
        try:
            # Transform to LDP coordinates directly using GeoPandas to_crs
            dfCMSP_ldp = self.dfCMSP.to_crs(self.LDP_PROJ_STRING)
            # Plot the line (thick, black, 50% opacity, dotted) using GeoPandas
            dfCMSP_ldp.plot(ax=ax, color="black", ls=':', lw=3, alpha=0.5, zorder=1000)
            
            # Extract centroid from the projected geometry to find the middle
            cmsp_geom_ldp = dfCMSP_ldp.geometry.iloc[0]
            mid_e = cmsp_geom_ldp.centroid.x
            mid_n = cmsp_geom_ldp.centroid.y
            
            # Extract parameters directly from PROJ definition
            parm = self.DATA.LDP_CRS.to_dict()
            
            # Format the text and place it at the middle
            if self.DATA.LDP[0] == 'TM':
                ll_dm = dd2DM(parm['lon_0'])
            elif self.DATA.LDP[0] == 'LCC':
                lat_dm = dd2DM(parm['lat_0'])
                lon_dm = dd2DM(parm['lon_0'])
                ll_dm = f"{lat_dm}, {lon_dm}"
                
            bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.8)
            
            ax.text(mid_e, mid_n, ll_dm, fontsize=12,
                    fontweight='bold', color='black', ha='center', va='center',
                    bbox=bbox_props, zorder=1100)
        except Exception:
            pass # Failsafe in case of geometry errors
        # ----------------------------------

        # Color bar to the right with custom ticks and extended labels
        cbar = fig.colorbar(sc, ax=ax, extend='both', fraction=0.046, pad=0.04)
        cbar.set_ticks([-100, -80, -60, -40, -20, 0, 20, 40, 60, 80, 100])
        cbar.set_ticklabels(['-100', '-80', '-60', '-40', '-20 ppm', '0', '+20 ppm', '+40', '+60', '+80', '+100'])
        cbar.set_label('CSF_ppm')
        # -----------------------------
        
        ax.set_aspect('equal')

        # --- Force Equal Tick Intervals ---
        # Calculate the automatic interval of the X-axis and apply it to both
        x_spacing = np.diff(ax.get_xticks())[0]
        ax.xaxis.set_major_locator(ticker.MultipleLocator(x_spacing))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(x_spacing))
        
        # --- Add Thousand Separators to Axis Labels (Ticks) ---
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        # ----------------------------------
        
        ax.grid(True, color='black', alpha=0.5)
        ax.set_xlabel('LDP_E (m)')
        ax.set_ylabel('LDP_N (m)')
        plt.xticks(rotation=90)

        hasc_1 = self.PROV_CODE
        if 'HASC_1' in gdf_pt.columns:
            values = gdf_pt['HASC_1'].dropna()
            if not values.empty:
                hasc_1 = str(values.iloc[0])

        name_1 = ''
        if 'NAME_1' in gdf_pt.columns:
            values = gdf_pt['NAME_1'].dropna()
            if not values.empty:
                name_1 = str(values.iloc[0])

        province_title = f'{hasc_1} : {name_1}' if name_1 else hasc_1
        part1, part2 = str(self.DATA.LDP_CRS).split("+x_0=", 1)
        title = part1.strip() + "\n" + "+x_0=" + part2.strip()
        plt.title(province_title + "\n" + title, fontsize=9)
        
        DEF_PLT = Path( self.RESULT / f'{self.STEM}.svg' )
        print( f'Writing definition plot : {DEF_PLT}...')
        
        # 1. Adjust internal padding to prevent overlap
        plt.tight_layout() 
        
        # 2. Force the saved canvas to wrap all elements tightly
        plt.savefig( DEF_PLT, bbox_inches='tight' ) 
        
        # Optional but recommended: clear the current figure from memory 
        # to prevent elements from leaking into the next iteration of the loop
        plt.close(fig)

    def Print_Summary(self):
        print(f"{f' LDP {self.DATA.LDP[0]} ':=^80}")
        centr = MultiPoint(self.dfPP.geometry).centroid
        print( f'@ Centroid @     <lng={dd2DM(centr.x)}>    <lat={dd2DM(centr.y)}>' )
        msl = self.dfPP.MSL.describe()
        csf = self.dfPP.CSF_ppm.describe()
        print( f'Offset Projection Plane = {self.DATA.OFFSET_PP[0]:+.1f} m. <{self.DATA.OFFSET_PP[1]}>' )
        print( f'Designed Project Plane : hPP={self.HAE_PP:+.2f} m. / MSL={self.MSL_PP:+.2f} m.'\
               f' tied to k0 = {self.k0:.6f}' )
        print( f'Points CSF min/mean/max [ppm] : {csf["min"]:+.1f} / {csf["mean"]:+.1f} / {csf["max"]:+.1f}'  ) 
        print( f'Points MSL min/mean/max [m.]  : {msl["min"]:+.1f} / {msl["mean"]:+.1f} / {msl["max"]:+.1f}' ) 
        min_max = self.dfPP[['LDP_E', 'LDP_N']].agg(['min','max'])
        min_max.loc['diff'] = min_max.iloc[1]-min_max.iloc[0]
        print( min_max.to_markdown(floatfmt=',.3f' ) )

    def Print_CSFppm(self):
        print(f"{' CSF_ppm Distribution ':=^80}")
        COLS = ['Point', 'lng', 'lat', 'MSL', 'CSF_ppm', 'LDP_E', 'LDP_N']
        FMT = [ None, None, ',.6f', ',.6f', '+,.1f', '+,.1f', ',.3f', ',.3f', ] 
        print( self.dfPP[COLS].to_markdown( floatfmt=FMT ) )

    def Print_UTM(self):
        epsg = self.dfPP.estimate_utm_crs().to_epsg()
        zn = str(epsg)[-2:]
        dfUTM = self.dfPP.to_crs( epsg )
        def makeUTM(row):
            utm_e = row.geometry.x ; utm_n = row.geometry.y 
            return utm_e,utm_n
        dfUTM[[f'UTM{zn}_E',f'UTM{zn}_N']] = dfUTM.apply( makeUTM, axis=1, result_type='expand' )
        FMT = [ None, ',.3f', ',.3f', '.3f', ',.3f', ',.3f' ]
        print( dfUTM[['Point', f'UTM{zn}_E', f'UTM{zn}_N', 'MSL', 'LDP_E', 'LDP_N' ]].to_markdown(
                     index=False , floatfmt=FMT ) )

    def DoTransformation(self, TOML_SECT):
        FR_PRJ = pyproj.CRS( self.DATA[TOML_SECT]['PROJ'] )
        TO_PRJ = self.DATA.LDP_CRS
        FR_COL = ['UTM_E','UTM_N','UTM_Elev']
        TO_COL = ['LDP_E','LDP_N','LDP_Elev']
        if TOML_SECT=='UTM_LDP':
            pass
        elif TOML_SECT=='LDP_UTM':
            FR_PRJ,TO_PRJ = TO_PRJ,FR_PRJ
            FR_COL,TO_COL = TO_COL,FR_COL
        
        del self.DATA[TOML_SECT]['PROJ']
        pnts = self.DATA[TOML_SECT]
        df = pd.DataFrame.from_dict( pnts, orient='index', columns=FR_COL )
        TR = pyproj.Transformer.from_crs( FR_PRJ, TO_PRJ )
        
        def Transf( row, TR, FR_COL, TO_COL ):
            E,N = TR.transform( row[FR_COL[0]], row[FR_COL[1]] )
            return E, N, row[FR_COL[2] ]
            
        df[TO_COL] = df.apply( Transf, axis=1, result_type='expand',
                                args=(TR,FR_COL,TO_COL) )
        return df

    def Print_Coverage(self):
        if 'POP' not in self.dfPP.columns:
            return
            
        df_valid = self.dfPP[(self.dfPP.CSF_ppm >= -20) & (self.dfPP.CSF_ppm <= 20)]
        valid_points = len(df_valid)
        valid_pop = df_valid['POP'].sum()
        
        pt_pct = (valid_points / self.INITIAL_POINTS * 100) if self.INITIAL_POINTS > 0 else 0.0
        pop_pct = (valid_pop / self.INITIAL_POP * 100) if self.INITIAL_POP > 0 else 0.0
        
        if valid_points > 0:
            csf_min = df_valid['CSF_ppm'].min()
            csf_mean = df_valid['CSF_ppm'].mean()
            csf_max = df_valid['CSF_ppm'].max()
        else:
            csf_min = csf_mean = csf_max = 0.0
        
        # Transform Population Coverage Analysis table into JSONL dictionary
        cov_dict = {
            "meta": "Coverage_Analysis",
            "Province": self.PROV_CODE,
            "Total_Pts": int(self.INITIAL_POINTS),
            "Valid_Pts": int(valid_points),
            "Pt_Coverage(%)": round(float(pt_pct), 2),
            "Total_POP": float(self.INITIAL_POP),
            "Valid_POP": float(valid_pop),
            "POP_Coverage(%)": round(float(pop_pct), 2),
            "CSF_Lower_ppm": round(float(csf_min), 1),
            "CSF_Mean_ppm": round(float(csf_mean), 1),
            "CSF_Upper_ppm": round(float(csf_max), 1)
        }
        # ensure_ascii=False ensures correct printing
        print(json.dumps(cov_dict, ensure_ascii=False))


###########################################################################
# CLI Processing
###########################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser( prog='constr_LDP',
                description='Calculate CSF from points defined by GPKG, CSV or single point and generate LDP grids per province.',
                epilog='P.Santitamnont ( phisan.chula@gmail.com ) July,2024')
    
    parser.add_argument('province', help="HASC_1 province code (e.g., TH.CM)")
    parser.add_argument('-t', '--toml', default='PROV_LDP.toml', help="TOML file containing province configuration data")
    parser.add_argument('-b', '--bypass', action='store_true', help="Bypass MSL outliers filtering")
    parser.add_argument('-c', '--csf', action='store_true', help='show CSF table') 
    parser.add_argument('-u', '--utm', action='store_true', help='show UTM-LDP table')
    parser.add_argument('-o', '--OFFSET_PP', type=int, help='offset for project plane')
    args = parser.parse_args()

    # 1. Read the entire TOML file and isolate the requested province
    with open(args.toml, "rb") as f:
        config_data = tomllib.load(f)
        
    if args.province not in config_data:
        print(f"ERROR: Configuration for '{args.province}' not found in {args.toml}.")
        sys.exit(1)
        
    prov_data = config_data[args.province]

    # 2. Run the workflow for the selected province
    ldp = LDP_Design(args, args.province, prov_data)
    ldp.Print_Summary()

    ldp.Print_Defintion()
    ldp.Plot_Definition()

    if args.csf: 
        ldp.Print_CSFppm()

    if args.utm: 
        ldp.Print_UTM()

    # Output the requested table at the very last line
    ldp.Print_Coverage()
