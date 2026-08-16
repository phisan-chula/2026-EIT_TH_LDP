from qgis.core import (
    QgsProject,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsSymbol,
    QgsRendererRange,
    QgsGraduatedSymbolRenderer,
    Qgis  
)
from PyQt5.QtGui import QColor
from qgis.utils import iface

def style_ldp_points():
    project = QgsProject.instance()
    layers = project.mapLayers().values()
    
    # 1. Find the target Point layer
    point_layer = None
    for layer in layers:
        if "Point" in layer.name():
            point_layer = layer
            break

    if not point_layer:
        print("Error: Could not find a layer with 'Point' in its name.")
        return

    print(f"Applying styles to: {point_layer.name()}")

    # 2. Configure Labeling (CSF_ppm with 0 decimal points)
    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = 'round("CSF_ppm", 0)'
    label_settings.isExpression = True

    text_format = QgsTextFormat()
    text_format.setSize(9)
    text_format.setColor(QColor("black"))
    
    buffer_settings = text_format.buffer()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(0.7)
    buffer_settings.setColor(QColor("white"))
    text_format.setBuffer(buffer_settings)
    
    label_settings.setFormat(text_format)

    label_settings.placement = Qgis.LabelPlacement.OverPoint
    
    try:
        label_settings.quadOffset = Qgis.LabelQuadrantPosition.AboveRight
    except AttributeError:
        label_settings.quadOffset = QgsPalLayerSettings.QuadrantAboveRight
        
    label_settings.xOffset = 1.5
    label_settings.yOffset = 1.5

    labeling = QgsVectorLayerSimpleLabeling(label_settings)
    point_layer.setLabelsEnabled(True)
    point_layer.setLabeling(labeling)

    # 3. Configure Symbology (Graduated colors for +/- 20 ppm)
    ranges_data = [
        (-99999, -20, '< -20 ppm (Outside)', QColor(139, 0, 0)),     
        (-20, -10, '-20 to -10 ppm', QColor(255, 69, 0)),            
        (-10, -3, '-10 to -3 ppm', QColor(255, 215, 0)),             
        (-3, 3, 'Near Zero (-3 to +3)', QColor(0, 150, 0)),          
        (3, 10, '+3 to +10 ppm', QColor(255, 215, 0)),               
        (10, 20, '+10 to +20 ppm', QColor(255, 69, 0)),              
        (20, 99999, '> +20 ppm (Outside)', QColor(139, 0, 0))        
    ]

    renderer_ranges = []
    for min_val, max_val, label, color in ranges_data:
        symbol = QgsSymbol.defaultSymbol(point_layer.geometryType())
        symbol.setColor(color)
        symbol.setSize(3.0) 
        
        symbol.symbolLayer(0).setStrokeColor(QColor("black"))
        symbol.symbolLayer(0).setStrokeWidth(0.2)
        
        range_obj = QgsRendererRange(min_val, max_val, symbol, label)
        renderer_ranges.append(range_obj)

    renderer = QgsGraduatedSymbolRenderer("CSF_ppm", renderer_ranges)
    renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
    
    point_layer.setRenderer(renderer)
    
    # 4. Refresh map canvas and layer tree
    point_layer.triggerRepaint()
    
    # THE FIX IS HERE: pass the layer ID instead of the layer object
    iface.layerTreeView().refreshLayerSymbology(point_layer.id())
    
    print("Styling complete! Check your map canvas and layers panel.")

style_ldp_points()