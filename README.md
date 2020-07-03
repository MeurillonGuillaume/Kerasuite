# Kerasuite

## Table of contents

1. [What is Kerasuite](#what-is-kerasuite)
2. [How does it work](#how-does-it-work)
    1. [Administrative functionalities](#administrative-functionalities)
    2. [Data projects](#data-projects)
3. [Getting started](#getting-started)
4. [Future features](#future-features)

## What is Kerasuite

Kerasuite is an open source visual web-based platform for Deep Learning development in Python3 using [Tensorflow Keras](https://github.com/tensorflow/tensorflow) and [Flask](https://github.com/pallets/flask).

## How does it work

### Administrative functionalities

Kerasuite comes with basic administrative functions that create a multi-user centralized platform for Deep Learning development.

Users with administrative roles can create and modify users, or revoke access.

### Data projects

Kerasuite is built around [Tensorflow.Keras](https://www.tensorflow.org/api_docs/python/tf/keras) and [Scikit-learn](https://scikit-learn.org/stable/).

Local datasets can be uploaded in projects, after which they can be used for data inspection, visualisation (using [Chart.js](https://www.chartjs.org/)) and/or preprocessing.

Properly preprocessed datasets can be used as training input for neural networks, that can easily and visually be created using the Kerasuite model builder. Creating models in Kerasuite requires 0 lines of user-written code.

## Getting started

### Installing Kerasuite

1. Download the [latest release](https://github.com/MeurillonGuillaume/Kerasuite/releases) of Kerasuite, or clone the `master` branch for the latest working version. Clone the `develop` branch if you are feeling a little more adventurous.
    ```shell script
    git clone https://github.com/MeurillonGuillaume/Kerasuite
    ```
2. Install all required Python packages:
    ```shell script
    cd Kerasuite
    pip3 install requirements.txt
    ```
3. Run Kerasuite:
    ```shell script
    python3 app.py
    ```
4. By default, Kerasuite comes with an administrative user-account that can be used to create, modify and delete other users. To access this account, use:
    ```text
   Name: admin
   Password: Kerasuite
   ```
   **Please change this password ASAP, you will be prompted to do so on each log-in with the default password**. After creating a second administrative user, you have the ability to remove this default `admin` account entirely. Doing so is best-practise.

## Future features

- Export complete trained models to embed in a production-ready environment;
- Iterate versions of generated models, which improves reverting changes and improves performance gain visualisation;
- Host created models directly as REST-based API in Kerasuite with the click of a button;
- Sharing projects between multiple users;
- Seeking for something else in Kerasuite? [Hit me up](mailto://guillaume.meurillon@hotmail.com) or create an [issue](https://github.com/MeurillonGuillaume/Kerasuite/issues)!
 