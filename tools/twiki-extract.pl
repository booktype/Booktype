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

use POSIX qw(strftime);
use Data::Dumper;

use constant FIND_EMAILS => 1;
use constant SEPARATOR => "\n------8<-----------------\n";

BEGIN {
    # Set library paths in @INC, at compile time
    unshift @INC, '/home/douglas/fm-data/floss/bin/';
    require 'setlib.cfg';
}

require TWiki;

my $DEFAULT_DOMAIN = 'flossmanuals.net';
#my $TWIKI_PATH = '/home/douglas/fm-data/twiki-data';
my $TWIKI_PATH = '/home/douglas/fm-data/import-tests/twiki-books';
my $STAGING_DIR = '/home/douglas/fm-data/import-tests/staging';

my @BAD_CHAPTERS = qw{WebAtom WebPreferences WebChanges WebRss
    WebCreateNewTopic WebSearchAdvanced WebHome WebSearch
    WebIndex WebStatistics WebLeftBar WebTopicList WebNotify
    WebTopicCreator WebTopicEditTemplate
};

my %BAD_BOOKS = map {($_ => 1)} qw{Main TWiki PR Trash Sandbox};



=pod

Get the text and metadata of a twiki page revision.  An attempt is
made to put the committers correct email in the metadata.

 render_version($webName, $topicName, $revision, $session, $raw) ==> ($text, $meta)

 * =$webName= the book.
 * =$topicName= the chapter.
 * =$session= a TWiki instance.  If undef, it will be created using the admin login.
 * =$revision= the required version (undef for the latest).
 * =$raw= is a flag to prevent the expansion of TWiki variables.

Return values:

 * =$text= the text of the chapter, with twiki tags filled out
 * =$meta= a TWiki::Meta object

=cut

sub render_version {
    my ($webName, $topicName, $revision, $session, $raw) = @_;

    $session ||= new TWiki('admin');

    my ($meta, $text) = $session->{store}->readTopic($session, $webName, $topicName, $revision);

    # Try to set the author's email to something sensible, if possible
    my $info = $meta->get('TOPICINFO');
    my $author = $info->{'author'};
    if (! defined $author){
        $author = 'Anonymous';
        print STDERR "Anonymous author on $webName.$topicName v$revision\n";
    }
    if (FIND_EMAILS){
        my $user = $session->{users}->findUserByWikiName($author);
        $info->{email} = $session->{users}->getEmails($user);
    }
    if (! $info->{email}){
        $info->{email} = "$author\@$DEFAULT_DOMAIN";
    }

    $info->{book} = $webName;

    if(! $raw) {
        $session->enterContext('body_text');
        $text = $session->handleCommonTags($text, $webName, $topicName, $meta);
        $text = $session->renderer->getRenderedVersion($text, $webName, $topicName);
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

    my $oldtext = 'Something to avoid annoying warnings';
    foreach (1 .. $head){
        my ($text, $meta) = render_version($webName, $topicName, $_, $session);
        if ($text ne $oldtext){
            $versions[$_] = [$text, $meta];
        }
        $oldtext = $text;
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
    my $book = shift || die "chapters of which book?";
    my $session = shift || new TWiki ('admin');

    my @chapters = grep {
        my $chapter = $_;
        $chapter =~ s/Talk$//;
        ! grep {$chapter eq $_} @BAD_CHAPTERS;
    } $session->{store}->getTopicNames($book);

    return @chapters;
}


=pod

 printer

Summary of a chapter revision to STDOUT.

=cut

sub printer {
    my ($text, $meta, $date, $title) = @_;
    my $info = $meta->get('TOPICINFO');
    my $s = sprintf ("%11s %20.20s %-5.5s %15.15s %.30s", $date, $title,
                     $info->{version}, $info->{author}, $text);
    $s =~ s/\n/ /g;
    print "$s\n";
};


sub staging_header {
    my $meta = shift;
    my $header = "chapter: $meta->{_topic}\n";
    my $info = $meta->get('TOPICINFO');
    foreach ('book', 'version', 'date', 'author', 'email'){
        if ($info->{$_}){
            $header .= "$_: $info->{$_}\n";
        }
    }
    $header .= "book2: $meta->{_web}\n";

    foreach my $type (qw {FILEATTACHMENT PREFERENCE TOPICPARENT FIELD TOPICMOVED}){
        next unless defined $meta->{$type};
        foreach my $item (@{$meta->{$type}}){
            $header .= "$type:";
            foreach my $k (sort keys %$item ){
                $header .= " '$k'='$item->{$k}'";
            }
            $header .= "\n";
        }
    }
    return $header;
}


=pod

Save a chapter in the staging directory.

=cut

sub stage_commit {
    my ($text, $meta, $date, $title) = @_;
    my $info = $meta->get('TOPICINFO');
    my $filename = sprintf ("%010d.%s.%s.%s", $date, $info->{book}, $title,
                            $info->{version});

    my $dir = $STAGING_DIR . '/' . strftime('%Y-%m', localtime($date));
    mkdir($dir) unless (-d $dir);

    my $fh;
    open ($fh, '>', "$dir/$filename");
    print $fh staging_header($meta);
    print $fh SEPARATOR;
    print $fh $text;
    close $fh;
}


=pod

 process_book

Given a book and a function reference, call the function on every
revision of every chapter of the book.

The function should take the arguments ($text, $meta, $date, $title).

=cut

sub process_book {
    my $book = shift;
    my $function = shift || \&printer;
    my $session = shift || new TWiki ('admin');

    my @chapters = get_chapters($book, $session);
    #print STDERR "@chapters\n";

    my %commits;

    for my $chapter (@chapters){
        #print STDERR "'$book' '$chapter'\n";
        my $versions = extract_all_versions($book, $chapter, $session);
        for my $v (@$versions){
            next unless defined $v;
            eval {
                my $date = $v->[1]->get('TOPICINFO')->{'date'};
                push @$v, $chapter;
                my @c;
                if (defined $commits{$date}){
                    @c = @{$commits{$date}};
                }
                push @c, $v;
                $commits{$date} = \@c;
            };
            if ($@){
                warn $@;
                print STDERR $v; #Dumper($v);
            }
        }
    }

    my @dates = sort {$a <=> $b} keys %commits;
    for my $date (@dates){
        for my $v (@{$commits{$date}}){
            my ($text, $meta, $title) = @$v;
            &$function($text, $meta, $date, $title);
        }
    }
}


sub process_repository {
    my $function = shift || \&printer;
    my $filter = shift || '.';
    my $session = shift || new TWiki ('admin');
    for my $book ($session->{store}->getListOfWebs){
        next if ($BAD_BOOKS{$book} || $book !~ /$filter/);
        print STDERR "'$book'\n";
        process_book($book, $function, $session);
    }
}


process_repository(\&stage_commit);
#process_book($ARGV[0], \&stage_commit);
#process_book($ARGV[0], \&printer);
#save_versions @ARGV;
#save_versions "Inkscape", "Introduction", $ARGV[0];

