"""
NAME
    pyframe.core
    
DESCRIPTION
    These are the core base-classes of the new re-vamped
    pyframe framework.

AUTHORS
    Ryan Reece  <ryan.reece@cern.ch>
    Alex Tuna   <alexander.tuna@cern.ch>
    Will Davey  <will.davey@cern.ch>

COPYRIGHT
    Copyright 2010 The authors
    License: GPL <http://www.gnu.org/licenses/gpl.html>

SEE ALSO
    ROOT <http://root.cern.ch>

2015-05-26
"""

## std imports
import json
import time
timestamp = time.strftime("%Y-%m-%d-%Hh%M")

## configure logging
import logging
logging.basicConfig(
       filename="pyframe.%s.log" % (timestamp),
       filemode="w",
       level=logging.INFO,
       format="[%(asctime)s %(name)-16s %(levelname)-7s]  %(message)s",
       datefmt="%Y-%m-%d %H:%M:%S",
       )
log = logging.getLogger(__name__)
#log.setLevel(logging.INFO)


#------------------------------------------------------------------------------
# Algorithm class
#------------------------------------------------------------------------------
class Algorithm(object):
    """
    A process to execute event-by-event in an analysis.  A user should write
    classes that inherit from Algorithm, implementing the initialize(),
    finalize(), and execute() methods as needed.
    """
    #_________________________________________________________________________
    def __init__(self, name=None, is_filter=False):
        # initialized here
        self.name = name or self.__class__
        self.is_filter = is_filter
        # initialized in +=
        self.parent = None             
        self.store  = None
        self.config = None

    #_________________________________________________________________________
    def initialize(self):
        """
        Override this method in your derived class as you need.
        """
        return None
    #_________________________________________________________________________
    def finalize(self):
        """
        Override this method in your derived class as you need.
        """
        return None
    #_________________________________________________________________________
    def execute(self):
        """
        Override this method in your derived class as you need.
        """
        return True



#------------------------------------------------------------------------------
# EventLoop class
#------------------------------------------------------------------------------
class EventLoop(object):
    """
    TODO: write a docstring.
    """
    #__________________________________________________________________________
    def __init__(self, name='myloop', config=None):
        self.name = name
        self.config = config or dict()  ## information persists
        self.store = dict()             ## information cleared event-by-event
        self._algorithms = list()
        self._progress_interval  = 100
        self._n_events_processed = 0
        self.quiet = False

    #_________________________________________________________________________
    def __iadd__(self, alg):
        """
        The user should use this operator to schedule Algorithms to the
        EventLoop.
        """
        algs_to_add = []
        try:
            iterator = iter(alg)
        except TypeError:
            # not iterable
            algs_to_add.append(alg)
        else:
            # iterable
            algs_to_add.extend(alg)

        for a in algs_to_add:
            a.parent = self # set a reference to this event loop
            a.config = self.config
            a.store  = self.store
            self._algorithms.append(a)

        return self

    #_________________________________________________________________________
    def run(self, min_entry=0, max_entry=-1):
        """
        This is the CPU-consuming function call that runs the event-loop.
        The user can optionally specify the event range to run over.
        """
        assert self.config.has_key('tree_reader')
        tr = self.config['tree_reader']

        log.info("EventLoop.run: %s" % self.name)

        n_entries = tr.get_entries()
        if max_entry < 0:
            max_entry = n_entries
        else:
            max_entry = min(max_entry, n_entries)

        ## initialize
        self.initialize()

        ## do the event-loop
        log_line = 'EventLoop.run: running on event %i to %i' % (min_entry, max_entry)
        log.info(log_line)
        print log_line
#        if not self.quiet:
#            progbar = progressbar.ProgressBar(width=24, block="=", empty=" ", min=min_entry, max=max_entry)
        rate = 0.0
        minutes_remaining = -1.0
        progress_time = time.clock()
        for i_entry in xrange(min_entry, max_entry):
            ## progress bar and log
            if i_entry % self._progress_interval == 0 or i_entry == max_entry-1:
                temp_progress_time = time.clock()
                if temp_progress_time-progress_time > 0.0:
                    rate = float(self._progress_interval)/(temp_progress_time-progress_time) if self._n_events_processed else 0.0
                else:
                    rate = 0.0
                minutes_remaining = float(max_entry-i_entry)/float(rate)/60.0 if rate else -1.0
#                if not self.quiet:
#                    digits = len(str(max_entry))
#                    progbar.update(i_entry+1, "[ %*s / %*s ] @ %.1f Hz (time remaining: %.1fm)" % (digits, i_entry+1, digits, max_entry, rate, minutes_remaining))
                progress_time = temp_progress_time
            if i_entry != 0 and (i_entry % 1000 == 0 or i_entry == max_entry-1):
                log_line = 'EventLoop.run: event: %12i @ %10.1f Hz (time remaining: %5.1fm)' % (i_entry, rate, minutes_remaining)
                log.info(log_line)
                print log_line

            ## GetEntry and execute algs
            tr.get_entry(i_entry)
            self.execute()

        # finalize
        self.finalize()

    #-------------------------------------------------------------------------
    # The user should not have to use the EventLoop functions below. 
    #-------------------------------------------------------------------------

    #_________________________________________________________________________
    def initialize(self):
        log.debug('EventLoop.initialize: %s' % self.name)
        ## begin timers
        self._timing = {}
        self._ncalls = {}
        ## initialize algs
        for alg in self._algorithms:
            _time = time.time()
            alg.initialize()
            _time = time.time()-_time
            self._timing['initialize_%s' % alg.name] = _time
            self._ncalls['initialize_%s' % alg.name] = 1
            self._timing['execute_%s' % alg.name] = _time
            self._ncalls['execute_%s' % alg.name] = 0
            log.debug('initialized %s' % alg.name)
        ## print config
        s_config = {}
        for key, val in self.config.iteritems():
            if isinstance(val, (int, long, float, complex, str, list)):
                s_config[key] = val
            else:
                s_config[key] = str(val)
        log.info('config =\n%s' % json.dumps(s_config, sort_keys=True, indent=4) )

    #_________________________________________________________________________
    def execute(self):
        for alg in self._algorithms:
            _time = time.time()
            result = alg.execute()
            _time = time.time()-_time
            ## bookkeep runtimes
            if 'execute_%s' % alg.name in self._timing:
                self._timing['execute_%s' % alg.name] += _time
                self._ncalls['execute_%s' % alg.name] += 1
            else:
                self._timing['execute_%s' % alg.name] = _time
                self._ncalls['execute_%s' % alg.name] = 1
            ## treat filter
            if alg.is_filter:
                if not result:
                    self.store.clear()
                    self._n_events_processed += 1
                    return False
        self.store.clear()
        self._n_events_processed += 1
        return True

    #_________________________________________________________________________
    def finalize(self):
        log.debug('EventLoop.finalize: %s' % self.name)
        ## finalize algs
        for alg in self._algorithms:
            _time = time.time()
            alg.finalize()
            _time = time.time()-_time
            self._timing['finalize_%s' % alg.name] = _time
            self._ncalls['finalize_%s' % alg.name] = 1
            log.debug('finalized %s' % alg.name)
        ## time summary
        log.info('ALGORITHM TIME SUMMARY\n' + self.get_time_summary())

    #_________________________________________________________________________
    def get_time_summary(self):
        s = '\n'
        s += '%3s %-40s %8s %8s %10s %8s\n' % ('#', 'ALGORITHM', 'TIME [s]', 'CALLS', 'RATE [Hz]', 'FRACTION')

        ## timing per method
        for method in ['initialize', 'execute', 'finalize']:
            s += ' %s %s %s\n' % ('-'*25, method, '-'*(79-25-len(method)))

            ## timing method summary
            timingSum = sum([self._timing['%s_%s' % (method,alg.name)] for alg in self._algorithms])
#            ncalls = self._n_events_processed if method == 'execute' else 1
            ncalls = self._ncalls['%s_%s' % (method,alg.name)] if method == 'execute' else 1
            rate = ncalls / timingSum if timingSum else 0.0
            s += '%3s %-40s %8.2f %8i %10.1f %8.3f\n' % ('', 'Sum', timingSum, ncalls, rate, 1.00)
            if not timingSum:
                continue

            ## timing per alg
            for i_alg, alg in enumerate(self._algorithms):
                if '%s_%s' % (method, alg.name) in self._timing:
                    timing = self._timing['%s_%s' % (method, alg.name)]
                    ncalls = self._ncalls['%s_%s' % (method, alg.name)]
                    rate = ncalls / timing if timing else -1
                    fraction = timing / timingSum
                    s += '%3i %-40s %8.2f %8i %10.1f %8.3f\n' % (i_alg, alg.name, timing, ncalls, rate, fraction)
                else:
                    log.warning(""" %s does not have runtime statistics. Oops!""" % (alg.name) )

        return s

