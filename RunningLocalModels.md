# Running Local Models

## Install 'unifree' and Active the Environment

### Linux/MacOS

```
git clone https://github.com/ProjectUnifree/unifree
cd unifree
./launch.sh
source venv/bin/activate
```

### Windows

```
git clone https://github.com/ProjectUnifree/unifree
cd unifree
launch.bat
.\venv\Scripts\activate.bat
```

## Install `ctranformers`

Please follow [the `ctransformers` GPU install guide](https://github.com/marella/ctransformers#gpu) to install to enable
Python bindings for the Transformer models on your local machine. We recommend using CUDA or Metal to increase
the inference speed.

## Use unifree as usual

(See main README.md for usage)[https://github.com/ProjectUnifree/unifree#installation-and-usage]. 
