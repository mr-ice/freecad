dominion_symbols_v1_13/

extras/coins* for Bin_gold_coin adn Box_gold_coin
The coins have a "1" in the center.

extras/debt* for Bin_copper_debt and Box_gold_coin
The coins have an outer hex an inner hex which is raised on the coin
itself, and it has a "1" in the center.

The following create a victory point sheild shape for Bin_points and
Box_stars.  Normally left is Red and Right is Green, so put them in as
separate parts and I'll print with those colors.   The VP shield
normally has a number in the center - use "8" 
extras/left shield*
extras/right shield*
extras/shield*  
Need a similar but smaller on the top of Box_stars.

We need to create a SVG for a 7 pointed star for the Bin_Stars and
Box_Stars -- there is not one that I could find in any of the
dominion_symbols*. Similar on the top of Box_stars.

The Bin_kingdom_markers need an oval outline with a basic "Dominion"
logo in the middle.  Make it as large as possible but keep the relative
axis lengths.   dominion_symbols_v1_13/extras/dominion logo.svg is the
source.  Similar on the top of Box_stars.

dominion_logo_v1_0/dl_flat.svg goes on the outer (min-x) face of PlayerCase_Lid, as wide as
the face allows (config.LID_LOGO).

Each bulk row is two bins side by side (Bin_<key>_1 / _2), each with its own icons, and
every icon is sunk config.ICON_DEPTH (0.8 mm, minimum 0.6) into its host.

Simplified for printing: the coin is three parts (outer ring, inner shield outline, digit) and
the victory shield is two (its outline ring with the inside left hollow, and the digit).
