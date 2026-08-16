from qgis.core import (
    QgsProject, QgsFeatureRequest, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
)

# Target the exact layer loaded in your project
layer_name = "gadm41_THA — ADM_ADM_2"
layers = QgsProject.instance().mapLayersByName(layer_name)

if layers:
    layer = layers[0]
    
    # Expression to find all Chiang Mai districts (TH.CM.XX)
    expression = "HASC_2 LIKE 'TH.CM.%'"
    request = layer.getFeatures(QgsFeatureRequest().setFilterExpression(expression))
    
    district_codes = []
    
    print(f"-> Scanning layer '{layer_name}' for Chiang Mai districts...")
    for feat in request:
        hasc2 = feat["HASC_2"]  # e.g., "TH.CM.MR"
        xx = hasc2.split('.')[-1]  # Extracts just the "XX" suffix (e.g., "MR")
        name2 = feat["NAME_2"] if "NAME_2" in feat.fields().names() else "N/A"
        
        district_codes.append((hasc2, xx, name2))
        print(f"   - Found HASC_2: {hasc2} | Suffix (XX): {xx} | Name: {name2}")
        
    print(f"\n-> [SUCCESS] Total Chiang Mai districts found: {len(district_codes)}")
    
    # Select them and enable labels automatically
    if len(district_codes) > 0:
        layer.selectByExpression(expression)
        
        # Setup Labeling to display the XX code or full HASC_2
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "HASC_2"
        label_settings.enabled = True
        
        text_format = label_settings.format()
        text_format.setSize(9)
        label_settings.setFormat(text_format)

        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()
        
        # Zoom map canvas to the selection
        iface.mapCanvas().zoomToSelected(layer)
        print("-> [SUCCESS] Selected all TH.CM.XX districts and applied labels on map.")
else:
    print(f"-> [ERROR] Layer '{layer_name}' not found in the project.")