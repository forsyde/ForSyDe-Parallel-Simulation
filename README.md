# ForSyDe-Parallel-Simulation
An automated parallel simulation flow for ForSyDe models.

The tool is implemented as a set of python scripts.
Some of them realize different pieces of the simulation flow and some act as top-level scripts that invoke other ones.

In addition reference implementation of key parts of the flow including model partitioning is provided in the ATL folder which is intended to be used in conjunction with model injectors, transformations, and code generation plugins provided by the [ForSyDe-Eclipse](https://github.com/forsyde/ForSyDe-Eclipse/) project

To run the flow, in addition to a Python installation you will need
- [ForSyDe-SystemC](https://github.com/forsyde/ForSyDe-SystemC)
- [Metis](http://glaros.dtc.umn.edu/gkhome/metis/metis/overview)
- [PaGrid](https://code.google.com/archive/p/pagrid)
- [SDF3](http://www.es.ele.tue.nl/sdf3/)
- [MiniZinc](https://www.minizinc.org/) with the [OR Tools](https://developers.google.com/optimization) solver backend [configured properly](https://www.minizinc.org/doc-2.3.2/en/installation_detailed_linux.html#or-tools).
- An active MPI installation such as [Open MPI](https://www.open-mpi.org/)

In the simplest case, you can use the `partition-sdf-synthetic.py` script in the `fparsim` directory to run the flow with synthetic benchmarks of different sizes generated with SDF3 using different partitioning algorithms.
Note that this is a Python 2 script.

Example of models for heterogeneous platforms are provided in the `platforms` folder.
