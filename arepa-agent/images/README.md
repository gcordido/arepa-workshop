# Handwritten catering image

Supply `catering-order.jpg` before the workshop. Do not reuse the cupcake photo.

The note should match [the prepared extraction](../examples/request.json):
Eugenia, seven Catira, Pernil crossed out for three Pelua, twenty-eight
Reina Pepiada, and the margin note `No nuts please!`. Use tally marks.
The quantities deliberately trigger the retail bulk-order policy.

Strip EXIF metadata, especially GPS coordinates. Rehearse
`python catering.py images/catering-order.jpg` on the configured deployment
and check exact quantities, corrections, allergy notes and uncertainties.
The JSON fallback does not test vision.
