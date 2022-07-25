# MCGeneratorStudy

A Python wrapper around different event generators for generator studies.

The wrapper has different sub-commands and at the moment there are 2.
1. pythia-jets,
1. sherpa

In general, to see all necessary/optional arguments of the wrapper, type
```bash
${PATH_TO_WRAPPER}/run.py <sub-command> --help
```

For all in common, there is the required argument `--exec-dir <path/to/executables>`. This is the directory where the wrapper assumes to find all executables such as `Pythia_Jets.exe`.

**NOTE** that the environment has to be properly set meaning that all required libraries for the invoked executable must be present.

## Setup

This wrapper was tested with Python version 3, it might work with some higher Python 2 versions. However, the time of Python 2 is over, so please consider using Python 3.
There is one Python dependency which is `psutil`. In general, it is good practise to setup a virtual anevironment, whenever one installs a custom package and its dependencies.
Follow these steps:
1. Create a Python virtual environment (only once) with `python3 -m venv <target/path/of/venv>`.
1. Enter the virtual environment with `source <target/path/of/venv>/bin/activate>
1. run necessary steps for software setup (exporting libraries etc) if needed, see also comments below.
1. Run whatever you want to run.

## On `aliceml`

On the `aliceml` machine the executables for the Pythia simulations are at `/home/nzardosh/PYTHIA_Sim/PYTHIA8_Simulations/Pythia_Simulations`.

Sherpa on the other hand does not need any executables for now because the Sherpa simulation is simply invoked by running the `Sherpa` executable with the run-card and the number of events.

## Example for Pythia

The following command
```bash
python3 ${PATH_TO_WRAPPER}/run.py pythia-jets --pthard-low 0 4 8 12 --pthard-up 4 8 12 24 --events-per-pthard 1001 2500 3000 4000 -j 5 --exec-dir /home/nzardosh/PYTHIA_Sim/PYTHIA8_Simulations/Pythia_Simulations/
```
runs `Pythia_jets.exe` for the 4 given mT-hard bins with 1001, 2500, 3000 and 4000 events, respectively. The number of parallel jobs is set to 5.

## Example for Sherpa

The following command
```bash
python3 ${PATH_TO_WRAPPER}/run.py sherpa --run-card <path/to/run_card> -j 10 --exec-dir /dummy/path/ --events 20000
```
runs `Sherpa` for 20,000 events in total. The execution is split such that there are 10 jobs maximum running in parallel. The `--exec-dir` gets a dummy path at the moment but it will be needed once there is an actual analysis executable defined to be run on the HepMC output.
Note that at the beginning, the simulation will take a bit longer because before the simulation, the required cross sections are explcictly computed.

## Generic options

Some of the most important generic command line options that refer to both the Pythia and Sherpa simulations:
* The top-level output directory can be chosen with the `--output <path/to/parent/output/dir>`. The default is `./simulations`.
* The number of parallel jobs is controlled by the `-j <n_parallel_jobs>`/`--jobs <n_prallel_jobs>` option. The default is `1`.
* The `--events-per-job <events_per_job>` limits the number of events per job to the given number of events. The default is `1000`.
