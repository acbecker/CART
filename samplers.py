"""
This file contains the class definition for the sampler MCMCSample classes.
"""

__author__ = 'Brandon C. Kelly'

import numpy as np
import progressbar
from matplotlib import pyplot as plt
import acor


class MCMCSample(object):
    """
    Class object for parameter samples generated by a yamcmc++ sampler. This class contains a dictionary of samples
    generated by an MCMC sampler for a set of parameters, as well as methods for plotting and summarizing the results.

    In general, the MCMCSample object is empty upon instantiation. One adds parameters to the dictionary through the
    AddStep method of a Sampler object. Running a Sampler object then fills the dictionary up with the parameter values.
    After running a Sampler object, the MCMCSample object will contain the parameter values, which can then be analyzed
    further.

    Alternatively, one can load the parameters and their values from a file. This is done through the method
    generate_from_file. This is helpful if one has a set of MCMC samples generated by a different program.
    """
    __slots__ = ["samples", "logpost"]

    def __init__(self, filename=None, logpost=None, trace=None):
        """
        Constructor for an MCMCSample object. If no arguments are supplied, then this just creates an empty dictionary
        that will contain the MCMC samples. In this case parameters are added to the dictionary through the addstep
        method of a Sampler object, and the values are generated by running the Sampler object. Otherwise, if a
        filename is supplied then the parameter names and MCMC samples are read in from that file.

        :param filename: A string giving the name of an asciifile containing the MCMC samples.
        """
        self.samples = dict()  # Empty dictionary. We will place the samples for each tracked parameter here.

        if logpost is not None:
            self.logpost = logpost

        if trace is not None:
            self.generate_from_trace(trace)
        elif filename is not None:
            # Construct MCMCSample object by reading in MCMC samples from one or more asciifiles.
            self.generate_from_file([filename])

    def generate_from_trace(self):
        pass

    def get_samples(self, name):
        """
        Returns a copy of the numpy array containing the samples for a parameter. This is safer then directly
        accessing the dictionary object containing the samples to prevent one from inadvertently changes the values of
        the samples output from an MCMC sampler.

        :param name: The name of the parameter for which the samples are desired.
        """
        return self.samples[name].copy()

    def generate_from_file(self, filename):
        """
        Build the dictionary of parameter samples from an ascii file of MCMC samples. The first line of this file
        should contain the parameter names.

        :param filename: The name of the file containing the MCMC samples.
        """
        # TODO: put in exceptions to make sure files are ready correctly
        for fname in filename:
            file = open(fname, 'r')
            name = file.readline()
            # Grab the MCMC output
            trace = np.genfromtxt(fname, skip_header=1)
            if name not in self.samples:
                # Parameter is not already in the dictionary, so add it. Otherwise do nothing.
                self.samples[name] = trace
        self.newaxis()

    def autocorr_timescale(self, trace):
        """
        Compute the autocorrelation time scale as estimated by the `acor` module.

        :param trace: The parameter trace, a numpy array.
        """
        acors = []
        for i in range(trace.shape[1]):
            tau, mean, sigma = acor.acor(trace[:, i].real)  # Warning, does not work with numpy.complex
            acors.append(tau)
        return np.array(acors)

    def effective_samples(self, name):
        """
        Return the effective number of independent samples of the MCMC sampler.

        :param name: The name of the parameter to compute the effective number of independent samples for.
        """
        if not self.samples.has_key(name):
            print "WARNING: sampler does not have", name
            return
        else:
            print "Calculating effective number of samples"

        traces = self.samples[name]  # Get the sampled parameter values
        npts = traces.shape[0]
        timescale = self.autocorr_timescale(traces)
        return npts / timescale

    def plot_trace(self, name, doShow=False):
        """
        Plot the trace of the values, a time series showing the evolution of the parameter values for the MCMC sampler.
        Only a single parameter element trace is shown per plot, and all plots are shown on the same plotting window. In
        particular, if a parameter is array-valued, then the traces for each element of its array are plotted on a
        separate subplot.

        :param name: The parameter name.
        """
        if not self.samples.has_key(name):
            print "WARNING: sampler does not have", name
            return
        else:
            print "Plotting Trace"
            fig = plt.figure()

        traces = self.samples[name]  # Get the sampled parameter values
        ntrace = traces.shape[1]
        spN = plt.subplot(ntrace, 1, ntrace)
        spN.plot(traces[:,-1], ".", markersize=2)
        spN.set_xlabel("Step")
        spN.set_ylabel("par %d" % (ntrace-1))
        for i in range(ntrace-1):
            sp = plt.subplot(ntrace, 1, i+1, sharex=spN)
            sp.plot(traces[:,i], ".", markersize=2)
            sp.set_ylabel("par %d" % (i))
            plt.setp(sp.get_xticklabels(), visible=False)
        plt.suptitle(name)
        if doShow:
            plt.show()

    def plot_1dpdf(self, name, doShow=False):
        """
        Plot histograms of the parameter values generated by the MCMC sampler. If the parameter is array valued then
        histograms of all of the parameter's elements will be plotted.

        :param name: The parameter name.
        """
        if not self.samples.has_key(name):
            print "WARNING: sampler does not have", name
            return
        else:
            print "Plotting 1d PDF"
            fig = plt.figure()

        traces = self.samples[name]  # Get the sampled parameter values
        ntrace = traces.shape[1]
        for i in range(ntrace):
            sp = plt.subplot(ntrace, 1, i+1)
            sp.hist(traces[:,i], bins=50, normed=True)
            sp.set_ylabel("par %d" % (i))
            if i == ntrace-1:
                sp.set_xlabel("val")
        plt.suptitle(name)
        if doShow:
            plt.show()

    def plot_2dpdf(self, name1, name2, pindex1=0, pindex2=0, doShow=False):
        """
        Plot joint distribution of the parameter values generated by the MCMC sampler.

        :param name1: The parameter name along x-axis
        :param name2: The parameter name along y-axis
        :param pindex1: Which element of the array to plot
        :param pindex2: Which element of the array to plot
        :param doShow: Call plt.show()
        """
        if (not self.samples.has_key(name1)) or (not self.samples.has_key(name2)) :
            print "WARNING: sampler does not have", name1, name2
            return

        if pindex1 >= self.samples[name1].shape[1]:
            print "WARNING: not enough data in", name1
            return
        if pindex2 >= self.samples[name2].shape[1]:
            print "WARNING: not enough data in", name2
            return

        print "Plotting 2d PDF"
        fig    = plt.figure()
        trace1 = self.samples[name1][:,pindex1]
        trace2 = self.samples[name2][:,pindex2]

        # joint distribution
        axJ = fig.add_axes([0.1, 0.1, 0.7, 0.7])               # [left, bottom, width, height]
        # y histogram
        axY = fig.add_axes([0.8, 0.1, 0.125, 0.7], sharey=axJ)
        # x histogram
        axX = fig.add_axes([0.1, 0.8, 0.7, 0.125], sharex=axJ)
        axJ.plot(trace1, trace2, 'ro', ms=1, alpha=0.5)
        axX.hist(trace1, bins=100)
        axY.hist(trace2, orientation='horizontal', bins=100)
        axJ.set_xlabel("%s %d" % (name1, pindex1))
        axJ.set_ylabel("%s %d" % (name2, pindex2))
        plt.setp(axX.get_xticklabels()+axX.get_yticklabels(), visible=False)
        plt.setp(axY.get_xticklabels()+axY.get_yticklabels(), visible=False)
        if doShow:
            plt.show()

    def plot_2dkde(self, name1, name2, pindex1=0, pindex2=0,
                   nbins=100, doPlotStragglers=True, doShow=False):
        """
        Plot joint distribution of the parameter values generated by the MCMC sampler using a kernel density estimate.

        :param name1: The parameter name along x-axis
        :param name2: The parameter name along y-axis
        :param pindex1: Which element of the array to plot
        :param pindex2: Which element of the array to plot
        :param doShow: Call plt.show()
        :param nbins: Number of bins along each axis for KDE
        :param doPlotStragglers: Plot individual data points outside KDE contours.  Works poorly for small samples.
        """
        if (not self.samples.has_key(name1)) or (not self.samples.has_key(name2)) :
            print "WARNING: sampler does not have", name1, name2
            return

        if pindex1 >= self.samples[name1].shape[1]:
            print "WARNING: not enough data in", name1
            return
        if pindex2 >= self.samples[name2].shape[1]:
            print "WARNING: not enough data in", name2
            return

        print "Plotting 2d PDF w KDE"
        fig    = plt.figure()
        trace1 = self.samples[name1][:,pindex1].real # JIC we get something imaginary?
        trace2 = self.samples[name2][:,pindex2].real
        npts = trace1.shape[0]
        kde = scipy.stats.gaussian_kde((trace1, trace2))
        bins1 = np.linspace(trace1.min(), trace1.max(), nbins)
        bins2 = np.linspace(trace2.min(), trace2.max(), nbins)
        mesh1, mesh2 = np.meshgrid(bins1, bins2)
        hist = kde([mesh1.ravel(), mesh2.ravel()]).reshape(mesh1.shape)

        clevels = []
        for frac in [0.9973, 0.9545, 0.6827]:
            hfrac = lambda level, hist=hist, frac=frac: hist[hist>=level].sum()/hist.sum() - frac
            level = scipy.optimize.bisect(hfrac, hist.min(), hist.max())
            clevels.append(level)

        # joint distribution
        axJ = fig.add_axes([0.1, 0.1, 0.7, 0.7])               # [left, bottom, width, height]
        # y histogram
        axY = fig.add_axes([0.8, 0.1, 0.125, 0.7], sharey=axJ)
        # x histogram
        axX = fig.add_axes([0.1, 0.8, 0.7, 0.125], sharex=axJ)
        cont = axJ.contour(mesh1, mesh2, hist, clevels, linestyles="solid", cmap=plt.cm.jet)
        axX.hist(trace1, bins=100)
        axY.hist(trace2, orientation='horizontal', bins=100)
        axJ.set_xlabel("par %d" % (pindex1))
        axJ.set_ylabel("par %d" % (pindex2))
        plt.setp(axX.get_xticklabels()+axX.get_yticklabels(), visible=False)
        plt.setp(axY.get_xticklabels()+axY.get_yticklabels(), visible=False)

        # Note to self: you need to set up the contours above to have
        # the outer one first, for collections[0] to work below.
        #
        # Also a note: this does not work if the outer contour is not
        # fully connected.
        if doPlotStragglers:
            outer = cont.collections[0]._paths
            sx = []
            sy = []
            for i in range(npts):
                found = [o.contains_point((trace1[i], trace2[i])) for o in outer]
                if not (True in found):
                    sx.append(trace1[i])
                    sy.append(trace2[i])
            axJ.plot(sx, sy, 'k.', ms = 1, alpha = 0.1)
        if doShow:
            plt.show()

    def plot_autocorr(self, name, acorrFac = 10.0, doShow=False):
        """
        Plot the autocorrelation functions of the traces for a parameter. If the parameter is array-value then
        autocorrelation plots for each of the parameter's elements will be plotted.

        :param name: The parameter name.
        """
        if not self.samples.has_key(name):
            print "WARNING: sampler does not have", name
            return
        else:
            print "Plotting autocorrelation function (this make take a while)"
            fig = plt.figure()

        traces = self.samples[name]  # Get the sampled parameter values
        mtrace = np.mean(traces, axis=0)
        ntrace = traces.shape[1]
        acorr  = self.autocorr_timescale(traces)

        for i in range(ntrace):
            sp = plt.subplot(ntrace, 1, i+1)
            lags, acf, not_needed1, not_needed2 = plt.acorr(traces[:, i] - mtrace[i], maxlags=traces.shape[0]-1, lw=2)
            sp.set_xlim(-0.5, acorrFac * acorr[i])
            sp.set_ylim(-0.01, 1.01)
            sp.axhline(y=0.5, c='k', linestyle='--')
            sp.axvline(x=acorr[i], c='r', linestyle='--')
            sp.set_ylabel("par %d autocorr" % (i))
            if i == ntrace-1:
                sp.set_xlabel("lag")
        plt.suptitle(name)
        if doShow:
            plt.show()

    def plot_parameter(self, name, pindex=0, doShow=False):
        """
        Simultaneously plots the trace, histogram, and autocorrelation of this parameter's values. If the parameter
        is array-valued, then the user must specify the index of the array to plot, as these are all 1-d plots on a
        single plotting window.

        :param name: The name of the parameter that the plots are made for.
        :param pindex: If the parameter is array-valued, then this is the index of the array that the plots are made
                       for.
        """
        if not self.samples.has_key(name):
            print "WARNING: sampler does not have", name
            return
        else:
            print "Plotting parameter summary"
            fig = plt.figure()

        traces = self.samples[name]
        plot_title = name
        if traces.ndim > 1:
            # Parameter is array valued, grab the column corresponding to pindex
            if traces.ndim > 2:
                # Parameter values are at least matrix-valued, reshape to a vector
                traces = traces.reshape(traces.shape[0], np.prod(traces.shape[1:]))
            traces = traces[:, pindex]
            plot_title = name + ", element " + str(pindex)

        # First plot the trace
        plt.subplot(211)
        plt.plot(traces, '.', markersize=2)
        plt.xlim(0, traces.size)
        plt.xlabel("Iteration")
        plt.ylabel("Value")
        plt.title(plot_title)

        # Now add the histogram of values to the trace plot axes
        pdf, bin_edges = np.histogram(traces, bins=25)
        bin_edges = bin_edges[0:pdf.size]
        # Stretch the PDF so that it is readable on the trace plot when plotted horizontally
        pdf = pdf / float(pdf.max()) * 0.34 * traces.size
        # Add the histogram to the plot
        plt.barh(bin_edges, pdf, height=bin_edges[1] - bin_edges[0], alpha=0.75)

        # Finally, plot the autocorrelation function of the trace
        plt.subplot(212)
        centered_trace = traces - traces.mean()
        lags, acf, not_needed1, not_needed2 = plt.acorr(centered_trace, maxlags=traces.size - 1, lw=2)
        acf = acf[acf.size / 2:]
        plt.ylabel("ACF")
        plt.xlabel("Lag")

        # Compute the autocorrelation timescale, and then reset the x-axis limits accordingly
        # acf_timescale = self.autocorr_timescale(traces)
        plt.xlim(0, traces.size / 10.0)
        if doShow:
            plt.show()

    def posterior_summaries(self, name):
        """
        Print out the posterior medians, standard deviations, and 68th, 95th, and 99th credibility intervals.

        :param name: The name of the parameter for which the summaries are desired.

        See the documentation for MCMCSample.plot_trace for further information.
        """
        if not self.samples.has_key(name):
            print "WARNING: sampler does not have", name
            return
        else:
            print "Plotting parameter summary"
            fig = plt.figure()

        traces = self.samples[name]  # Get the sampled parameter values
        effective_nsamples = self.effective_samples(name)  # Get the effective number of independent samples
        if traces.ndim == 1:
            # Parameter is scalar valued, so this is easy
            print "Posterior summary for parameter", name
            print "----------------------------------------------"
            print "Effective number of independent samples:", effective_nsamples
            print "Median:", np.median(traces)
            print "Standard deviation:", np.std(traces)
            print "68% credibility interval:", np.percentile(traces, (16.0, 84.0))
            print "95% credibility interval:", np.percentile(traces, (2.5, 97.5))
            print "99% credibility interval:", np.percentile(traces, (0.5, 99.5))
        else:
            if traces.ndim > 2:
                # Parameter values are at least matrix-valued, reshape to a vector.
                traces = traces.reshape(traces.shape[0], np.prod(traces.shape[1:]))

            for i in xrange(traces.shape[1]):
                # give summary for each element of this parameter separately
                # Parameter is scalar valued, so this is easy
                print "Posterior summary for parameter", name, " element", i
                print "----------------------------------------------"
                print "Effective number of independent samples:", effective_nsamples[i]
                print "Median:", np.median(traces[:, i])
                print "Standard deviation:", np.std(traces[:, i])
                print "68% credibility interval:", np.percentile(traces[:, i], (16.0, 84.0))
                print "95% credibility interval:", np.percentile(traces[:, i], (2.5, 97.5))
                print "99% credibility interval:", np.percentile(traces[:, i], (0.5, 99.5))

    def newaxis(self):
        for key in self.samples.keys():
            if len(self.samples[key].shape) == 1:
                self.samples[key] = self.samples[key][:, np.newaxis]


class Sampler(object):
    """
    A class to generate samples of parameter from their probability distribution. Samplers consist of a series of
    steps, where each step updates the value of the parameter(s) associated with it. The samples for the tracked
    parameters are saved to a MCMCSample object.
    """
    __slots__ = ["sample_size", "burnin", "thin", "_steps", "_burnin_bar", "_sampler_bar", "mcmc_samples"]

    def __init__(self, steps=None):
        """
        Constructor for Sampler object.

        :param steps: A list of step objects to iterate over in one MCMC iteration.
        :param mcmc_samples: An MCMCSample object. The generated samples are added to this object.
        """
        self.sample_size = 0
        self.burnin = 0
        self.thin = 1
        self._steps = []  # Empty list that will eventually contain the step objects.
        if steps is not None:
            for s in steps:
                self.add_step(s)

        # Construct progress bar objects
        self._burnin_bar = progressbar.ProgressBar()
        self._sampler_bar = progressbar.ProgressBar()

        self.mcmc_samples = MCMCSample()  # MCMCSample class object. This is where the sampled values are stored.

    def add_step(self, step):
        """
        Method to add a step object to the sampler. The sampler will iterate over the step objects, calling their
        Draw() method once per iteration. This method will also initialize the parameter value associated with this
        step, and if the parameter is tracked it will add it to the dictionary containing the samples.
        """
        self._steps.append(step)

    def _allocate_arrays(self):

        for step in self._steps:
            if step._parameter.track:
                # We are saving this parameter's values, so add to dictionary of samples.
                if np.isscalar(step._parameter.value):
                    # Parameter is scalar-valued, so this is easy
                    value_array = np.empty(self.sample_size)
                else:
                    # Parameter is array-like, so get shape of parameter array first
                    pshape = step._parameter.value.shape
                    trace_shape = (self.sample_size,) + pshape
                    # Get numpy array that will store the samples values for this parameter
                    value_array = np.empty(trace_shape)
                    # Add the array that will hold the sampled parameter values to the dictionary of samples.
                self.mcmc_samples.samples[step._parameter.name] = value_array

    def start(self):
        for step in self._steps:
            step._parameter.set_starting_value()
        self._allocate_arrays()
        self._burnin_bar.maxval = self.burnin
        self._sampler_bar.maxval = self.sample_size

    def iterate(self, niter, burnin_stage):
        """
        Method to perform niter iterations of the sampler.

        :param niter: The number of iterations to perform.
        :param burnin_stage: Are we in the burn-in stage? A boolean.
        """
        for i in xrange(niter):
            for step in self._steps:
                step.do_step()

            if burnin_stage:
                # Update the burn-in progress bar
                self._burnin_bar.update(i + 1)

    def save_values(self):
        """
        Save the parameter values. These values are saved in a dictionary of numpy arrays, indexed according to the
        parameter names. The dictionary of samples is accessed as Sampler.samples.
        """
        current_iteration = self._sampler_bar.currval  # Progress bar keeps track of how many iterations we have run
        for step in self._steps:
            # Save the parameter value associated with each step.
            if np.isscalar(step._parameter.value):
                # Need to treat scalar case separately
                self.mcmc_samples.samples[step._parameter.name][current_iteration] = step._parameter.value
            else:
                # Have a vector- or matrix-valued parameter
                self.mcmc_samples.samples[step._parameter.name][current_iteration, :] = step._parameter.value

    def run(self, burnin, nsamples, thin=1):
        """
        Run the sampler.

        :param nsamples: The final sample size to generate. A total of burnin + thin * nsamples iterations will
                        be performed.
        :param burnin: The number of burnin iterations to run.
        :param thin: The thinning interval. Every thin iterations will be kept.
        """
        self.burnin = burnin
        self.sample_size = nsamples
        self.thin = thin
        # Set starting values
        self.start()

        print "Using", len(self._steps), "steps in the MCMC sampler."
        print "Obtaining samples of size", self.sample_size, "for", len(self.mcmc_samples.samples), "parameters."

        # Do burn-in stage
        print "Doing burn-in stage first..."
        self._burnin_bar.start()
        self.iterate(self.burnin, True)  # Perform the burn-in iterations

        # Now run the sampler.
        print "Sampling..."
        self._sampler_bar.start()

        for i in xrange(self.sample_size):
            if self.thin == 1:
                # No thinning is performed, so don't waste time calling self.Iterate.
                for step in self._steps:
                    step.do_step()

            else:
                # Need to thin the samples, so do thin iterations.
                self.iterate(self.thin, False)

            # Now save the tracked parameter values to the samples dictionary object
            self.save_values()

            self._sampler_bar.update(i + 1)  # Update the progress bar

        return self.mcmc_samples

    def restart(self, sample_size, thin=1):
        """
        Restart the MCMC sampler at the current value. No burn-in stage will be performed.
        """
        pass
