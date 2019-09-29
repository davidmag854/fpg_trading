# FPG Trading Demos and Systems

This contains a public repository to interact with and trade using the FPG system.
This software allows quantatative traders to trade in the crypto market using FPG's Smart Order Routing algos.
You only need to implement your strategies, the system allows backtesting, data delivery, and portfolio managment. 

To use this, follow the setup below to run the example strategy, then develop your own strategy within the `lib/py/strategies/<your strategy name>` folder and test it out.

## Setup:

1. virtualenv fpg_venv
2. source activate fpg_venv/bin/activate
3. python3 -m pip install -r requirements.txt (NEED TO UPDATE THIS, HAD BUGS)
4. Within the config directory, put a `debug.env` file.
Format of this should be:
 
Also place a `prod.env` file, but this will be used later.
 
## Setup (optional - Data):

Insert data_bundles from csv here.

# Run:
 
1. python3 core.py

This starts the main program.
 
