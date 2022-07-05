from time import time, sleep
import argparse

import psutil


def run(self, cmds, n_jobs=1):
    """
    run a list of command lines

    Args:
        cmds: iter
            iterable of command lines to be executed. These command lines are assumed to not depend on one another
        n_jobs: int (default: 1)
            number of parallel jobs/command lines to be executed
    """

    def is_running(p):
        return p is not None and p.is_running() and p.status() != psutil.IS_ZOMBIE
    def is_done(p):
        return p is not None and (not p.is_running() or p.status() == psutil.IS_ZOMBIE)

    if not n_jobs:
        n_jobs = self.n_jobs


    # keep track of running processes
    n_running = 0
    processes_next_index = 0
    processes_launched = []
    processes_finished = []
    processes_start_time = []
    processes = []

    while True:
        for _ in range(n_running, n_jobs):
            if processes_next_index < len(cmds):
                p = psutil.Popen(cmds[processes_next_index])
                processes_start_time.append(time())
                processes.append(processes_next_index)
                print(f"Processing command line number {processes_next_index}\n{cmds[processes_next_index]}")
                processes_next_index += 1
                n_running += 1

        for i, pl in enumerate(processes_launched):
            if pl in processes_finished:
                continue
            if is_done(processes[pl]):
                # time elapsed in minutes
                time_elapsed = (time() - processes_start_time[i]) / 60
                print(f"Job number {pl} has finished, time elapsed: {time_elapsed} minutes")
                processes_finished.append(pl)
        sleep(10)
    
        if len(processes_finished) == len(cmds):
            break
        if len(processes_finished) + len(processes_dead) == len(cmds):
            break



def pythia_impl():
    pass

def sherpa_impl():
    pass

def pythia(args):
    pass

def sherpa(args):
    pass


def main():
    """entry point"""

    common_job_parser = argparse.ArgumentParser(add_help=False)
    common_job_parser.add_argument("-j", "--jobs", type=int, help="number of parallel jobs", default=1)

    parser = argparse.ArgumentParser(description='Study MC event generators')

    sub_parsers = parser.add_subparsers(dest="command")
    
    rel_val_parser = sub_parsers.add_parser("pythia", parents=[common_job_parser])
    rel_val_parser.set_defaults(func=pythia)

    inspect_parser = sub_parsers.add_parser("sherpa", parents=[common_job_parser])
    inspect_parser.set_defaults(func=sherpa)

    args = parser.parse_args()
    return(args.func(args))

if __name__ == "__main__":
    sys.exit(main())
