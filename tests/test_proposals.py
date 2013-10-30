"""
Test proposal objects in proposals.py
"""

__author__ = 'Brandon C. Kelly'

import numpy as np
from scipy import stats
import proposals


def test_NormalProposal():
    """
    Test the normal proposal object.
    """
    sigma = np.random.chisquare(10) / 10.0
    mu = np.random.standard_cauchy()

    NormProposal = proposals.NormalProposal(sigma)

    ndraws = 100000

    x = np.empty(ndraws)
    for i in xrange(ndraws):
        x[i] = NormProposal.draw(mu)

    x0 = np.random.normal(mu, sigma, ndraws)

    # Do K-S test to verify that the distribution of proposals from the NormalProposal object
    # have the same distribution as values drawn from numpy.random.normal.
    ks_statistic, significance = stats.ks_2samp(x, x0)

    assert significance > 1e-3


def test_MultiNormalProposal():
    """
    Test the multivariate normal proposal object.
    """
    # Make a positive-definite symmetric array
    corr = np.array([[1.0, 0.3, -0.5], [0.3, 1.0, 0.54], [-0.5, 0.54, 1.0]])
    sigma = np.array([[2.3, 0.0, 0.0], [0.0, 0.45, 0.0], [0.0, 0.0, 13.4]])
    covar0 = sigma.dot(corr.dot(sigma))

    # Randomly generate the proposal covariance matrix
    xx = np.random.multivariate_normal(np.zeros(3), covar0, 10)
    covar = np.cov(xx.T)

    # Randomly generate the centroid of the proposals
    mu = np.random.standard_cauchy(3)

    MultiProp = proposals.MultiNormalProposal(covar)

    ndraws = 100000
    xx = np.zeros((ndraws, 3))
    for i in xrange(ndraws):
        xx[i, :] = MultiProp.draw(mu)

    sample_mean = xx.mean(axis=0)
    sample_covar = np.cov(xx, rowvar=0)

    chisqr = ndraws * np.dot(sample_mean - mu, np.linalg.inv(covar).dot(sample_mean - mu))

    # Do chi-square test to make sure that the standardized values generated by the proposal object are consistent
    # with a multivariate normal distribution with mean mu and covariance covar.
    significance = stats.chisqprob(chisqr, 3)

    assert significance > 1e-3

    # Make sure maximum difference between the true and sample covariance matrices are within 3-sigma
    varmat = np.zeros_like(covar)
    for i in xrange(3):
        for j in xrange(3):
            varmat[i, j] = (covar[i, j] ** 2 + covar[i, i] * covar[j, j]) / ndraws

    covar_diff = np.abs(covar - sample_covar) / np.sqrt(varmat)
    assert covar_diff.max() < 3.0


def test_LogNormalProposal():
    """
    Test the log-normal proposal object.
    """
    sigma = np.random.chisquare(10) / 10.0
    mu = np.random.standard_cauchy()

    LogNormProp = proposals.LogNormalProposal(sigma)

    ndraws = 100000

    x = np.empty(ndraws)
    for i in xrange(ndraws):
        x[i] = LogNormProp.draw(np.exp(mu))

    x0 = np.random.lognormal(mu, sigma, ndraws)

    # Do K-S test to verify that the distribution of proposals from the NormalProposal object
    # have the same distribution as values drawn from numpy.random.normal.
    ks_statistic, significance = stats.ks_2samp(x, x0)

    assert significance > 1e-3

    # Test LogNormalProposal.LogDensity
    proposed_value = x[0]
    current_value = np.exp(mu)

    logdens_forward = LogNormProp.logdensity(proposed_value, current_value)
    logdens_backward = LogNormProp.logdensity(current_value, proposed_value)

    lograt = logdens_forward - logdens_backward

    logdens_forward0 = stats.lognorm.logpdf(proposed_value, sigma, scale=current_value)
    logdens_backward0 = stats.lognorm.logpdf(current_value, sigma, scale=proposed_value)

    lograt0 = logdens_forward0 - logdens_backward0

    logdens_diff = abs(lograt - lograt0) / lograt0

    assert logdens_diff < 1e-8


def test_StudentProposal():
    """
    Test the student's t proposal object.
    """
    sigma = np.random.chisquare(10) / 10.0
    mu = np.random.standard_cauchy()
    dof = 4

    tProp = proposals.StudentProposal(dof, sigma)

    ndraws = 100000

    x = np.empty(ndraws)
    for i in xrange(ndraws):
        x[i] = tProp.draw(mu)

    x0 = mu + sigma * np.random.standard_t(dof, ndraws)

    # Do K-S test to verify that the distribution of proposals from the NormalProposal object
    # have the same distribution as values drawn from numpy.random.normal.
    ks_statistic, significance = stats.ks_2samp(x, x0)

    assert significance > 1e-3


if __name__ == "__main__":
    test_NormalProposal()
    test_StudentProposal()
    test_LogNormalProposal()
    test_MultiNormalProposal()

    print "All tests passed"