**DiversiFlyEngine V 0.1**


- run with main.py
- components in diversifly/components/core
- products/strategies in diversifly/components/products
- all future additional modules are in diversifly/components/modules

** Binance Python API Client **
- docs @ https://readthedocs.org/projects/python-binance/downloads/pdf/latest/ 

## deployment

* copy `.env.example` to `.env` and edit it according to your needs
* (if you're not in an anaconda environment): install dependencies with `pip3 install -r requirements.txt`
* run with `python3 main.py`

In order to deploy to tokyo:
* prepare a file `.env.tokyo` which contains the config for the Tokyo instance
* run `./deploy-to-tokyo.sh`

There's currently no convenient way for tracking dependencies and replicating them in a non-anaconda environment. Need to figure out.
In the meantime, ping Didi if it breaks after deployment or login with `ssh engine1@tokyo.dnd.d10r.net` and manually install a missing package with `pip3 install <pkg>`.
# crypto-derivative-trading-engine
