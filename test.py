import unittest
import numpy as np
from scipy import stats
from tree import CartTree, Node, BartVariance, BartMeanParameter, BartTreeParameter

class TreeTestCases(unittest.TestCase):
    def setUp(self):
        nsamples  = 100
        nfeatures = 10
        self.X    = np.random.random((nsamples, nfeatures)) - 0.5
        self.y    = np.random.random((nfeatures)) - 0.5
        self.tree = CartTree(self.X, self.y)

    def tearDown(self):
        del self.X
        del self.y
        del self.tree

    def testGrow(self):
        headId = self.tree.head.Id
        self.tree.grow(1, 0.0)
        self.assertTrue([x.Id-headId for x in self.tree.terminalNodes] == [2, 1])
        self.assertTrue([x.Id-headId for x in self.tree.internalNodes] == [0])

    def testSplit(self):
        headId = self.tree.head.Id
        self.tree.split(self.tree.head, 1, 0.0)
        self.tree.split(self.tree.head.Left, 2, 0.0)
        self.tree.split(self.tree.head.Left.Right, 3, 0.0)
        self.assertTrue([x.Id-headId for x in self.tree.terminalNodes] == [2, 6, 5, 3])
        self.assertTrue([x.Id-headId for x in self.tree.internalNodes] == [0, 1, 4])

    def testPrune(self):
        headId = self.tree.head.Id
        self.tree.split(self.tree.head, 1, 0.0)
        self.tree.prune()
        self.assertTrue([x.Id-headId for x in self.tree.terminalNodes] == [0])
        self.assertTrue([x.Id-headId for x in self.tree.internalNodes] == [])

    def testChange(self):
        headId = self.tree.head.Id
        self.tree.grow(1, 0.0)
        self.tree.grow(2, 0.0)
        self.tree.grow(3, 0.0)
        tNodes = self.tree.terminalNodes
        iNodes = self.tree.internalNodes
        node = self.tree.change(4, 1.0)
        self.assertTrue(node.feature == 4)
        self.assertTrue(node.threshold == 1.0)
        self.assertTrue(tNodes == self.tree.terminalNodes) # tree itself is not changed
        self.assertTrue(iNodes == self.tree.internalNodes)

    def testSwap(self):
        headId = self.tree.head.Id
        self.tree.split(self.tree.head, 1, 0.0)
        self.tree.split(self.tree.head.Left, 2, 0.0)
        self.tree.swap()


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

    def test_prior(self):
        nu = 3.0  # Degrees of freedom for error variance prior; should always be > 3
        q = 0.90  # The quantile of the prior that the sigma2 estimate is placed at
        qchi = stats.chi2.interval(q, nu)[1]
        # scale parameter for error variance scaled inverse-chi-square prior
        lamb = self.true_sigsqr * qchi / nu

        # is the prior scale parameter within 5% of the expected value?
        frac_diff = np.abs(self.sigsqr.lamb - lamb) / lamb

        prior_msg = "Fractional difference in prior scale parameter for variance parameter is greater than 5%"
        self.assertLess(frac_diff, 0.05, msg=prior_msg)

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

        ksstat, pvalue = stats.kstest(ssqr_draws, igamma.cdf)
        gibbs_msg = 'KS-Test finds that BartVariance.random_posterior() deviates from theoretical distribution.'
        self.assertGreater(pvalue, 0.01, msg=gibbs_msg)

if __name__ == "__main__":
    unittest.main()
