"""
FPG Trading System
"""

from lib.py.fpg.logger import get_module_logger
from lib.py.fpg.interface import Interface

logger = get_module_logger('core')


def main():
    """
        Main method that will setup the crypto trader,
        and the portfolio manager.
        This will initialize the portfolio manager which
        is in charge of the actual ticking
    """
    Interface()

if __name__=='__main__':
    main()
