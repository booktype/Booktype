#!/usr/bin/perl

=pod

Initially based on TWiki::UI::View for which the following copyright
notice applies:

# Copyright (C) 1999-2007 Peter Thoeny, peter@thoeny.org
# and TWiki Contributors. All Rights Reserved. TWiki Contributors
# are listed in the AUTHORS file in the root of this distribution.
# NOTE: Please extend that file, not this notice.
#
# Additional copyrights apply to some or all of the code in this
# file as follows:
# Based on parts of Ward Cunninghams original Wiki and JosWiki.
# Copyright (C) 1998 Markus Peter - SPiN GmbH (warpi@spin.de)
# Some changes by Dave Harris (drh@bhresearch.co.uk) incorporated
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version. For
# more details read LICENSE in the root of this distribution.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# As per the GPL, removal of this notice is prohibited.

=cut

use strict;
use warnings;
use integer;


BEGIN {
    # Set library paths in @INC, at compile time
    unshift @INC, '/home/douglas/fm-data/floss/bin/';
    require 'setlib.cfg';
}

require TWiki;

sub render_version {
    my ($webName, $topicName, $revision, $session, $raw) = @_;

    if (! $session){
        $session = new TWiki ('admin');
    }

    my ($meta, $text) = $session->{store}->readTopic($session, $webName, $topicName, $revision);

    if(! $raw) {
        $session->enterContext('body_text');
        $text = $session->handleCommonTags( $text, $webName, $topicName, $meta );
        $text = $session->renderer->getRenderedVersion( $text, $webName, $topicName );
        $session->leaveContext('body_text');
        $text =~ s/( ?) *<\/?(nop|noautolink)\/?>\n?/$1/gois;
    }

    return $text, $meta;
}

sub extract_all_versions {
    my ($webName, $topicName, $session) = @_;
    if (! $session){
        $session = new TWiki ('admin');
    }

    my ($text, $meta) = render_version($webName, $topicName, undef, $session);
    my ($date, $author, $rev) = $meta->getRevisionInfo();

    #Assume everything is 1.something
    print "rev is $rev\n";

    #$rev =~ m/^1\.(\d+)$/;
    #my $r = $1;
    my $r = $rev;

    my @versions;
    $versions[$r] = [$text, $meta, $rev];

    for ($r--; $r > 0; $r--){
        $rev = "1.$r";
        ($text, $meta) = render_version($webName, $topicName, $rev, $session);
        $versions[$r] = [$text, $meta, $rev];
    }

    return \@versions;
}



sub save_versions {
    my ($webName, $topicName, $dest) = @_;
    if (! -d $dest || ! -w $dest){
        die "'$dest' is not a writeable directory; it should be\n";
    }
    my $versions = extract_all_versions($webName, $topicName);

    foreach my $r (1 .. $#$versions){
        my $v = $versions->[$r];
        next unless defined $v;
        my ($text, $meta, $rev) = @$v;
        open FILE, '>', "$dest/$webName-$topicName.$r.txt";
        print FILE $meta->stringify . "\n$text\n";
        close FILE;
    }
}


save_versions @ARGV;
#save_versions "Inkscape", "Introduction", $ARGV[0];

