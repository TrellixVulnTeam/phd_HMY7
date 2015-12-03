import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

from matplotlib.colors import LinearSegmentedColormap


def shiftedcmap(cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
    """Offset the 'center' of a colormap.

    Useful for data with a negative min and positive max and you
    want the middle of the colormap's dynamic range to be at zero.

    Parameters
    ----------
    cmap : The matplotlib colormap to be altered
    start : Offset from lowest point in the colormap's range.
            Defaults to 0.0 (no lower ofset). Should be between
            0.0 and `midpoint`.
    midpoint : The new center of the colormap. Defaults to
               0.5 (no shift). Should be between 0.0 and 1.0. In
               general, this should be  1 - vmax/(vmax + abs(vmin))
               For example if your data range from -15.0 to +5.0 and
               you want the center of the colormap at 0.0, `midpoint`
              should be set to  1 - 5/(5 + 15)) or 0.75
    stop : Offset from highets point in the colormap's range.
           Defaults to 1.0 (no upper ofset). Should be between
           `midpoint` and 1.0.

    From http://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib  # noqa
    """
    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(start, stop, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False),
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)
        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    newcmap = LinearSegmentedColormap(name, cdict)
    plt.register_cmap(cmap=newcmap)

    return newcmap


def cochleogram(data, time, freqs, cmap=plt.cm.RdBu):
    if data.min() >= 0.0:
        cmap = plt.cm.Blues
    elif not np.allclose(data.max() + data.min(), 0, atol=1e-5):
        midpoint = np.abs(data.min()) / (data.max() - data.min())
        cmap = shiftedcmap(cmap, midpoint=midpoint)

    plt.pcolormesh(time, freqs, data.T, cmap=cmap)
    # For some reason, putting this on a log y scale is crashing MPL...
    # plt.yscale('log')
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time (ms)')
    plt.axis('tight')
    sns.despine()
    plt.colorbar()
    plt.tight_layout()


def compare(data, columns, x_keys, x_label, y_label,
            relative_to=None, group_by=None, filter_by=None,
            plot_f=sns.violinplot, **plot_args):
    data = data.copy()  # Make a copy, as we modify it

    # Make columns relative to other columns
    relative_to = [] if relative_to is None else relative_to
    for col, rel in zip(columns, relative_to):
        data[col] /= data[rel].mean()

    filter_by = [] if filter_by is None else filter_by

    extra_keys = [key for key, val in filter_by]
    extra_keys.extend(relative_to)
    if group_by is not None:
        extra_keys.append(group_by)

    if len(extra_keys) > 0:
        # Get the requested columns, and the one we're grouping by
        data = pd.concat([data[[c] + extra_keys] for c in columns],
                         keys=x_keys, names=[x_label])
        # Merge all of the columns into one
        data[y_label] = np.nan
        for c in columns:
            data[y_label].fillna(data[c], inplace=True)
            del data[c]
    else:
        # Get the requested columns (auto-merged)
        data = pd.concat([data[c] for c in columns],
                         keys=x_keys, names=[x_label]).to_frame()
        data.columns = [y_label]
    # Make the index (`x_label`) into a column
    data.reset_index(level=0, inplace=True)
    # Only take what we're filtering by
    for key, val in filter_by:
        data = data[data[key] == val]

    # Go Seaborn!
    plot_f(x=x_label, y=y_label, hue=group_by, data=data, **plot_args)
    sns.despine()
