import sys
from time import time, sleep
import argparse
from os.path import join, exists, abspath
from os import makedirs
from subprocess import PIPE
from glob import glob

import psutil


def print_error(err):
    print(f"ERROR: {err}")

def run_single(cmd, cwd, log_file=None):
    cwd = abspath(cwd)
    cmd = f"{cmd} ; "
    if not exists(cwd):
        makedirs(cwd)
    if not log_file:
        timestamp = int(time() * 1000)
        log_file = join(cwd, f"run_{timestamp}.log")
    p = psutil.Popen(["/bin/bash", "-c", f"{{ {cmd}}} > {log_file} 2>&1"], cwd=cwd)
    return p


def run(cmds, parent_dir="simulations", *, n_jobs=1, cwds=None):
    """
    run a list of command lines

    Args:
        cmds: iter
            iterable of command lines to be executed. These command lines are assumed to not depend on one another
        n_jobs: int (default: 1)
            number of parallel jobs/command lines to be executed
    """
    print(f"### RUN INFORMATION ###\nNumber of jobs: {n_jobs}\nNumber of command lines to be run: {len(cmds)}")

    if not exists(parent_dir):
        makedirs(parent_dir)

    def is_running(p):
        return p is not None and p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    def is_done(p):
        return p is not None and (not p.is_running() or p.status() == psutil.STATUS_ZOMBIE)

    # keep track of running processes
    n_running = 0
    processes_next_index = 0
    processes_launched = []
    processes_finished = []
    processes_start_time = []
    processes = []
    if not cwds:
        cwds = [f"run_{i}" for  i, _ in enumerate(cmds)]
    if len(cwds) != len(cmds):
        print("Make sure to pass as many output directories as you pass command lines")
        sys.exit(1)

    while True:
        for _ in range(n_running, n_jobs):
            if processes_next_index < len(cmds):
                cwd = join(abspath(parent_dir), cwds[processes_next_index])
                p = run_single(f"{cmds[processes_next_index]}", cwd)
                processes_start_time.append(time())
                processes.append(p)
                processes_launched.append(processes_next_index)
                print(f"Processing command {processes_next_index}\n{cmds[processes_next_index]}\nin directory {cwd}")
                processes_next_index += 1
                n_running += 1

        do_sleep = True
        for i, pl in enumerate(processes_launched):
            if pl in processes_finished:
                continue
            if is_done(processes[pl]):
                time_elapsed = (time() - processes_start_time[i]) / 60
                print(f"Job number {pl} has finished, time elapsed: {time_elapsed} minutes")
                processes_finished.append(pl)
                n_running -= 1
                do_sleep = False
        if do_sleep:
            sleep(2)
    
        if len(processes_finished) == len(cmds):
            break

def check_args(args):
    """
    Common checks for cmd args
    """
    if not exists(args.exec_dir):
        print_error(f"Cannot find executable directory at {args.exec_dir}")
        return False
    return True


def get_executable(exec_dir, exec_name):
    executable = join(exec_dir, exec_name)
    if not exists(executable):
        print_error(f"Executable {exec_name} cannot be found in {exec_dir}, make sure that it exists")
        sys.exit(1)
    return executable

def compute_events_per_job(n_events_total, n_events_per_job):
    n_rounds = int(n_events_total / n_events_per_job)
    events = [n_events_per_job] * n_rounds

    append_events = n_events_total - sum(events)
    if append_events > 0:
        if append_events < n_events_per_job:
            events[-1] += append_events
        else:
            events.append(append_events)
    return events


def pythia(args):
    executable = get_executable(args.exec_dir, "Pythia_jets.exe")
    pthard_low = args.pthard_low
    pthard_up = args.pthard_up
    events_per_pthard = args.events_per_pthard
    if len(pthard_low) != len(pthard_up):
        print_error(f"Different lengths of pthard limits, {len(pthard_low)} vs. {len(pthard_up)}")
        return 1
    if len(pthard_low) != len(events_per_pthard):
        print_error(f"Different lengths of pthard limits and number of events per bin, {len(pthard_low)} vs. {len(events_per_pthard)}")
        return 1

    cmds = []
    for pt_low, pt_up, n_ev in zip(pthard_low, pthard_up, events_per_pthard):
        events = compute_events_per_job(n_ev, args.events_per_job)
        print(f"pT hard bin [{pt_low}, {pt_up}] with {n_ev} events")
        for ev in events:
            cmd = f"{executable} {args.tune} {args.number} {ev} {args.jet_radius} {args.mecorr} {args.charged} {args.unev} {args.flavour} {pt_low} {pt_up}"
            cmds.append(cmd)
            print(cmd)

    save_dir = args.output
    run(cmds, save_dir, n_jobs=args.jobs)

    merge_dir = join(save_dir, "pthat_merged")
    print(f"==> MERGE per pThat to {merge_dir} <==")
    if not exists(merge_dir):
        makedirs(merge_dir)
    cmds = []
    out_dirs = []
    for pt_low, pt_up, n_ev in zip(pthard_low, pthard_up, events_per_pthard):
        root_files = glob(f"{save_dir}/*/*{pt_low}*pthat{pt_up}*.root", recursive=True)
        root_files = [abspath(rf) for rf in root_files]
        out_root_file = f"merged_pthatlow_{pt_low}_pthatup_{pt_up}.root"
        in_root_files = " ".join(root_files)
        cmd = f"hadd {out_root_file} {in_root_files}"
        cmds.append(cmd)
        out_dirs.append(merge_dir)
    run(cmds, merge_dir, n_jobs=args.jobs, cwds=out_dirs)

def sherpa(args):
    baseline_dir = abspath(join(args.output, "baseline"))
    run_card = abspath(args.run_card)
    #p = run_single(f"Sherpa -f {run_card} -e 1", baseline_dir)
    #p.wait()

    cmds = []
    for n_ev in compute_events_per_job(args.events, args.events_per_job):
        cmds.append(f"cp -r {baseline_dir}/* . && Sherpa -f {args.run_card} -e {n_ev} ; mv run.log runrun.log")
    run(cmds, args.output, n_jobs=args.jobs)


def main():
    """entry point"""

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("-j", "--jobs", type=int, help="number of parallel jobs", default=1)
    common_parser.add_argument("-o", "--output", help="output directory", default="simulations")
    common_parser.add_argument("--exec-dir", dest="exec_dir", help="directory where to find compiled generator executables", required=True)
    common_parser.add_argument("--events-per-job", type=int, help="number", default=1000)

    parser = argparse.ArgumentParser(description='Study MC event generators')

    sub_parsers = parser.add_subparsers(dest="command")
    
    pythia_parser = sub_parsers.add_parser("pythia-jets", parents=[common_parser])
    pythia_parser.add_argument("--pthard-low", dest="pthard_low", nargs="*", type=float, help="list of lower pT hard bins", default=[0.])
    pythia_parser.add_argument("--pthard-up", dest="pthard_up", nargs="*", type=float, help="list of upper pT hard bins", default=[1000.])
    pythia_parser.add_argument("--events-per-pthard", dest="events_per_pthard", nargs="*", type=int, help="how many events to be simulated per pT hard bin", default=[1000])
    pythia_parser.add_argument("--flavour", type=int, help="some flavour", default=1)
    pythia_parser.add_argument("--jet-radius", dest="jet_radius", type=float, help="jet radius", default=0.4)
    pythia_parser.add_argument("--mecorr", type=int, help="mecorr", default=1)
    pythia_parser.add_argument("--charged", type=int, help="charged", default=1)
    pythia_parser.add_argument("--unev", type=int, help="unev", default=1)
    pythia_parser.add_argument("--tune", type=int, help="tune", default=14)
    pythia_parser.add_argument("--number", type=int, help="number", default=-1)

    pythia_parser.set_defaults(func=pythia)

    sherpa_parser = sub_parsers.add_parser("sherpa", parents=[common_parser])
    sherpa_parser.add_argument("--run-card", dest="run_card", help="the Sherpa run card to be used", required=True)
    sherpa_parser.add_argument("--events", type=int, help="number", default=1000)

    sherpa_parser.set_defaults(func=sherpa)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return(args.func(args))

if __name__ == "__main__":
    sys.exit(main())
