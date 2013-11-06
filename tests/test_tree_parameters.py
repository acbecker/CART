__author__ = 'brandonkelly'

import unittest
import numpy as np
from scipy import stats
from tree import *


class SimpleBartStep(object):
    def __init__(self):
        self.nsamples = 500
        self.resids = np.random.standard_normal(self.nsamples)


class VarianceTestCase(unittest.TestCase):
    def setUp(self):
        nsamples = 500
        nfeatures = 2
        self.X = np.random.standard_cauchy((nsamples, nfeatures))
        self.true_sigsqr = 0.7 ** 2
        self.y = 2.0 + self.X[:, 0] + np.sqrt(self.true_sigsqr) * np.random.standard_normal(nsamples)
        self.sigsqr = BartVariance(self.X, self.y)
        self.sigsqr.bart_step = SimpleBartStep()

    def tearDown(self):
        del self.X
        del self.y
        del self.true_sigsqr
        del self.sigsqr

    def test_prior(self):
        nu = 3.0  # Degrees of freedom for error variance prior; should always be > 3
        q = 0.90  # The quantile of the prior that the sigma2 estimate is placed at
        qchi = stats.chi2.interval(q, nu)[1]
        # scale parameter for error variance scaled inverse-chi-square prior
        lamb = self.true_sigsqr * qchi / nu

        # is the prior scale parameter within 5% of the expected value?
        frac_diff = np.abs(self.sigsqr.lamb - lamb) / lamb

        prior_msg = "Fractional difference in prior scale parameter for variance parameter is greater than 10%"
        self.assertLess(frac_diff, 0.10, msg=prior_msg)

    def test_random_posterior(self):
        ndraws = 100000
        ssqr_draws = np.empty(ndraws)
        for i in xrange(ndraws):
            ssqr_draws[i] = self.sigsqr.random_posterior()

        nu = self.sigsqr.nu
        prior_ssqr = self.sigsqr.lamb

        post_dof = nu + len(self.y)
        post_ssqr = (nu * prior_ssqr + np.sum(self.sigsqr.bart_step.resids ** 2)) / post_dof

        igam_shape = post_dof / 2.0
        igam_scale = post_dof * post_ssqr / 2.0
        igamma = stats.distributions.invgamma(igam_shape, scale=igam_scale)

        # test draws from conditional posterior by comparing 1st and 2nd moments to true values
        true_mean = igamma.moment(1)
        frac_diff = np.abs(true_mean - ssqr_draws.mean()) / true_mean
        rpmsg = "Fractional difference in mean from BartVariance.random_posterior() is greater than 2%"
        self.assertLess(frac_diff, 0.02, msg=rpmsg)

        true_ssqr = igamma.moment(2)
        frac_diff = np.abs(true_ssqr - (ssqr_draws.var() + ssqr_draws.mean() ** 2)) / true_ssqr
        rpmsg = "Fractional difference in 2nd moment from BartVariance.random_posterior() is greater than 2%"
        self.assertLess(frac_diff, 0.02, msg=rpmsg)


class MuTestCase(unittest.TestCase):
    def setUp(self):
        nsamples = 500
        nfeatures = 2
        self.alpha = 0.95
        self.beta = 2.0
        self.X = np.random.standard_cauchy((nsamples, nfeatures))
        self.mu = BartMeanParameter("mu", 200)
        self.y = 3.0 + np.random.standard_normal(nsamples)
        # Rescale y to lie between -0.5 and 0.5
        self.y -= self.y.min()  # minimum = 0
        self.y /= self.y.max()  # maximum = 1
        self.y -= 0.5      # range is -0.5 to 0.5
        self.mu.tree = BaseTree(self.X, self.y)
        # build the tree configuration by performing a sequence of grow updates
        ngrows = 5
        for i in xrange(ngrows):
            self.mu.tree.grow()
        self.mu.sigsqr = BartVariance(self.X, self.y)
        self.mu.sigsqr.bart_step = SimpleBartStep()
        self.mu.sigsqr.value = self.y.var()
        self.mu.set_starting_value(self.mu.tree)

    def tearDown(self):
        del self.X
        del self.y
        del self.mu

    def test_random_posterior(self):
        # first get values of mu drawn from their conditional posterior
        ndraws = 100000
        nleaves = len(self.mu.value)
        mu_draws = np.empty((ndraws, nleaves))
        for i in xrange(ndraws):
            mu_draws[i, :] = self.mu.random_posterior()

        l_idx = 0
        for leaf in self.mu.tree.terminalNodes:
            ny = leaf.npts
            ybar = leaf.ybar
            post_var = 1.0 / (1.0 / self.mu.prior_var + ny / self.mu.sigsqr.value)
            post_mean = post_var * (self.mu.mubar / self.mu.prior_var + ny * ybar / self.mu.sigsqr.value)

            # test draws from conditional posterior by comparing 1st and 2nd moments to true values
            zscore = np.abs((post_mean - mu_draws[:, l_idx].mean())) / np.sqrt(post_var / ndraws)
            rpmsg = "Sample mean from BartMeanParameter.random_posterior() differs by more than 3-sigma."
            self.assertLess(zscore, 3.0, msg=rpmsg)

            frac_diff = np.abs(np.sqrt(post_var) - mu_draws[:, l_idx].std()) / np.sqrt(post_var)
            rpmsg = "Fractional difference in standard deviation from BartMeanParameter.random_posterior() is greater" \
                + " than 2%"
            self.assertLess(frac_diff, 0.02, msg=rpmsg)

            l_idx += 1


if __name__ == "__main__":
    unittest.main()