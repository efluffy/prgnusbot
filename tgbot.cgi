#!/usr/bin/perl -wT 

use strict;
use CGI;
use LWP::UserAgent;
use JSON;
use Data::Dumper;

if($ENV{REMOTE_ADDR} !~ /149\.154\.(1(6[4-7]))\.([0-9]|[1-9][0-9]|1([0-9][0-9])|2([0-4][0-9]|5[0-5]))/) { print "Content-type: text/html\n\n"; exit(0); }

our $botid = "tgapi_bot_token";
our $inlineReply = "https://api.telegram.org/bot$botid/answerInlineQuery";

sub answerInlineQuery {
	my ($queryid, $query, $filename, $translation) = @_;
	my $res;
	my $ua = LWP::UserAgent->new( ssl_opts => { verify_hostname => 1 } );
	$filename =~ s/\.flac//;
	my $title = $filename;
	$title =~ s/(bd_|\.flac)//g;
	
	my %result;
	
	if($query eq "0" && $filename eq "0" && $translation eq "0") {
		%result = (
			"type" 	=> "article",
			"id" 	=> "1",
			"title" => "Nothing found!",
			"description" => "",
			"input_message_content" => {
				"message_text" => "Nothing found!",
			},
		);
	}
	else {
		%result = (
			"type" 	=> "voice",
			"id" 	=> "1",
			"voice_url" => "location_to_prgnus_files_in_opus_format",
			"title" => "$title",
			"caption" => "$query"
		);
	}
	
	$res = $ua->post($inlineReply, [
			"inline_query_id" => $queryid,
			"cache_time" => 1,
			"is_personal" => "true",
			"results" => to_json([\%result])
	]);
	
	if($res->code != 200) {
		open(my $fh, '>>', "debug.txt");
		my $dbgs = "SENT: " . "[\"inline_query_id\" => $queryid, \"results\" => ". to_json([\%result]) . "]\n";
		my $dbgr = "RECD: " . $res->code . ":" . $res->content . "\n";
		print $fh $dbgs;
		print $fh $dbgr;
		close($fh);
		die("telegram responded wrongly\n");
	}
}

open ( my $fh, "<", "prgnus.json" ) or die "Failure opening lookup JSON: $! \n";
my $jsonin = <$fh>;
close($fh);
my $json_dec = decode_json($jsonin);

my $q;
my $json;
my $queryid;
my $query;

$q = CGI->new;
print $q->header();
$json = decode_json( $q->param('POSTDATA') );

if(!defined($json->{inline_query}->{id})) { exit(0); }

$queryid = $json->{inline_query}->{id};
$query = $json->{inline_query}->{query};

$query =~ s/[^a-zA-Z0-9 ]//g;

if(!defined($query)) { exit(0); }

if($query ne "") {

	my $querys = "(" . join("|", split(" ", $query)) . ")";

	foreach my $file (@{$json_dec->{files}}) {
		for my $key (keys(%{$file})) {
			my $val = $file->{$key};
			my $trans = $val->{results}[0]->{alternatives}[0]->{transcript};
			if(defined($trans)) {
				if ($trans =~ m/$querys/) {
					answerInlineQuery($queryid, $query, $key, $trans);
					last;
				}
			}
		}
		answerInlineQuery($queryid, "0", "0", "0");
	}
}
exit(0);
