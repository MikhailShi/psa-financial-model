# Implementation of Financial Modeling with Python

The initial case description and the model implementation in a jupyter notebook could be found according to the structure below:

<pre>
case description
|__ case sub-saharan psa.pdf
html
|__ psa_cashflow_projection.html
jupyter notebook
|__ psa_cashflow_projection.ipynb
jupyter notebook win
|__ mc_simulation.py
|__ psa_cashflow_projection.ipynb
requirements.txt
</pre>

To run a jupyter notebook one should install the nesessary python packages, i.e.:

``` bash
> conda create --name ENV_NAME python=3.6.9
> conda activate ENV_NAME
> pip install -r requirements.txt
```

To directly download an html version please follow this [Dropbox link](https://www.dropbox.com/s/fnumk7anx4zgg7j/psa_cashflow_projection.html?dl=1).

P.S. Due to specific jupyter notebook arrangement for the multiprocessing package ('spawn' start method), please use separate win version with the supplementary python file to import.