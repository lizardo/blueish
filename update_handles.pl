#!/usr/bin/perl
# Shift attribute handles in order to insert attributes on existing services.
# Usage: perl -pi update_handles.pl data/file.yaml
# NOTE:
#  - Update $offset accordingly
#  - handles in attrbute values (e.g. READ_BY_TYPE_RSP PDUs) need to be updated
#    manually.

use strict;
use warnings;

sub replace {
	my $prefix = shift;
	my $offset = shift;

	if (!m/$prefix: (0x[0-9a-fA-F]+)/) {
		return;
	}
	if (hex($1) + $offset > 0xffff) {
		warn("Skip replacing to handle bigger than 0xffff: $_");
		return;
	}
	my $n = sprintf("0x%04x", hex($1) + $offset);
	s/$prefix: $1/$prefix: $n/g;
}

my $offset = 3;
replace(", end_handle", $offset);
replace("handle", $offset);
