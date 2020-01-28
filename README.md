# Introduction


## Code Organization
This project is accomplished by extending the QuantConnect's framework to implement a smart beta algorithm. The source code can be found under the <code>src</code> folder. Below is the structure of the code organization:

<pre>
requirements.txt
notebook
|__ psa_cashflow_projection
case
|__ case_scan.pdf
</pre>

## Environment
### Cloud
As mentioned above, as part of the research for our project, we have used the QuantConnect platform. QuantConnect provides its framework to write our own algorithms either on the cloud at https://www.quantconnect.com/terminal/ or by downloading and using the QuantConnect's Lean engine locally. In either case, the implementation remains pretty much the same. We performed most of our analysis on the cloud because of the availability of large US equity datasets. We have also used the local Lean engine to test the custom dollar bars we generated using the tick data we obtained for some stocks on Russian stock exchange.

### Desktop
For some parts of this project we also need a local Python environment. To create python environment one needs to use **anaconda**. The ```requirements.txt``` lists all the Python packages that we have used for the purpose of this research. The script below sets up the environment. This environment will be used for running Python scripts in our **Tick Data Strategies** as well as the QuantConnect's **LEAN** (desktop) Engine.

> Note: This environment should be built on Python version 3.6.

``` bash
> conda create --name QC python=3.6.6
> conda activate QC
> pip install -r requirements.txt
```
