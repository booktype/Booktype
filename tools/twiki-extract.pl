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

(That last claim seems dubious, but there you go).

=cut

use strict;
use warnings;
use integer;

use constant FIND_EMAILS => 1;

BEGIN {
    # Set library paths in @INC, at compile time
    unshift @INC, '/home/douglas/fm-data/floss/bin/';
    require 'setlib.cfg';
}

require TWiki;

my $DEFAULT_DOMAIN = 'flossmanuals.net';
my $TWIKI_PATH = '/home/douglas/fm-data/twiki-data';

my @BAD_CHAPTERS = qw{WebAtom WebPreferences WebChanges WebRss
    WebCreateNewTopic WebSearchAdvanced WebHome WebSearch
    WebIndex WebStatistics WebLeftBar WebTopicList WebNotify
    WebTopicCreator WebTopicEditTemplate
};


=pod

 render_version($webName, $topicName, $revision, $session, $raw) = @_;
   ==> ($text, $meta)

 * =$webName= the book.
 * =$topicName= the chapter.
 * =$session= a TWiki instance.  If undef, it will be created.
 * =$revision= the required version (RCS style "1.\d+", undef for the latest).

Return values:

 * =$text= the text of the chapter, with twiki tags filled out
 * =$meta= a TWiki::Meta object
=cut

sub render_version {
    my ($webName, $topicName, $revision, $session, $raw) = @_;

    if (! $session){
        $session = new TWiki ('admin');
    }

    my ($meta, $text) = $session->{store}->readTopic($session, $webName, $topicName, $revision);

    # Try to set the author's email to something sensible, if possible
    my $info = $meta->get('TOPICINFO');
    my $author = $info->{'author'};
    if (FIND_EMAILS){
        my $user = $session->{users}->findUserByWikiName($author);
        $info->{email} = $session->{users}->getEmails($user);
    }
    $info->{email} ||= "$author\@$DEFAULT_DOMAIN";

    if(! $raw) {
        $session->enterContext('body_text');
        $text = $session->handleCommonTags( $text, $webName, $topicName, $meta );
        $text = $session->renderer->getRenderedVersion( $text, $webName, $topicName );
        $session->leaveContext('body_text');
        $text =~ s/( ?) *<\/?(nop|noautolink)\/?>\n?/$1/gois;
    }

    return $text, $meta;
}

=pod
    extract_all_versions($webName, $topicName, $session)

Find all revisions of the chapter $topicName in book $webName and put
them in an array indexed by revision numbers.  Return the arrays as a
reference.

Version 0 is undefined.

=cut

sub extract_all_versions {
    my ($webName, $topicName, $session) = @_;
    if (! $session){
        $session = new TWiki ('admin');
    }

    my $head = $session->{store}->getRevisionNumber($webName, $topicName);
    #my @versions = ['', new TWiki::Meta($session, $webName, $topicName)];
    my @versions;

    foreach (1 .. $head){
        my ($text, $meta) = render_version($webName, $topicName, $_, $session);
        $versions[$_] = [$text, $meta];
    }
    return \@versions;
}

=pod
    save_versions($webName, $topicName, $dest)

Save versions of chapter $topicName of book $webName in files in the
directory $dest.  Their names are structured thus:

  $dest/$topicName.$revision_number.txt

$dest ought to exist.  Files will be overwritten.

=cut

sub save_versions {
    my ($webName, $topicName, $dest) = @_;
    if (! -d $dest || ! -w $dest){
        die "'$dest' is not a writeable directory; it should be.\n";
    }
    my $versions = extract_all_versions($webName, $topicName);

    foreach my $r (1 .. $#$versions){
        my $v = $versions->[$r];
        next unless defined $v;
        my ($text, $meta) = @$v;
        open FILE, '>', "$dest/$webName-$topicName.$r.txt";
        print FILE $meta->stringify . "\n$text\n";
        close FILE;
    }
}


=pod
    get_chapters

Find all the real chapters in the repository.  TWiki will have made a
number of unused pages by default: these are filtered out.

=cut

sub get_chapters {
    my $book = shift;

    opendir(DIR, "$TWIKI_PATH/$book") || die "could not open directory '$TWIKI_PATH/$book'";
    my @chapters = grep {
        my $chapter = $_;
        s/\.txt$// && ! grep {$chapter =~ /^$_(Talk)?\./} @BAD_CHAPTERS;        
    } readdir(DIR);
    closedir(DIR);
    #print "@chapters\n";
    return @chapters;
}

=pod

 commit_versions

Extract all versions of each file and commit them in creation order.
This is a bit harder than doing each file at a time, but it will make
the git history more useful.

=cut

sub commit_versions {
    my $book = shift;
    my $session = shift || new TWiki ('admin');

    my @chapters = get_chapters($book);
    print "@chapters\n";

    my %commits;

    for my $chapter (@chapters){
        print "'$book' '$chapter'\n";
        my $versions = extract_all_versions($book, $chapter, $session);
        #print $versions, @$versions, "-------\n";
        #print join '-', @$versions, '-';
        for my $v (@$versions){
            next unless defined $v;
            #print $v;
            #print @$v, "\n";
            my $date = $v->[1]->get('TOPICINFO')->{'date'};
            push @$v, $chapter;
            my @c;
            if (defined $commits{$date}){
                @c = @{$commits{$date}};
            }
            push @c, $v;
            $commits{$date} = \@c;
        }
    }

    my @dates = sort {$a <=> $b} keys %commits;
    for my $date (@dates){
        for my $v (@{$commits{$date}}){
            my ($text, $meta, $chapter) = @$v;
            my $info = $meta->get('TOPICINFO');
            print "$date, $chapter, $info->{'version'},  $info->{'author'}", "\n";
        }
    }
}

#chdir $TWIKI_PATH;

commit_versions @ARGV;
#save_versions @ARGV;
#save_versions "Inkscape", "Introduction", $ARGV[0];

