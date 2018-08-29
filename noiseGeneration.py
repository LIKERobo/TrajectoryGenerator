import numpy as np

def add_simple_noise(trace_x, trace_y, noise):
    """Adds independent noise to traces.

    Parameters
    ----------
    trace_x, trace_y : *array_like*/*list*
        Lists containing the individual values of the trace.
    noise : *float*
        Standard deviation of the gaussion noise.

    Returns
    -------
    xn, yn : *list*/*list*
        Lists containing the noisy trace-data.

    """
    assert (len(trace_x) > 0) and \
        (len(trace_y) > 0) and \
        (len(trace_x) == len(trace_y))
    if isinstance(trace_x, list):
        xn = (trace_x + np.random.normal(0, noise, \
                                         len(trace_x)).astype(int)).tolist()
        yn = (trace_y + np.random.normal(0, noise, \
                                         len(trace_y)).astype(int)).tolist()
    elif isinstance(trace_x, np.ndarray):
        xn = (trace_x + np.random.normal(0, noise, \
                                         trace_x.shape).astype(int)).tolist()
        yn = (trace_y + np.random.normal(0, noise, \
                                         trace_y.shape).astype(int)).tolist()
    else:
        raise TypeError("Invalid trace-types:",type(trace_x),",",type(trace_y))
    return xn, yn
    

def add_complex_noise(trace_x, trace_y, cov):
    """Adds noise from multivariate gaussian to traces.

    TODO: Add Gui-Option for Covariance.

    Parameters
    ----------
    trace_x, trace_y : *array_like*/*list*
        Lists containing the individual values of the trace.
    cov : *2x2-array*
        Covariance matrix of the distribution. It must be symmetric and
        positive-semidefinite for proper sampling.

    Returns
    -------
    xn, yn : *list*/*list*
        Lists containing the noisy trace-data.
    """
    assert (len(trace_x) > 0) and (len(trace_y) > 0) and (len(trace_x) == len(trace_y))
    assert np.all(np.linalg.eigvals(cov) >= 0)
    xn, yn = np.random.multivariate_normal([0,0], cov, len(trace_x)).T
    xn = (trace_x + xn).astype(int).tolist()
    yn = (trace_y + yn).astype(int).tolist()
    return xn, yn
