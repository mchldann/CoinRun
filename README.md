**Status:** Archive (code is provided as-is, no updates expected)

# Notes to Self

Looks like the training settings are in config.py.

The reward for each episode is 10, so an average episode return of 6.5 should be interpreted as a 65% success rate.

# Installing

conda create -n py36 python=3.6 anaconda

Good idea to make a clone at this point:
conda create --name py36clone --clone py36

source activate py36
pip install tensorflow-gpu==1.12.0

Good idea to make another clone at this point:
conda create --name py36clonetf --clone py36

Extra steps needed on old dev box:
conda install -c conda-forge scikit-build
conda install -c anaconda mpi4py

pip install -r requirements.txt
pip install -e .

Good idea to make *another* clone at this point:
conda create --name py36cloneprecudnn --clone py36

Somehow ended up with two versions of numpy installed at this point, one via conda, one via pip...
Had to run:
pip uninstall numpy

Then (to update):
conda install numpy

Then I had issues with qt, so:
conda install -c dsdale24 qt5

Need to make sure there's not a bunch of old built stuff (c++ or python) in the coinrun directory. Show hidden files, delete the build stuff and delete all the pycache stuff.

Now needed this critical bit, which I didn't see mentioned in the install notes! Basically have to install an appropriate version of cudnn:
conda install -c anaconda cudnn=7.1.2=cuda9.0_0


# Actually running

For some reason I was getting errors related to mpi4py... So:
conda install -c anaconda mpi4py

python -m coinrun.interactive (note: not actually running off the conda environment

or to train an agent:
python -m coinrun.train_agent --run-id myrun --save-interval 1

Then fire up TensorBoard!
tensorboard --logdir /tmp/tensorflow/myrun_0

# Quantifying Generalization in Reinforcement Learning

#### [[Blog Post]](https://blog.openai.com/quantifying-generalization-in-reinforcement-learning/) [[Paper]](https://drive.google.com/file/d/1U1-uufB_ZzQ1HG67BhW9bB8mTJ6JtS19/view)

This is code for the environments used in the paper [Quantifying Generalization in Reinforcement Learning](https://drive.google.com/file/d/1U1-uufB_ZzQ1HG67BhW9bB8mTJ6JtS19/view) along with an example training script.

Authors: Karl Cobbe, Oleg Klimov, Chris Hesse, Taehoon Kim, John Schulman

![CoinRun](coinrun.png?raw=true "CoinRun")

## Install

You should install the package in development mode so you can easily change the files.  You may also want to create a virtualenv before installing since it depends on a specific version of OpenAI baselines.

This environment has been used on Mac OS X and Ubuntu 16.04 with Python 3.6.

```
# Linux
apt-get install mpich build-essential qt5-default pkg-config
# Mac
brew install qt open-mpi pkg-config

git clone https://github.com/openai/coinrun.git
cd coinrun
pip install tensorflow==1.12.0  # or tensorflow-gpu
pip install -r requirements.txt
pip install -e .
```

Note that this does not compile the environment, the environment will be compiled when the `coinrun` package is imported.

## Try it out

Try the environment out with the keyboard:

```
python -m coinrun.interactive
```

If this fails, you may be missing a dependency or may need to fix `coinrun/Makefile` for your machine.

Train an agent using PPO:

```
python -m coinrun.train_agent --run-id myrun --save-interval 1
```

After each parameter update, this will save a copy of the agent to `./saved_models/`. Results are logged to `/tmp/tensorflow` by default.

Run parallel training using MPI:

```
mpiexec -np 8 python -m coinrun.train_agent --run-id myrun
```

Train an agent on a fixed set of N levels:

```
python -m coinrun.train_agent --run-id myrun --num-levels N
```

Train an agent on the same 500 levels used in the paper:

```
python -m coinrun.train_agent --run-id myrun --num-levels 500
```

Train an agent on a different set of 500 levels:

```
python -m coinrun.train_agent --run-id myrun --num-levels 500 --set-seed 13
```

Continue training an agent from a checkpoint:

```
python -m coinrun.train_agent --run-id newrun --restore-id myrun
```

Evaluate an agent's final training performance across N parallel environments. Evaluate K levels on each environment (NxK total levels). Default N=20 is reasonable. Evaluation levels will be drawn from the same set as those seen during training.

```
python -m coinrun.enjoy --train-eval --restore-id myrun -num-eval N -rep K
```

Evaluate an agent's final test performance on PxNxK distinct levels. All evaluation levels are uniformly sampled from the set of all high difficulty levels. Although we don't explicitly enforce that the test set avoid training levels, the probability of collisions is negligible.

```
mpiexec -np P python -m coinrun.enjoy --test-eval --restore-id myrun -num-eval N -rep K
```

Run simultaneous training and testing using MPI. Half the workers will train and half will test.

```
mpiexec -np 8 python -m coinrun.train_agent --run-id myrun --test
```

View training options:

```
python -m coinrun.train_agent --help
```

Watch a trained agent play a level:

```
python -m coinrun.enjoy --restore-id myrun --hres
```

Train an agent to play RandomMazes:

```
python train_agent.py --run-id random_mazes --game-type maze --use-lstm 1
```

Train an agent to play CoinRun-Platforms, using a larger number of environments to stabilize learning:

```
python train_agent.py --run-id coinrun_plat --game-type platform --num-envs 96 --use-lstm 1
```

There's an example random agent script in [`coinrun/random_agent.py`](coinrun/random_agent.py) which you can run like so:

```
python -m coinrun.random_agent
```

## Docker

There's also a `Dockerfile` to create a CoinRun docker image:

```
docker build --tag coinrun .
docker run --rm coinrun python -um coinrun.random_agent
```

## Colab

There's also a [Colab notebook](https://colab.research.google.com/drive/1e2Eyl8HANzcqPheVBMbdwi3wqDv41kZt) showing how to setup CoinRun.

See [LICENSES](ASSET_LICENSES.md) for asset license information.
