import traceback

import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.spatial import Voronoi
from sklearn.neighbors import KDTree

mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42


#####################
# Main-plot function


def plot_cvt_map(
    archive_file,
    centroids_file,
    save_path,
    case_name,
    min_fit=False,
    max_fit=False,
    verbose=False,
    colormap=mpl.cm.viridis,
    bd_axis=["Leg 1 proportion of contact-time", "Leg 2 proportion of contact-time"],
    ryan=False,
    plot_species=False
):
    """
    Plot a cvt archive.
    Inputs:
        - archive_file {str} - file containing the archive
        - centroids_file {str} - file containing the corresponding centroids coordinates
        - save_path {str} - path to save the resultant archive
        - case_name {str} - template of filename to save the archive
        - min_fit {float} - min fitness value for colormap
        - max_fit {float} - max fitness value for colormap
        - verbose {bool}
        - colormap {mpl.colormap}
    Outputs: {bool} - has the archive succesfully been ploted
    """

    # Read file
    centroids = load_centroids(centroids_file)

    verbose and print("\nArchive filename : ", archive_file)
    
    if ryan:
        fit, beh = load_ryan_data(archive_file, plot_species) # fit = fit if plot_species False, species id if True
        if plot_species:
            # colormap = mpl.colors.ListedColormap(["red", "green", "orange", "yellow", "violet", "deeppink", "sienna", "black"])
            # print(plt.colormaps())
            colormap = mpl.cm.Set1
    else:
        fit, beh, _ = load_data(archive_file, centroids.shape[1], verbose=verbose)

    if len(fit) == 0:
        print("\n!!!WARNING!!! Empty archive:", archive_file, ".\n")
        return True
    if len(beh[0]) > 2:
        print("\n!!!WARNING!!! Archive has too many dimensions.")
        return False

    # Fitness range
    verbose and print(
        "Average fit : ", fit.sum() / fit.shape[0], " --- Total len : ", len(fit)
    )

    index = np.argmax(fit)
    verbose and print("Fitness max : ", max(fit), " --- Associated desc : ", beh[index])
    verbose and print("Index : ", index)

    # If no min and max fitness given, use min and max fitness of the file
    if min_fit is None:
        min_fit = min(fit)
    elif min_fit > min(fit):
        print(
            "!!!Warning!!! Fitness minimum chosen greater than actual minimum fitness:",
            min(fit),
        )
    if max_fit is None:
        max_fit = max(fit)
    elif max_fit < max(fit):
        print(
            "!!!Warning!!! Fitness maximum chosen lower than actual maximum fitness:",
            max(fit),
        )
    verbose and print("Min = {} Max = {}".format(min_fit, max_fit))

    # Set plot params
    params = {
        "axes.labelsize": 18,
        "legend.fontsize": 18,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "text.usetex": False,
        "figure.figsize": [6, 6],
        'legend.title_fontsize': 18
    }
    mpl.rcParams.update(params)

    # Plot
    fig, ax = plt.subplots(facecolor="white", edgecolor="white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set(adjustable="box", aspect="equal")
    norm = mpl.colors.Normalize(vmin=min_fit, vmax=max_fit)

    try:
        plot_cvt(ax, centroids, fit, beh, norm, colormap=colormap)
    except BaseException:
        print("\n!!!WARNING!!! Error when plotting archive")
        print(traceback.format_exc(-1))

    # Add axis name and colorbar
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel(bd_axis[0])
    ax.set_ylabel(bd_axis[1])
    
    # Defining either a color bar if not plotting species, or a legend if plotting species
    if not plot_species:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)

        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=colormap), cax=cax)
        cbar.set_label("Fitness", size=24, labelpad=5)
        cbar.ax.tick_params(labelsize=18)
    else:
        custom_lines = []
        for i in range(max_fit[0]+1):
            custom_lines.append(Line2D([0], [0], color='w', marker='s', markersize=18, markerfacecolor=colormap(norm(i/1.))))

        labels = []
        for i in range(max_fit[0]+1):
            species_id = i + 1
            labels.append(f"$z_{species_id}$")
        
        ax.legend(custom_lines, labels, title="Species", loc="center left", bbox_to_anchor=(1, 0.5))

    # Save figure
    fig.savefig(f"{save_path}/{case_name}.png", bbox_inches="tight")
    plt.close()
    return True


#####################
# Sub-plot functions


def plot_cvt(ax, centroids, fit, desc, norm, colormap=mpl.cm.viridis):
    """
    Plot each cell using polygon shapes.
    """
    # compute Voronoi tesselation
    vor = Voronoi(centroids)
    regions, vertices = voronoi_finite_polygons_2d(vor)
    kdt = KDTree(centroids, leaf_size=30, metric="euclidean")
    for region in regions:
        polygon = vertices[region]
        ax.fill(*zip(*polygon), alpha=0.5, edgecolor="black", facecolor="white", lw=1)

    k = 0
    for i in range(0, len(desc)):
        q = kdt.query([desc[i]], k=1)
        index = q[1][0][0]
        region = regions[index]
        polygon = vertices[region]
        ax.fill(*zip(*polygon), alpha=0.9, color=colormap(norm(fit[i]))[0])
        k += 1


def voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite regions.
    Source:
    https://stackoverflow.com/questions/20515554/colorize-voronoi-diagram/20678647#20678647

    Parameters
    ----------
    vor : Voronoi
        Input diagram
    radius : float, optional
        Distance to 'points at infinity'.

    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.
    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1]  # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)


#######################
# Files load functions


def load_centroids(filename):
    """Load a file."""
    points = np.loadtxt(filename)
    return points


def load_data(filename, dim, verbose=False):
    """Load a cvt archive file and transform it into a usable dataframe."""

    data = np.loadtxt(filename)

    # print("Raw data : ", data)
    verbose and print("Raw data dimension: ", data.ndim)
    if data.ndim == 1:
        if len(data) == 0:
            fit = np.array([])
            desc = np.array([])
            x = np.array([])
        else:
            fit = np.array([data[0:1]])
            desc = np.array([data[dim + 1 : 2 * dim + 1]])
            x = np.array([data[dim + 1 : 2 * dim + 1]])
    else:
        fit = data[:, 0:1]
        desc = data[:, dim + 1 : 2 * dim + 1]
        x = data[:, dim + 1 : 2 * dim + 1 :]

    print("fit", fit, type(fit), fit.shape)
    print("\n\n\n\nDESC", desc)
    print("\n\n\nx", x, type(x), x.shape)

    return fit, desc, x

import json 

def load_ryan_data(archive_file, plot_species=False):
    archive = {}

    with open(archive_file) as f:
        archive_dict = json.load(f)

    if not plot_species: # Plotting the fit value
        for item in archive_dict["items"]:
            archive[tuple(item[0])] = item[1]

        beh = np.asarray(list(archive.keys())) 
        fit = np.asarray(list(archive.values()))
        fit = np.expand_dims(fit, axis=1)
    else: # Plotting the species id
        for item in archive_dict["species_ids"]:
            archive[tuple(item[0])] = item[1]
        
        beh = np.asarray(list(archive.keys())) 
        fit = np.asarray(list(archive.values())) # Actually species id, not fit
        fit = np.expand_dims(fit, axis=1)
    
    return fit, beh
