import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def draw_ldp_infographic():
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 1. Define the spatial grid (1000m x 1000m area)
    x = np.linspace(-200, 200, 50)
    y = np.linspace(-500, 500, 50)
    X, Y = np.meshgrid(x, y)

    # 2. Ellipsoid Surface (Exaggerated curvature for oblique visualization)
    R_exaggerated = 150000
    Z_ellps = -(X**2 + Y**2) / (2 * R_exaggerated)
    
    # Plot Ellipsoid
    ax.plot_surface(X, Y, Z_ellps, alpha=0.3, color='royalblue', edgecolor='none')
    ax.text(-200, -500, np.min(Z_ellps), 'Ellipsoid Surface', color='darkblue', fontsize=12, fontweight='bold')

    # 3. Ground Surface (Ellipsoid + height 'h' + slight terrain noise)
    h = 50  # Separation height in meters (scaled for visual clarity)
    terrain_noise = np.sin(X/50) * np.cos(Y/150) * 5
    Z_ground = Z_ellps + h + terrain_noise
    
    # Plot Ground
    ax.plot_surface(X, Y, Z_ground, alpha=0.6, color='forestgreen', edgecolor='none')
    ax.text(-200, -500, np.min(Z_ground) + 10, 'Ground Surface', color='darkgreen', fontsize=12, fontweight='bold')

    # 4. The 1,000.000m Exact Line on Ground
    line_x = np.zeros(100)
    line_y = np.linspace(-500, 500, 100)
    line_z = -(line_x**2 + line_y**2) / (2 * R_exaggerated) + h + (np.sin(line_x/50) * np.cos(line_y/150) * 5)
    
    ax.plot(line_x, line_y, line_z, color='red', linewidth=5, 
            zorder=0, alpha=0.7)
    
    # Text updated and aligned along the Y-axis to run parallel to the red line
    ax.text(20, -400, np.max(line_z) + 5, 'L=1,000.000 m ; Az = 0°', zdir='y', zorder=99,
            color='red', fontsize=14, fontweight='bold')
            
    # P1 and P2 markers at both ends of the line
    ax.text(0, -500, line_z[0] + 5, 'P1', zorder=99, color='darkred', fontsize=14, fontweight='bold')
    ax.text(0, 500, line_z[-1] + 5, 'P2', zorder=99, color='darkred', fontsize=14, fontweight='bold')

    # 5. Separation Indicators (h)
    # Draw vertical dashed lines connecting Ellipsoid to Ground at the ends and center
    for y_pos in [-500, 0, 500]:
        z_bottom = -(0**2 + y_pos**2) / (2 * R_exaggerated)
        z_top = z_bottom + h + (np.sin(0/50) * np.cos(y_pos/150) * 5)
        ax.plot([0, 0], [y_pos, y_pos], [z_bottom, z_top], color='black', linestyle='--', linewidth=1.5)
    
    # Label the height 'h' at the center
    z_mid_bottom = 0
    z_mid_top = h + 5
    ax.text(10, 0, (z_mid_bottom + z_mid_top) / 2, 'h', color='black', fontsize=12)

    # 6. North Arrow / Compass
    # Placed in the top corner of the extent
    arrow_x, arrow_y, arrow_z = -150, 350, np.max(Z_ground) + 20
    ax.quiver(arrow_x, arrow_y, arrow_z, 0, 150, 0, color='black', linewidth=3, arrow_length_ratio=0.3)
    ax.text(arrow_x, arrow_y + 180, arrow_z, 'N', color='black', fontsize=16, fontweight='bold')

    # Formatting the Oblique View
    ax.view_init(elev=20, azim=-60)  # Classic oblique surveying angle
    ax.set_box_aspect([1, 2.5, 0.5]) # Stretch the Y axis to emphasize the 1km line
    ax.axis('off')                   # Hide the matplotlib grid for a clean infographic look
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_ldp_infographic()
