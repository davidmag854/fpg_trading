# Main directory of python source code

This has two modules:

## fpg

These are Floating Point Group provided files that serve as the underlying infrastructure and  methods of running strategies.

Mostly this folder can be ignored.

## strategies

In each folder there are three files:
- `<strategy>.py` - Defines the strategy, and logic of buying/selling.
- `portfolio.py` - Defines the logic of what strategies to activate and focus on.
- `risk_manager.py` - Defines how much to buy/sell.

To create/run a new strategy, make a new folder here and update the files appropriately.