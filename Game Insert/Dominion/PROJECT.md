Create boxes that will work in existing box spaces (config.bay) to store
components from Dominion which are currently stored both there and in
the wooden bit box.  The wooden bit box will not be reused.

Create the two config.bay spaces, separate them in x/y space, and make
them 70% transparent.

Reuse the grab notch cut from ../BombBusters (secret mission tray) for the bit boxes in
Dominion.  The Dominion bit boxes have to be extracted vertically so
design them with a lid that can hold the pieces while storing and
retrieving.  Borrow the wall thickness from ../BombBusters as well.

Bulk components are under config.Components.metal and have a volume.
The volume given should be a box cutout shape but with one or two bottom
corners filleted significantly (r=5 or higher) to get the pieces out.

There are up to 6 players in the game.  There are 7 different player
mats. These all end in _mat in config.Components
* base
* exile
* coffers and villagers
* island
* ship
* sea
* favor

There is also a set of 'small' 80x80 mats unrelated to the per-player
sets.

Create a stack for each given the dimensions in config.  Also create a
stack per player with 1 of each mat.    Make sure that the mats are
aligned so that their 'y' is actually in the 'z' direction as that would
be how they would fit into the box.

config.Components.stars can be treated as bulk in 35x60x16

config.Components.player_pieces has three parts. minus_card_gold,
plus_tokens, and cube.  The cubes are wood and the others are cardboard,
they should be grouped into the smallest volume that will hold them all.


