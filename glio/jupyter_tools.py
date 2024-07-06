"""Jupyter stuffs"""
from typing import TYPE_CHECKING, Optional
from collections.abc import Sequence
import sys, gc, traceback, torch

if TYPE_CHECKING:
    def get_ipython(): pass

def clean_ipython_hist():
    """    Clean up IPython history by removing input history and variables.

    This function cleans up the IPython history by removing input history
    and variables stored in the user namespace.  Source: ... (idk but I
    found it from fastai)
    """
    # Code in this function mainly copied from IPython source
    if  'get_ipython' not in globals(): return
    ip = get_ipython() # type: ignore #pylint:disable=E1111
    user_ns = ip.user_ns # type:ignore
    ip.displayhook.flush()# type:ignore
    pc = ip.displayhook.prompt_count + 1# type:ignore
    for n in range(1, pc): user_ns.pop('_i'+repr(n),None)
    user_ns.update(dict(_i='',_ii='',_iii=''))
    hm = ip.history_manager# type:ignore
    hm.input_hist_parsed[:] = [''] * pc
    hm.input_hist_raw[:] = [''] * pc
    hm._i = hm._ii = hm._iii = hm._i00 =  ''#pylint:disable=W0212

def clean_tb():
    """Clean up the traceback information stored in the sys module.

    This function clears the frames from the last traceback and removes the
    last_type, last_value, and last_traceback attributes from the sys module
    if they exist.

    Note:
        This function is based on the implementation by Piotr Czapla.
    """

    # h/t Piotr Czapla
    if hasattr(sys, 'last_traceback'):
        traceback.clear_frames(sys.last_traceback)
        delattr(sys, 'last_traceback')
    if hasattr(sys, 'last_type'): delattr(sys, 'last_type')
    if hasattr(sys, 'last_value'): delattr(sys, 'last_value')
def clean_mem():
    """Clean memory by clearing traceback, IPython history, and garbage
    collection.

    This function cleans the traceback, IPython history, and performs
    garbage collection twice. It also empties the CUDA memory cache if
    PyTorch is being used.
    """

    clean_tb()
    clean_ipython_hist()
    gc.collect()
    gc.collect()
    torch.cuda.empty_cache()



def is_jupyter():
    """Check if the code is running in a Jupyter environment.

    This function checks the type of the IPython shell to determine if it is
    running in a Jupyter environment.

    Returns:
        str: 'jupyter' if running in Jupyter, True if running in a terminal, False
            otherwise.
    """

    try:
        ipy_str = str(type(get_ipython()))
        if 'zmqshell' in ipy_str:
            return 'jupyter'
        if 'terminal' in ipy_str:
            return True
    except:# type:ignore #pylint:disable=W0702
        return False

def isnotebook():
    """Check if the code is running in a Jupyter notebook or IPython terminal.

    This function checks the type of IPython shell to determine if the code
    is running in a Jupyter notebook or IPython terminal.

    Returns:
        bool: True if running in a Jupyter notebook or qtconsole, False otherwise.
    """

    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

def markdown_if_jupyter(string):
    """Display markdown string if running in a Jupyter environment.

    This function checks if the code is running in a Jupyter environment. If
    it is, it displays the provided markdown string.

    Args:
        string (str): The markdown string to display.

    Returns:
        None: If running in a Jupyter environment, the markdown string is displayed.
            Otherwise, returns the input string.
    """

    if is_jupyter():
        from IPython.display import Markdown, display
        display(Markdown(string))
        return None
    else: return string

def show_slices(sliceable):
    """Display interactive slices of a multidimensional array.

    This function displays interactive slices of a multidimensional array
    using ipywidgets and qimshow.

    Args:
        sliceable (array): A multidimensional array to display slices of.
    """

    from .plot import qimshow
    from .python_tools import shape, ndims
    from ipywidgets import interact

    kwargs = {f"s{i}":(0,v-1) for i,v in enumerate(shape(sliceable)[:-2])}
    stats = dict(orig_shape = shape(sliceable))
    def f(color, **kwargs):
        """Perform a series of operations on a sliceable object based on the
        provided color and keyword arguments.

        Args:
            color (bool): A boolean value indicating whether to use color.
            **kwargs: Additional keyword arguments to specify operations.

        Returns:
            dict: A dictionary containing statistics and information about the processed
                view.
        """

        nonlocal sliceable
        view = sliceable
        for v in list(kwargs.values())[:-1] if color else kwargs.values():
            view = view[v]
        qimshow(view, cmap="gray")
        return dict(**stats, view_shape=view.shape, view_min = view.min(), view_max = view.max())
    return interact(f, color=False, **kwargs)

def show_slices_arr(sliceable):
    """Display interactive slices of a sliceable object.

    This function takes a sliceable object, such as an image or a volume,
    and displays interactive slices using ipywidgets.

    Args:
        sliceable: A sliceable object that can be converted to a numpy array for display.
    """

    from .plot import qimshow
    from ipywidgets import interact
    import numpy as np
    if hasattr(sliceable, "detach"): sliceable = sliceable.detach().cpu()
    sliceable = np.array(sliceable)
    shape = sliceable.shape
    kwargs = {f"s{i}":(0, max(shape)-1) for i in range(len(shape)-2)}
    permute = " ".join([str(i) for i in range(len(kwargs)+2)])
    stats = dict(orig_shape = sliceable.shape, dtype=sliceable.dtype, min=sliceable.min(), max=sliceable.max(), mean=sliceable.mean(), std=sliceable.std())
    def f(color, permute:str,**kwargs):
        """Perform operations on a sliceable array based on color and permutation.

        This function takes a sliceable array and performs operations based on
        the color flag and permutation provided. It transposes the sliceable
        array based on the permutation values, iterates through the kwargs
        values, and updates the view. Finally, it displays the view using
        qimshow function and returns a dictionary containing statistics and the
        shape of the view.

        Args:
            color (bool): A flag indicating whether to consider color.
            permute (str): A string containing space-separated permutation values.
            **kwargs: Additional keyword arguments.

        Returns:
            dict: A dictionary containing statistics and the shape of the view.

        Note:
            The 'sliceable' variable is assumed to be defined in the outer scope.
        """

        nonlocal sliceable
        view = np.transpose(sliceable, [int(i) for i in permute.split(" ")])
        for v in list(kwargs.values())[:-1] if color else kwargs.values():
            view = view[v]
        qimshow(view, cmap="gray")
        return dict(**stats, view_shape=view.shape)
    return interact(f, permute=permute,color=False, **kwargs)


def sequence_to_table(s:Sequence, keys:Optional[Sequence] = None, keys_from_s = False, transpose=False):
    """Display a sequence as a table in Jupyter notebook using Markdown format.

    Args:
        s (Sequence): The input sequence to be displayed as a table.
        keys (Optional[Sequence]): Optional keys for the table columns.
        keys_from_s (bool): Flag to indicate whether keys should be extracted from the input
            sequence.
        transpose (bool): Flag to indicate if the table should be transposed.


    Note:
        This function requires IPython and python_tools module to be imported.
    """

    from .python_tools import sequence_to_markdown
    md = sequence_to_markdown(s, keys=keys, keys_from_s=keys_from_s, transpose=transpose)
    from IPython.display import Markdown, display
    display(Markdown(md))