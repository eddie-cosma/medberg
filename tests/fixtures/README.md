# Offline fixtures

All account numbers, item IDs, prices, customer names, and HTML are synthetic.
No fixture was downloaded from a customer account.

- `039A_012345678_0101.TXT` uses the currently supported ICS_039A row layout.
  It includes leading zeroes, a blank line, and three item records.
- `listing.html` contains the fields that the site parser reads, with two files
  and a table header. It is a minimal test page, not a copy of the live site.
- `login.html` and `login_failure.html` represent login responses.

Other filename specifications have filename tests, but do not yet have row
parsers. Add row fixtures when support for those specifications is added.
