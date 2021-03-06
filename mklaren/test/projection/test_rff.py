import unittest
import numpy as np
from mklaren.kernel.kernel import exponential_kernel
from mklaren.projection.rff import RFF, RBFSampler

class TestRFF(unittest.TestCase):

    def setUp(self):
        self.n = 100
        self.p = 100
        self.rank_range = [10, 30, 50, 90]
        self.X = np.random.rand(self.n, self.p)
        self.gamma_range = np.logspace(-3, -1, 5)
        self.lbd_range = np.logspace(-2, 2, 5)

        # Generate a random signal by employing one of the kernels
        K = exponential_kernel(self.X, self.X, gamma=self.gamma_range[1])
        self.alpha = np.random.rand(self.n, 1)
        self.y = K.dot(self.alpha).ravel()


    def testReconstruction(self):
        """
        Fitted features must match transformed ones.
        """
        model = RFF(delta=10, rank=30, gamma_range=self.gamma_range, lbd=0)
        model.fit(self.X, self.y)
        G = model.G
        Gt = model.transform(self.X)
        self.assertAlmostEqual(np.linalg.norm(G - Gt), 0, places=3)


    def testFitting(self):
        """
        Reconstruction must improve with increasing rank and
        random initial conditions
        """
        errors = np.zeros((len(self.rank_range),))

        for ri, rank in enumerate(self.rank_range):
            model = RFF(delta=10, rank=rank,
                        gamma_range=self.gamma_range, random_state=42,
                        lbd=0)
            model.fit(self.X, self.y)
            yp = model.predict(self.X)
            errors[ri] = np.sum((self.y.ravel() - yp.ravel()) ** 2)
        self.assertTrue(np.all(errors[:-1] > errors[1:]))

    def testRegularization(self):
        """
        Reconstruction must improve with increasing rank and
        random initial conditions
        """
        errors = np.zeros((len(self.lbd_range),))
        beta_norms = np.zeros((len(self.lbd_range),))

        for li, lbd in enumerate(self.lbd_range):
            model = RFF(delta=10, rank=30,
                        gamma_range=self.gamma_range, random_state=42,
                        lbd=lbd)
            model.fit(self.X, self.y)
            yp = model.predict(self.X)
            errors[li] = np.sum((self.y.ravel() - yp.ravel()) ** 2)
            beta_norms[li] = np.linalg.norm(model.beta)

        # Error grows with lambda
        # Vector norm drops
        self.assertTrue(np.all(errors[:-1] < errors[1:]))
        self.assertTrue(np.all(beta_norms[:-1] > beta_norms[1:]))

    def testConvergence(self):
        """
        Make sure both definitions of gamma are equivalent.
        :return:
        """

        for g in self.gamma_range:
            K = exponential_kernel(self.X, self.X, gamma=g)[:, :]
            y = K.dot(np.ones((self.n, 1)))

            model = RFF(delta=0, rank=100,
                        gamma_range=[g], random_state=42, lbd=0.0,
                        normalize=False)
            model.fit(self.X, y)

            errors = np.zeros((len(self.rank_range),))
            for ri, rank in enumerate(self.rank_range):
                Gt = model.transform(X=self.X)[:, :rank]
                Kt = Gt.dot(Gt.T)
                errors[ri] = np.linalg.norm(K - Kt)

            self.assertTrue(np.all(errors[:-1] > errors[1:]))