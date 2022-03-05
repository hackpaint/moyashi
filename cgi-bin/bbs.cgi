#!/usr/bin/perl

use strict;

use CGI::Carp qw(fatalsToBrowser);

use CGI;
$CGI::LIST_CONTEXT_WARN = 0;
my $cgi = new CGI;
use URI::Escape;
use File::Temp 'tmpnam';
use File::Basename 'basename';
use Time::Local;
use List::Util 'max';
use Encode 'from_to';
use Unicode::Japanese qw(unijp);
use MIME::Base64;

# ホストの gzip のパス
my $gzip = '/bin/gzip';

# 自動リロードさせる秒数
my $refresh_seconds = 120;

# 未読数を集計して末端に出力、.js に投げる
my $newercount = 0;

# 設定ファイルの読み込み
my $server = $ENV{SERVER_NAME};
goto404() if !(-e "${server}.txt");
my %conffiles = read_config("${server}.txt");
my %default_messages = read_config('messages.txt');
my %messages = read_config($conffiles{messages});
my %default_parameters = read_config('parameters.txt');
my %parameters = read_config($conffiles{parameters});
my %default_securities = read_config('securities.txt');
my %securities = read_config($conffiles{securities});

my %cookie = read_cookie();

# グローバルワンショット変数群
my $argrewind = arg('rewind');
my $argtree = arg('tree');
my $argtrad = arg('trad');
my $argexp = arg('exp');
if(!$argtree && !$argtrad && !$argexp)
{
  $argtree = '1' if $cookie{DISPLAY} eq 'tree';
  $argtrad = '1' if $cookie{DISPLAY} eq 'trad';
  $argexp = '1' if $cookie{DISPLAY} eq 'exp';
}
#$argexp = '1' if $argtrad == 0 && $argtree == 0 && $argexp == 0;
my $argautoreload = arg('autoreload');
my $argbgcolor = arg('bgcolor');
$argbgcolor = $cookie{BGCOLOR} if $cookie{BGCOLOR} ne '';
my $argzoom = arg('zoom');
my $argtarget = arg('target');
$argtarget = $cookie{TARGET} if $cookie{TARGET} ne '';
my $argadmin = arg('admin');
my $argarticles = arg('articles');
$argarticles = $cookie{ARTICLES} if $cookie{ARTICLES} ne '';
my $arginfo = 'false';
# my $arginfo = 'true';
# $arginfo = $cookie{INFO} if $cookie{INFO} ne '';
# $arginfo = arg('info') if arg('info') ne '';
my $argghost = arg('ghost');
my $globaldate = now_date();
my $globaltime = now_time();
my $globaladdress = $ENV{'REMOTE_ADDR'};
my @globaladdr = split(/\./, $globaladdress);
my $globalip = pack("C4", $globaladdr[0], $globaladdr[1], $globaladdr[2], $globaladdr[3]);
my $globalhost = gethostbyaddr($globalip, 2);
my $globaltmpnam = tmpnam();

# 設定ファイル群を一つにまとめる
my %default_conffiles = (%default_messages, %default_parameters, %default_securities);
my %conffiles = (%messages, %parameters, %securities);
my %configs = %default_conffiles;
$configs{$_} = $conffiles{$_} foreach(keys(%conffiles));

goto404() if is_attack();
goto404() if is_ngident();
goto404() if $globaladdress eq "153.205.226.216";

# my %logcache;

# 設定ファイルからの複写
my $adminname = $configs{username};
my $pass = $configs{password};
my $default_articles = $configs{defaultarticles};
my $default_imode_articles = $configs{defaultimodearticles};
my $logprefix = $configs{logprefix};
my $logpostfix = $configs{logpostfix};
my $audiences_filename = $configs{audiencesfilename};
my $audiences_seconds = $configs{audiencesseconds};
my $writers_filename = $configs{writersfilename};
my $writers_seconds = $configs{writersseconds};
my $write_limit_count = $configs{writelimitcount};
my $counterlevel = $configs{counterlevel};
my $counterprefix = $configs{counterprefix};
my $nazo = $configs{nazoflag};
my $ghosts_filename = $configs{ghostsfilename};
my $ghostprefix = $configs{ghostprefix};

# 全板なぞ化
$nazo = 1;

# ghostbbs か ghost ならマークする
my $ghost = 0;
if($ghostprefix ne '')
{
  if($argghost ne '')
  {
    $ghost++;
  }
  else
  {
    my @lines = read_textfile($ghosts_filename);
    chomp(@lines);
    foreach(@lines)
    {
      $ghost++ if $globalhost =~ /$_/;
    }
  }
}
$ghost = 0 if arg('noghost') ne '';

# 背景画像のファイル名を得る
# ファイル名が空なら表示しない
my $bgname;
my $bgdirectory = $configs{bgdirectory};
my @bgnames;
if($configs{bgnames} ne '')
{
  @bgnames = split(/:/, $configs{bgnames});
  $bgname = $bgnames[$cookie{ZYOJINUMBER}];
}

# カウンタの加算
increment_counter();

# 新書き込みの色などを変えるためのクラス
my $class_hot = 'newitem';

# タイトルタグの指定がなければ通常タイトルをコピー
$configs{titletag} = $configs{title} if $configs{titletag} eq "";

# 最新%d件、の置換
$configs{newerreload} =~ s/%d/$default_articles/;

# 表示時文字列の置換設定の読み込み
my @replaces = read_textfile($configs{replaces});
chomp(@replaces);

# スマホ判定
#my $smartphone = $ENV{HTTP_USER_AGENT} =~ /(iPhone|Android)/;
my $smartphone = $ENV{HTTP_USER_AGENT} =~ /iPhone/;
$smartphone += uri_unescape($cgi->param('smartphone')) ne "" ? 1 : 0;

# iPhone判定
my $iphone = $ENV{HTTP_USER_AGENT} =~ /iPhone/;
$iphone += uri_unescape($cgi->param('iphone')) ne "" ? 1 : 0;

# trad と exp の関係性
my ($trad, $exp, $modelock);

if(!$argtree && !$argtrad && !$argexp)
{
  if($configs{defaultmode} eq 'tree')
  {
    $trad = 0;
    $exp = 0;
    $modelock = 1;
  }
  elsif($configs{defaultmode} eq 'trad')
  {
    $trad = 1;
    $exp = 0;
    $modelock = 1;
  }
  elsif($configs{defaultmode} eq 'exp')
  {
    $trad = 0;
    $exp = 1;
    $modelock = 1;
  }
}

if($argtree)
{
  $trad = 0;
  $exp = 0;
}
elsif($argtrad)
{
  $trad = 1;
  $exp = 0;
}
elsif($argexp)
{
  $trad = 0;
  $exp = 1;
}
else
{
  if(!$modelock)
  {
    $trad = 1;
    $exp = 0;
  }
}

# (なぞの互換表時強制を 0 でキャンセルした)
if($nazo && 0)
{
  $trad = 1;
  $exp = 0;
}

# スマートフォンでは実験表示は禁止する
if($smartphone)
{
  $exp = 0;

  # しかしなぞでは互換表示強制(0 でキャンセルした)
  if($nazo && 0) {
    $trad = 1;
    $exp = 0;
  }
}

my $imode = uri_unescape($cgi->param('i')) ne "" ? 1 : 0;

my $zeroreload = 0;
my $newerreload = 0;

my $trad_res_depth = 3;

my $nowbgcolor = '#' . ($argbgcolor ne "" ? $argbgcolor : $configs{bgcolor});

imode_main() if $imode;
# config() if uri_unescape($cgi->param('mode')) eq 'config';

main();
exit();

# 設定ファイルを読み込む
# 一行に一項目、コンマ区切りでキー/値のペアが書いてある
# 空白行と先頭文字 # の行は無視
sub read_config
{
  my %dst;
  open(IN, '<' . shift);
  while(<IN>)
  {
    if($_ ne "" && $_ !~ /^#/)
    {
      $_ =~ s/\x0d?\x0a?$//;
      my ($key, $value) = split(/,/, $_, 2);
      $dst{$key} = $value;
    }
  }
  close(IN);
  return %dst;
}

# テキストファイルを単純に読み込む
sub read_textfile
{
  open(IN, '<' . shift);
  my @lines = <IN>;
  close(IN);
  return @lines;
}

# カウンタのファイル名を組み立てる
# ファイルの位置名称を変えるならここだけをいじる
sub make_counter_name
{
  my $name = shift;
  return $configs{counterprefix} . $name . '.txt';
}

# カウンタファイルを一つ読み込む
# ファイルにテキストで書き込まれている数値を返す
# ファイルが存在しなければ 0 を返す
sub read_counters
{
  my $filename = make_counter_name(shift);
  my $count = 0;
  if(-e $filename)
  {
    open(IN, '<' . $filename);
    flock(IN, 1);
    $count = <IN>;
    close(IN);
  }
  return $count;
}

# カウンタファイルを一つ書き込む
sub write_counters
{
  my ($num, $count) = @_;
  my $filename = "counter$num.txt";
  open(OUT, '>' . make_counter_name($num));
  flock(OUT, 2);
  print OUT $count;
  close(OUT);
}

# カウンタファイル群が持つ一番大きい数値に 1 加算し、
# すべてのカウンタファイルにその値を書き込む
sub increment_counter
{
  my @count;
  $count[$_] = read_counters($_) foreach(1..$counterlevel);
  my $max = max(@count);
  $max++;
  write_counters($_, $max) foreach(1..$counterlevel);
}

# カウンタファイル群が持つ一番大きい数値を返す
sub get_counter
{
  my @count;
  $count[$_] = read_counters($_) foreach(1..$counterlevel);
  return max(@count);
}

# 書き込み制限リストの該当数を返す
sub get_writer
{
  my $address = shift;
  my @writers = read_writers();
  my $datetime = now_seconds();
  my $writer = $datetime . ',' . $address;
  @writers = limit_writer($datetime, $writers_seconds, @writers);
  write_writers(@writers);
  return count_writer($writer, @writers);
}

# 書き込み制限リストファイルを読み込む
sub read_writers
{
  open(IN, '<' . $writers_filename);
  flock(IN, 1);
  my @lines = <IN>;
  close(IN);
  chomp(@lines);
  return @lines;
}

# 書き込み制限リストファイルを書き出す
sub write_writers
{
  my @lines = @_;
  open(OUT, '>', $writers_filename);
  flock(OUT, 2);
  print OUT $_ . "\n" foreach(@lines);
  close(OUT);
}

# 書き込み制限リストにIPを追加する
sub append_writer
{
  my ($writer, @writers) = @_;
  push(@writers, $writer);
  return @writers;
}

# 書き込み制限リストファイルにIPを追加する
sub append_writer_file
{
  my $address = shift;
  my @writers = read_writers();
  my $datetime = now_seconds();
  my $writer = $datetime . ',' . $address;
  @writers = append_writer($writer, @writers);
  write_writers(@writers);
}

# 書き込み制限リストから指定時間経過したエントリを取り除く
sub limit_writer
{
  my ($datetime, $limit, @writers) = @_;
  my @list;
  foreach(@writers)
  {
    my ($indatetime, $inip) = split(/,/, $_);
    push(@list, $_) if $datetime - $indatetime <= $limit;
  }
  return @list;
}

# 書き込み制限リスト内に存在する指定IPの総数を返す
sub count_writer
{
  my ($writer, @writers) = @_;
  my ($datetime, $ip) = split(/,/, $writer);
  my $count = 0;
  foreach(@writers)
  {
    my ($indatetime, $inip) = split(/,/, $_);
    $count++ if $inip eq $ip;
  }
  return $count;
}

# 観客数を得る
sub get_audiences
{
  my @audiences = read_audiences();
  my $datetime = now_seconds();
  my $audience = $datetime . ',' . $globaladdress . ',' . $globalhost;
  @audiences = unique_audiences($audience, $audiences_seconds, @audiences);
  write_audiences(@audiences);
  return scalar(@audiences);
}

# bot 数を得る
sub get_bot
{
  my @audiences = read_audiences();
  my @hosts = map { (split(/,/, $_))[2] } @audiences;
  my @list = read_textfile($configs{botsfilename});
  chomp(@list);
  my $bots;
  my $hostlist = join(' ', @hosts);
  foreach(@list)
  {
    $bots += () = $hostlist =~ m/$_/g;
  }
  return $bots;
}

# bot の内訳を得る
sub get_bots
{
  my @audiences = read_audiences();
  my @hosts = map { (split(/,/, $_))[2] } @audiences;
  my @list = read_textfile($configs{botsfilename});
  chomp(@list);
  my %names;
  $names{$_} = 0 foreach(@list);
  my $hostlist = join(' ', @hosts);
  foreach(@list)
  {
    $names{$_} = () = $hostlist =~ m/$_/g;
  }
  return %names;
}

# 攻撃数を得る
sub get_attack
{
  my @audiences = read_audiences();
  my @hosts = map { (split(/,/, $_))[2] } @audiences;
  my @list = read_textfile($configs{attacksfilename});
  chomp(@list);
  my $attacks;
  my $hostlist = join(' ', @hosts);
  foreach(@list)
  {
    $attacks += () = $hostlist =~ m/$_/g;
  }
  return $attacks;
}

# 攻撃数の内訳を得る
sub get_attacks
{
  my @audiences = read_audiences();
  my @hosts = map { (split(/,/, $_))[2] } @audiences;
  my @list = read_textfile($configs{attacksfilename});
  chomp(@list);
  my %names;
  $names{$_} = 0 foreach(@list);
  my $hostlist = join(' ', @hosts);
  foreach(@list)
  {
    $names{$_} = () = $hostlist =~ m/$_/g;
  }
  return %names;
}

# 引けないIPの数を得る
sub get_unknown
{
  my @audiences = read_audiences();
  my @hosts = map { (split(/,/, $_))[2] } @audiences;
  return scalar(@audiences) - scalar(@hosts);
}

# 観客数管理ファイルを読み込む
sub read_audiences
{
  open(IN, '<' . $audiences_filename);
  flock(IN, 1);
  my @lines = <IN>;
  close(IN);
  chomp(@lines);
  return @lines;
}

# 観客数管理ファイルを書き出す
sub write_audiences
{
  my @lines = @_;
  open(OUT, '>' . $audiences_filename);
  flock(OUT, 2);
  print OUT $_ . "\n" foreach(@lines);
  close(OUT);
}

# 観客数を増減する
sub unique_audiences
{
  my ($audience, $limit, @audiences) = @_;
  my ($datetime, $ip, $host) = split(/,/, $audience);
  my %dic;
  foreach(@audiences)
  {
    my ($indatetime, $inip, $inhost) = split(/,/, $_);
    $dic{$inip . ',' . $inhost} = $indatetime;
  }
  $dic{$ip . ',' . $host} = $datetime;
  my @newaudiences;
  foreach(keys(%dic))
  {
    if($datetime - $dic{$_} <= $limit)
    {
      push(@newaudiences, $dic{$_} . ',' . $_);
    }
  }
  return @newaudiences;
}

# 現在の総秒数を得る
sub now_seconds
{
  my $date = $globaldate;
  my $time = $globaltime;
  my $year = substr($date, 0, 4);
  my $month = substr($date, 4, 2) - 1;
  my $day = substr($date, 6, 2);
  my $hour = substr($time, 0, 2);
  my $minute = substr($time, 2, 2);
  my $second = substr($time, 4, 2);
  return timelocal($second, $minute, $hour, $day, $month, $year);
}

# 指定した URL パラメータをデコードして返す
sub arg
{
  return uri_unescape($cgi->param(shift));
}

# 板で指定されたアーティクル数を返す
# 指定がなければ $default_articles を返す
# ０件リロードのセッションでは０を返す
# 最新リロードのセッションでは $default_articles を返す
sub get_articles
{
  my $articles = $argarticles;
  $articles = $default_articles if $articles eq undef;
  $articles = 0 if $zeroreload;
  $articles = $default_articles if $newerreload;
  return $articles;
}

# 板の現在の下端表示に使ったページ番号を返す
sub get_pages
{
  my $pages = arg('pages');
  $pages = 1 if $pages eq undef;
  return $pages;
}

# 掲示板メインルーチン
sub main
{
  my $mode = arg('mode');
  configed() if $mode eq $configs{configchange};

  if($ghost)
  {
    $logprefix = $ghostprefix;
    post() if $mode eq $configs{postbutton};
    post() if $mode eq $configs{postreloadbutton};
    warata();
  }
  else
  {
    post() if $mode eq $configs{postbutton};
    post() if $mode eq $configs{postreloadbutton};
    warata();
    if($ghostprefix ne '')
    {
      my $savelogprefix = $logprefix;
      $logprefix = $ghostprefix;
      post() if $mode eq $configs{postbutton};
      post() if $mode eq $configs{postreloadbutton};
      warata();
      $logprefix = $savelogprefix;
    }
  }

  res() if $mode eq 'res';
  disp() if $mode eq 'display';
  del() if $mode eq 'delete';
  amend() if $mode eq 'amend';
  $zeroreload = 1 if arg('reload') eq $configs{zeroreload};
  $newerreload = 1 if arg('newer') eq $configs{newerreload};
  print_content_type();
  if (arg('newerdisp') ne '')
  {
    print_tree();
    print_newercount();
    printfl(make_lastreloadtime());
    printfl('<script type="text/javascript" src="newer.js"></script>');
  }
  else
  {
    print_header($argautoreload ne "" ? 1 : 0);
    printfl($configs{infoline});
    printfl('<span id="newerline" class="newerline"></span>');
    print_inputforms() if $argautoreload eq "";
    printfl('<hr>');
    printfl('<span id="linklines">');
    print_normalboard() if $argautoreload ne "";
    if(!$argautoreload)
    {
      print_linkline();
      if(!$smartphone)
      {
      printfl('<hr>');
      print_notice();
      }
      printfl('<hr>') if $trad || $exp;
    }
    printfl('</span>');
    printfl('<script type="text/javascript" src="fernandes.js"></script>');
    printfl('<script type="text/javascript" src="tinyflip.js"></script>');
    printfl('<div class="content">');
    $trad ? print_flat() : print_tree();
    printfl('</div>');
    print_next(get_articles(), get_pages() + 1);
    print_newercount();
    print_footer();
    print_closer();
  }
}

# .js に渡す新規書き込み数を出力する
sub print_newercount
{
  printfl(sprintf('<span id="newercount" value="%d"></span>', $newercount));
}

# content-type を出力する
# 圧縮できる条件が揃っていたら圧縮ストリームを設定する
sub print_content_type
{
  if($ENV{'HTTP_ACCEPT_ENCODING'} =~ /gzip/)
  {
    print("Content-type: text/html; charset=UTF-8\n");
    if($ENV{'HTTP_ACCEPT_ENCODING'} =~ /x-gzip/)
    {
      print("Content-encoding: x-gzip\n\n");
    }
    else
    {
      print("Content-encoding: gzip\n\n");
    }
    open(STDOUT, "| $gzip -1 -c");
  }
  else
  {
    print("Content-type: text/html; charset=UTF-8\n\n");
  }
}

# HTML ヘッダ出力
sub print_header
{
  my $autoreloadflag = shift;
  my $zoom = sanitize($argzoom);
  $zoom = 2 if $smartphone;
  $zoom = 1 if $zoom eq undef;
  my $articlezoom;
  $articlezoom = ".article { font-size: ${zoom}em; }" if $zoom != 1;
  my $reszoom;
  $reszoom = ".res { font-size: ${zoom}em; }" if $zoom != 1;
  my $tradcontentzoom;
  $tradcontentzoom = ".tradcontent { font-size: ${zoom}em; }" if $zoom != 1;
  my $datetimezoom;
  my $smallzoom = $zoom * 0.9;
  $datetimezoom = ".datetime { font-size: ${smallzoom}em; }" if $zoom != 1;
  my $tradreszoom;
  $tradreszoom = ".tradres { font-size: ${zoom}em; }" if $zoom != 1;
  my $articlepadding;
  $articlepadding = ".article { padding: 0; }" if $zoom != 1;
  my $refresher;
  $refresher = "<meta http-equiv='refresh' content='$refresh_seconds'>" if $autoreloadflag;
  my $bodysmall;
  $bodysmall = ".article { font-size: 9pt; }" if $exp;
  my $reslinknone;
  $reslinknone = "a.res { text-decoration: none; }" if $exp;
  my $modeid;
  $modeid = '<span id="tree"></span>';
  $modeid = '<span id="trad"></span>' if $trad;
  $modeid = '<span id="exp"></span>' if $exp;
  my $iphoneheight;
  $iphoneheight = "body { line-height: 1em; }" if $iphone;
  my $extendparam = '<span id="extendparam" value="';
# $extendparam .= $arginfo eq 'true' ? 'info' : 'noinfo';
  $extendparam .= 'noinfo';
  $extendparam .= ',' . scalar(@bgnames);
  $extendparam .= '"></span>';
  my $rightbottomimg;
  $rightbottomimg = "<img src=\"$bgdirectory$bgname\" style=\"position: fixed; right: 0; bottom: 0; z-order: 1;\">" if !$smartphone;
  my $lastreload = make_lastreloadtime();
  my $righttopselector = '<div style="float:right" id="zoomer"></div>';
  my $smartid;
  $smartid = '<span id="smartphone"></span>' if $smartphone;
  my $zoomer;
  $zoomer = $cookie{ZOOM} == '' ? 1 : $cookie{ZOOM} * 0.25;
  printfl(flattize(<<EOT));
<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="description" content="$configs{title}">
<title>$configs{titletag}</title>
<link rel="apple-touch-icon-precomposed" href="$configs{appletouchiconfilename}">
<link rel="shortcut icon" type="image/x-icon" href="$configs{faviconfilename}">
<link rel="stylesheet" type="text/css" href="./bbs.css">
<link rel="stylesheet" type="text/css" href="$configs{cssfilename}">
$refresher
<script type="text/javascript" src="jquery-3.0.0.min.js"></script>
<script type="text/javascript" src="jquery.autopager-1.0.0.min.js"></script>
<script type="text/javascript">
\$(function() {
\$.autopager({
load: function(current, next) {
warater.initPage();
banner.init();
vanisher.init();
nger.visibleExp(true);
}
});
});
</script>
<!-- 
<script type="text/javascript" src="zoom.js"></script>
 -->
<style>
body { zoom: $zoom; }
.ruler, .r { $configs{ruler}; }
.res { $configs{res}; }
$articlezoom
$reszoom
$tradcontentzoom
$datetimezoom
$tradreszoom
$articlepadding
$bodysmall
$reslinknone
$iphoneheight
</style>
</head>
<body bgcolor="$nowbgcolor">
$righttopselector
$rightbottomimg
$modeid
$lastreload
$extendparam
$smartid
<div class="shadow" id="shadow" style="zoom: $zoomer">
EOT
  if(!$argautoreload)
  {
    printfl(flattize(<<EOT));
<span id="boardtitle" class="title">$configs{title}</span>
EOT
#   print_link();
    if($configs{tentoridirname} ne '')
    {
      printfl('<span id="tentori" class="tentori"></span>');
    }
    printfl(flattize(<<EOT));
<br>
<br>
EOT
  }
}

# 最終リロード時間のフォーマットを返す
sub make_lastreloadtime
{
  my $lastreloadtime = $globaldate . $globaltime;
  $lastreloadtime = arg('newerdisp') if arg('newerdisp') ne '';
  return '<span id="lastreload" value="' . $lastreloadtime . '"></span>';
}

# HTML 入力フォームの出力
sub print_inputforms
{
  my $name = arg('name');
  $name = $cookie{NAME} if $cookie{NAME} ne '';
  my $mail = arg('mail');
  my $articles = get_articles();
  my $statline = sprint_counter() . '&nbsp;' . sprint_audiences();
  my @placeholders = split(/,/, $configs{placeholder});
  my $placeholder = $placeholders[int(rand(scalar(@placeholders)))];
  $configs{textareahtml} = '' if $smartphone;
  my $flipped;
  $flipped = $cookie{TINYFLIP} == '' ? 'inline' : $cookie{TINYFLIP};
  my $pen;
  $pen = '<img src="PenToolFilled_24x.png" width="16" height="16">' if $configs{imgdir} ne "" && !$iphone;
  printfl(flattize(<<EOT));
<form method="post" action="$configs{cginame}" id="tinyflip" style="display: $flipped">
<table border="0" cellpadding="0" cellspacing="0">
<tr><td>$configs{bcwriter}</td><td><input id="name" type="text" size="15" name="name" value="$name">&nbsp;<a href="strangeoekaki.cgi" target="_blank">$pen</a></td></tr>
<tr><td>$configs{bcmail}</td><td><input type="text" size="25" name="mail" value="$mail"></td></tr>
<tr><td>$configs{bctitle}</td><td><input type="text" size="25" name="title">
<!--
&nbsp;&nbsp;<input type="submit" name="mode" value="$configs{postbutton}">
&nbsp;&nbsp;<input type="submit" name="mode" accesskey="r" value="$configs{reloadbutton}">
-->
&nbsp;&nbsp;<input id="submitflip" type="submit" name="mode" accesskey="r" value="$configs{postreloadbutton}">
<!-- &nbsp;&nbsp;<input type="reset" value="$configs{bcreset}"> --></td></tr>
<tr><td>$configs{bccontent}</td><td><textarea id="msgflip" rows="5" cols="50" name="text" wrap="off" placeholder="$placeholder"></textarea>$configs{textareahtml}</td></tr>
<!--
<tr><td>$configs{bclink}</td><td><input type="text" size="25" name="url">
&nbsp;&nbsp;<input type="submit" name="reload" accesskey="y" value="$configs{zeroreload}">
&nbsp;&nbsp;<input type="submit" name="newer" value="$configs{newerreload}"></td></tr>
-->
EOT
  printfl('<tr><td>') if $configs{statusline} ne undef;
# if(!$smartphone)
# {
#   printfl("$configs{bcdisp}</td><td>");
#   printfl("<input type=\"text\" size=\"4\" name=\"articles\" value=\"$articles\"> ");
# }
# else
# {
    printfl('</td><td colspan="3">');
# }
  printfl("$statline</td></tr>") if $configs{statusline} ne undef;
  printfl('</table>');
  print_hidden('datetime' => $globaldate . $globaltime);
  print_hidden_simple('admin');
  print_hidden_simple('zoom');
  print_hidden_simple('trad');
  print_hidden_simple('exp');
  print_hidden_simple('tree');
  print_hidden_simple('autoreload');
  print_hidden_simple('rewind');
  printfl('</form>');
=pod
  printfl(flattize(<<EOT));
<span id="tinyflop" style="display: none;">
<form method="post" action="$configs{cginame}">
<table border="0" cellpadding="0" cellspacing="0">
<tr><td>$configs{bcwriter}</td><td><input type="text" size="15" name="name" value="$name">&nbsp;&nbsp;<input id="submitflop" type="submit" name="mode" accesskey="r" value="$configs{postreloadbutton}"></td></tr>
<tr><td>$configs{bccontent}</td><td><textarea id="msgflop" rows="3" cols="50" name="text" wrap="off" placeholder="$placeholder"></textarea>$configs{textareahtml}</td></tr>
<!--
<tr><td>$configs{bclink}</td><td><input type="text" size="25" name="url">
&nbsp;&nbsp;<input type="submit" name="reload" accesskey="y" value="$configs{zeroreload}">
&nbsp;&nbsp;<input type="submit" name="newer" value="$configs{newerreload}"></td></tr>
-->
EOT
  printfl('<tr><td>');
# if(!$smartphone)
# {
#   printfl("$configs{bcdisp}</td><td>");
#   printfl("<input type=\"text\" size=\"4\" name=\"articles\" value=\"$articles\"> ");
# }
# else
# {
    printfl('</td><td>');
# }
  printfl("$statline</td></tr>");
  printfl('</table>');
  print_hidden('datetime' => $globaldate . $globaltime);
  print_hidden_simple('admin');
  print_hidden_simple('zoom');
  print_hidden_simple('trad');
  print_hidden_simple('exp');
  print_hidden_simple('tree');
  print_hidden_simple('autoreload');
  print_hidden_simple('rewind');
  printfl('</form>');
  printfl('</span>');
=cut
}

# 自動更新モードから通常板に戻すリンクの出力
sub print_normalboard
{
  printfl("<a href=\"$configs{cginame}\">$configs{normalboard}</a>");
}

# 未読リロードリンクを返す
sub make_zeroreload
{
  my @dst;
  pushnb(\@dst, escparam('datetime', $globaldate . $globaltime));
  pushnb(\@dst, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@dst, escparam('admin', $argadmin));
  pushnb(\@dst, escparam('zoom', $argzoom));
  pushnb(\@dst, escparam('trad', $argtrad));
  pushnb(\@dst, escparam('exp', $argexp));
  pushnb(\@dst, escparam('tree', $argtree));
  pushnb(\@dst, escparam('autoreload', $argautoreload));
  my $params = join('&', @dst);
  return "<a href=\"$configs{cginame}?$params&reload=$configs{zeroreload}\">$configs{zeroreload}</a>";
}

# 新規リロードリンクを返す
sub make_newerreload
{
  my @dst;
  pushnb(\@dst, escparam('datetime', $globaldate . $globaltime));
  pushnb(\@dst, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@dst, escparam('admin', $argadmin));
  pushnb(\@dst, escparam('zoom', $argzoom));
  pushnb(\@dst, escparam('trad', $argtrad));
  pushnb(\@dst, escparam('exp', $argexp));
  pushnb(\@dst, escparam('tree', $argtree));
  pushnb(\@dst, escparam('autoreload', $argautoreload));
  my $params = join('&', @dst);
  return "<a href=\"$configs{cginame}?$params&newer=$configs{newerreload}\">$configs{newerreload}</a>";
}

# リンク行の出力
sub print_linkline
{
  if($configs{linkline} ne "")
  {
    my $zeroreload = make_zeroreload();
    my $newerreload = make_newerreload();
    printfl(flattize(<<EOT));
<!-- <hr> -->
<span class="linkline"><span class="nav"><!-- $zeroreload | $newerreload | -->
EOT
    print_link();
    printfl(flattize(<<EOT));
$configs{stablelinkline}$configs{linkline}
</span></span>
$configs{stablelinklineafter}
EOT
  }
}

# HTML カウンタの出力
sub sprint_counter
{
  my $count = get_counter();
  return sprintf("<span class=\"counter\">$configs{startdate} $count</span>");
}

# 観客数の出力
sub sprint_audiences
{
  my $dst;
  my $audiences = get_audiences();
  my $bot = get_bot();
  my $adsl = get_attack();
  my $unknown = get_unknown();
  my $unhuman = $bot + $adsl + $unknown;
  my $human = $audiences - $unhuman;
  my $attack = $adsl + $unknown;
# $dst .= sprintf('<span id="tentori" class="tentori"></span>');
  $dst .= sprintf('<span class="audiences">');
  $dst .= sprintf($configs{audiences}, $human);
# $dst .= '&nbsp;';
# my %bots = get_bots();
# my $botstr;
# foreach(sort(keys(%bots)))
# {
#   $botstr .= sprintf("$_:%s ", $bots{$_}) if $bots{$_} != 0;
# }
# $dst .= sprintf("<span title=\"$botstr\">$configs{audiencesbot}</span>", $bot);
# $dst .= '&nbsp;';
# my %attacks = get_attacks();
# my $attackstr;
# foreach(sort(keys(%attacks)))
# {
#   $attackstr .= sprintf("$_:%s ", $attacks{$_}) if $attacks{$_} != 0;
# }
# $dst .= sprintf("<span title=\"$attackstr\">$configs{audiencesattack}</span>", $attack);
  $dst .= sprintf('</span>');
  return $dst;
}

# HTML リンク行の出力
sub print_link
{
  my @dst;
  pushnb(\@dst, escparam('mode', 'config'));
# pushnb(\@dst, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@dst, escparam('zoom', $argzoom));
  pushnb(\@dst, escparam('trad', $argtrad));
  pushnb(\@dst, escparam('exp', $argexp));
  pushnb(\@dst, escparam('tree', $argtree));
  my $params = join('&', @dst);
  my $infolinkflat = $configs{infolink};
  $infolinkflat =~ s/&nbsp;//g;
  printfl(flattize(<<EOT));
$infolinkflat | <!-- <a href="$configs{cginame}?$params">$configs{config}</a> | -->
EOT
}

# 板タイプに対応した注意書き表示
sub print_notice
{
  printfl('<span class="usage">');
  printfl($configs{noticestable}) if !($trad || $exp);
  printfl($configs{noticetrad}) if $trad;
  printfl($configs{noticeexp}) if $exp;
  printfl('</span>');
}

# HTML フッタの出力
sub print_footer
{
  printfl('<hr>');
  printfl(flattize(<<EOT));
<p align="left">$configs{footercomment}</p>
<p align="right">$configs{scriptname}</p>
EOT
  printfl('</div>');
  print_javascripts();
}

# javascript 群を適用する
sub print_javascripts
{
  printfl(flattize(<<EOT));
<script type="text/javascript" src="ban.js"></script>
<script type="text/javascript" src="vanish.js"></script>
<script type="text/javascript" src="ng.js"></script>
<script type="text/javascript" src="picture.js"></script>
<script type="text/javascript" src="lastreload.js"></script>
<script type="text/javascript" src="tentori.js"></script>
<script type="text/javascript" src="extendparam.js"></script>
<script type="text/javascript" src="newer.js"></script>
<script type="text/javascript" src="warata.js"></script>
<script type="text/javascript" src="ctrlenter.js"></script>
<script type="text/javascript" src="zoomer.js"></script>
<script type="text/javascript" src="config.js"></script>
EOT
}

# HTML 終了の出力
sub print_closer
{
  printfl('</body></html>');
}

# タグ内のダブルクォートを極力取り除く
sub safe_quote
{
  my $s = shift;
  $s =~ s/"([a-zA-Z0-9]+?)"/$1/g;
  return $s;
}

# nbsp が二個連続していたら全角空白に置換する
sub reduce_nbsp
{
  my $s = shift;
  $s =~ s/&nbsp;&nbsp;/　/g;
  return $s;
}

# 全角空白を nbsp 二個に置換する
sub zenkaku_nbsp
{
  my $s = shift;
  $s =~ s/　/&nbsp;&nbsp;/g;
  return $s;
}

# 半角空白二個を nbsp 二個に置換する
sub hankaku_nbsp
{
  my $s = shift;
  $s =~ s/  /&nbsp;&nbsp;/g;
  return $s;
}

# 出力文字列を加工する
sub flattize
{
  my $s = shift;
  $s =~ s/\n//g;
# $s = safe_quote($s);
# $s = reduce_nbsp($s);
# $s = zenkaku_nbsp($s);
  $s = hankaku_nbsp($s);
  $s =~ s/class=ruler/class=r/g;
  $s =~ s/class=line/class=l/g;
  $s =~ s/<span /<u /g;
  $s =~ s#</span>#</u>#g;
  return $s;
}

# 「次のページ」リンクの出力
sub print_next
{
  return if $argrewind ne "";
  my ($articles, $pages) = @_;
  my @dst;
  pushnb(\@dst, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@dst, escparam('pages', $pages));
  pushnb(\@dst, escparam('admin', $argadmin));
  pushnb(\@dst, escparam('zoom', $argzoom));
  pushnb(\@dst, escparam('trad', $argtrad));
  pushnb(\@dst, escparam('exp', $argexp));
  pushnb(\@dst, escparam('tree', $argtree));
  pushnb(\@dst, escparam('autoreload', $argautoreload));
  my $params = join('&', @dst);
  printfl(flattize(<<EOT)) if $articles != 0;
<hr>
<a href="$configs{cginame}?$params" rel="next">$configs{nextpage}</a>
EOT
}

# 隠しパラメータを出力
# キー/値ペアで値が空でなければキー/値を出力、空なら非出力
sub print_hidden
{
  my %pairs = @_;
  foreach my $key (sort(keys(%pairs)))
  {
    if($pairs{$key} ne "")
    {
      printfl("<input type=\"hidden\" name=\"$key\" value=\"$pairs{$key}\">");
    }
  }
}

# 隠しパラメータ出力のヘルパ
sub print_hidden_simple
{
  my $name = shift;
  print_hidden($name => $cgi->param($name));
}

# 書き込み処理
sub post
{
  my $address = $ENV{'REMOTE_ADDR'};
  return if get_writer($address) >= $write_limit_count;
  append_writer_file($address);

  my $reptext;
  $reptext = "http://" . $server . "/cgi-bin/" . write_canvas() if $cgi->param('canvas') ne "";

  my @matches = arg('text') =~ /(http|https)/g;
  return if scalar(@matches) > 10;

  return if $reptext eq "" && arg('text') =~ /^[\x01-\x7f]+$/;

  return if arg('mail') ne "";

  return if arg('name') ne "" && arg('name') eq arg('title');

  my $articles = get_articles();
  my $datetime = arg('datetime');

  my %article;
  $article{TEXT} = arg('text');
  $article{TEXT} = $reptext if $reptext ne "";
  return if $article{TEXT} eq "";

  my $date = $globaldate;
  $article{DATE} = $date;
  $article{TIME} = $globaltime;
  $article{WDAY} = now_wday();

  my $name = arg('name');
  $article{USNM} = $name if $name ne "";

  my $mail = arg('mail');
  $article{MAIL} = $mail if $mail ne "";

  my $title = arg('title');
  $article{TITL} = $title if $title ne "";

  my $url = arg('url');
  $article{URLS} = $url if $url ne "";

  my $address = $ENV{'REMOTE_ADDR'};
  $article{ADDR} = $address if $address ne "";

  my @addr = split(/\./, $address);
  my $ip = pack("C4", $addr[0], $addr[1], $addr[2], $addr[3]);
  my $host = gethostbyaddr($ip, 2);
  $article{HOST} = $host if $host ne "";

  my $parent = arg('parent');
  $article{PRNT} = $parent if $parent ne "";

  my $tempname = $globaltmpnam;
  my $identifier = basename($tempname);
  $article{IDNT} = $date . $identifier;

  # ツリーと imode からのレスはすべて引用消去済みとみなす
  $article{QUOT} = 'ERASED' if !$trad || $imode;

  # imode からのレスにマークをつける
  $article{IMOD} = 'TRUE' if $imode;

  # 過去30件の書き込みに同じものがあるか
  my @collects = collect_new_articles(30);
  my $exists = 0;
  foreach my $prevline (reverse(@collects))
  {
    my %prevarticle = decode_article($prevline);
    $exists++ if $prevarticle{TEXT} eq $article{TEXT};
  }

  if($exists == 0)
  {
    if($parent ne "")
    { # 親があれば親の子リストに自分を子として追加
      my %t = read_article($parent);
      $t{CHLD} = '' if $t{CHLD} eq undef;
      my @children = split(/:/, $t{CHLD});
      push(@children, $article{IDNT});
      $t{CHLD} = join(':', @children);
      write_article($parent, %t);
    }
    # 同じものがなければログの末端に書き込む
    my @log = read_log($date);
    $article{QUOT} = 'ERASED' if has_simple_quote(\%article);
    $article{NOSP} = 'TRUE' if $trad && !has_quote_blankline(\%article);
    $article{TEXT} = remove_quote(\%article);
    push(@log, encode_article(%article));
    write_log($date, @log);
  }
}

# ワラタを受け取ってログに書き込む
sub warata
{
  my @waratas = split(/,/, $cookie{WARATAADD});
  foreach(@waratas)
  {
    my @warata = split(/:/);
    my $id = $warata[0];
    my %article = read_article($id);
    my @walses = split(/:/, $article{WALS});
    my @walsesnew;
    foreach(@walses)
    {
      push(@walsesnew, $_) if $warata[1] ne $_;
    }
    push(@walsesnew, $warata[1]);
    $article{WALS} = join(':', @walsesnew);
    write_article($id, %article);
  }
  @waratas = split(/,/, $cookie{WARATADEL});
  foreach(@waratas)
  {
    my @warata = split(/:/);
    my $id = $warata[0];
    my %article = read_article($id);
    my @walses = split(/:/, $article{WALS});
    my @walsesnew;
    foreach(@walses)
    {
      push(@walsesnew, $_) if $warata[1] ne $_;
    }
    $article{WALS} = join(':', @walsesnew);
    write_article($id, %article);
  }
}

# 書き込みが単純引用なら真を返す
sub has_simple_quote
{
  my $article = shift;
  return 0 if $article->{PRNT} eq undef;
  my $text1 = $article->{TEXT};
  $text1 =~ s/(\r\n|\n|)//g;
  $text1 =~ s/> /&gt; /g;
  $text1 =~ s/  /&nbsp;&nbsp;/g;
  my $text2 = make_allowed_parents($article, $trad_res_depth, 1);
  $text2 =~ s/(\r\n|\n|)//g;
  $text2 =~ s/> /&gt; /g;
  $text2 =~ s/  /&nbsp;&nbsp;/g;
  return substr($text1, 0, length($text2)) eq $text2;
}

# 書き込みと引用の間に空行があれば真を返す
sub has_quote_blankline
{
  my $article = shift;
  my $prev;
  foreach(split(/\n/, $article->{TEXT}))
  {
    return 1 if $prev =~ /^(>|&gt;) / && $_ =~ /^(\r\n|\n|)$/;
    $prev = $_;
  }
  return 0;
}

# 書き込みの単純引用部分だけを取り除く
sub remove_quote
{
  my $article = shift;
  my $dst = $article->{TEXT};
  if(has_simple_quote($article))
  {
    my @lines;
    foreach(split(/\n/, $article->{TEXT}))
    {
      push(@lines, $_) if $_ !~ /^(>|&gt;) /;
    }
    shift(@lines) if $lines[0] =~ /^(\r\n|\n|)$/;
    $dst = join("\n", @lines);
  }
  return $dst;
}

# ログファイル名を組み立てる
sub logfilename
{
  my $name = shift;
  return $logprefix . $name . $logpostfix;
}

# 指定したログファイルをすべて読み込む
# 各行末尾の改行は捨てる
sub read_log
{
  my $date = shift;
  my @lines;
# if($logcache{$date} ne "")
# {
#   @lines = @{$logcache{$date}};
#   return @lines;
# }
  if(-e logfilename($date))
  {
    open(IN, "<", logfilename($date));
    flock(IN, 1);
    @lines = <IN>;
    close(IN);
    if(scalar(@lines) == 0)
    {
      sleep(1);
      open(IN, "<", logfilename($date));
      flock(IN, 1);
      @lines = <IN>;
      close(IN);
    }
    $_ =~ s/\x0d?\x0a?$// foreach(@lines);
#   $logcache{$date} = \@lines;
  }
  return @lines;
}

# 指定したログファイルをすべて読み込む
# 各行末尾の改行は捨てる
sub read_log_nocache
{
  my $date = shift;
  my @lines;
  if(-e logfilename($date))
  {
    open(IN, "<", logfilename($date));
    flock(IN, 1);
    @lines = <IN>;
    close(IN);
    if(scalar(@lines) == 0)
    {
      sleep(1);
      open(IN, "<", logfilename($date));
      flock(IN, 1);
      @lines = <IN>;
      close(IN);
    }
    $_ =~ s/\x0D?\x0A?$// foreach(@lines);
  }
  return @lines;
}

# 指定したログファイルへ書き出す
sub write_log
{
  my $date = shift;
  my @log = @_;
  open(OUT, '>' . logfilename($date));
  flock(OUT, 2);
  print OUT $_ . "\n" foreach(@log);
  close(OUT);
# $logcache{$date} = \@log;
}

# 指定したIDの書き込みを読み出す
# IDの頭8文字は年月日
sub read_article
{
  my $id = shift;
  my @log = read_log(substr($id, 0, 8));
  my %article;
  foreach my $line (@log)
  {
    %article = decode_article($line);
    last if $article{IDNT} eq $id;
    %article = undef;
  }
  return %article;
}

# 指定したIDの書き込みをあるべきログファイルに書き出す
# 同じIDが既にあれば上書きする
sub write_article
{
  my $id = shift;
  my %article = @_;
  my @log = read_log(substr($id, 0, 8));
  my @newlog;
  foreach my $line (@log)
  {
    my %a = decode_article($line);
    if($a{IDNT} eq $id)
    {
      push(@newlog, encode_article(%article));
    }
    else
    {
      push(@newlog, $line);
    }
  }
  write_log(substr($id, 0, 8), @newlog);
}

# ログから書き込みを新しい順に指定個読み込む
# 2013 年より前の書き込みはないのでそこまではさかのぼる
sub collect_new_articles
{
  my $counts = shift;
  my @dst;
  my $date = $globaldate;
  while($counts != 0)
  {
    if(-e logfilename($date))
    {
      foreach my $line (reverse(read_log($date)))
      {
        push(@dst, $line);
        last if --$counts == 0;
      }
    }
    $date = yesterday($date);
    last if substr($date, 0, 4) < 2013;
  }
  return @dst;
}

# 書き込みをCSVに変換する
sub encode_article
{
  my %article = @_;
  my @items;
  foreach my $key (sort(keys(%article)))
  {
    push(@items, $key . uri_escape($article{$key}));
  }
  return join(',', @items);
}

# CSVから書き込みを復元する
sub decode_article
{
  my $line = shift;
  my @items = split(/,/, $line);
  my %dst;
  $dst{substr($_, 0, 4)} = uri_unescape(substr($_, 4)) foreach(@items);
  $dst{IPID} = make_ipid($dst{ADDR});
  $dst{WAID} = make_waid($globaladdress);
  return %dst;
}

# 現在の年月日
sub now_date
{
  my @tick = (localtime(time()));
  my ($year, $month, $day) = @tick[5, 4, 3];
  $year += 1900;
  $month += 1;
  return sprintf("%04d%02d%02d", $year, $month, $day);
}

# 現在の時分秒
sub now_time
{
  my @tick = (localtime(time()));
  my ($hour, $minute, $second) = @tick[2, 1, 0];
  return sprintf("%02d%02d%02d", $hour, $minute, $second);
}

# 現在の曜日
sub now_wday
{
  my @tick = (localtime(time()));
  return $tick[6];
}

# 指定した文字列日付の昨日を文字列で返す
sub yesterday
{
  my $date = shift;
  my $year = substr($date, 0, 4) - 1900;
  my $month = substr($date, 4, 2) - 1;
  my $day = substr($date, 6);
  my $y = timelocal(0, 0, 0, $day, $month, $year);
  $y -= (24 * 3600);
  ($day, $month, $year) = (localtime($y))[3..5];
  return sprintf("%04d%02d%02d", $year + 1900, $month + 1, $day);
}

# 指定した文字列日時を秒数にして返す
sub seconds
{
  my $datetime = shift;
  my $year = substr($datetime, 0, 4) - 1900;
  my $month = substr($datetime, 4, 2) - 1;
  my $day = substr($datetime, 6, 2);
  my $hour = substr($datetime, 8, 2);
  my $minute = substr($datetime, 10, 2);
  my $second = substr($datetime, 12);
  return timelocal($second, $minute, $hour, $day, $month, $year);
}

# 指定した文字列日時の指定分前を文字列で返す
sub rewind_minutes
{
  my $datetime = shift;
  my $rewind = shift;
  my $year = substr($datetime, 0, 4) - 1900;
  my $month = substr($datetime, 4, 2) - 1;
  my $day = substr($datetime, 6, 2);
  my $hour = substr($datetime, 8, 2);
  my $minute = substr($datetime, 10, 2);
  my $second = substr($datetime, 12);
  my $y = timelocal($second, $minute, $hour, $day, $month, $year);
  $y -= ($rewind * 60);
  ($day, $month, $year) = (localtime($y))[3..5];
  ($second, $minute, $hour) = (localtime($y))[0..2];
  return sprintf("%04d%02d%02d%02d%02d%02d", $year + 1900, $month + 1, $day, $hour, $minute, $second);
}

# 木の表示メイン
sub print_tree
{
  my $count = get_articles();
  my $pages = get_pages();
  my $skiproots = $count * ($pages - 1);
  $count = $count * $pages;
  my $datetime = arg('datetime');
  $datetime = $cookie{LASTRELOAD} if $cookie{LASTRELOAD} ne '';
  $datetime = 0 if $datetime eq "";
  $datetime = rewind_minutes($globaldate . $globaltime, $argrewind) if $datetime == 0 && $argrewind ne "";
  my @roots;
  my $dst;
  if($count > 0)
  { # 最新の書き込みがある木の根の時間を取得
    @roots = root_counts($count);
    $dst = $roots[scalar(@roots) - 1];
    $dst = $dst->{DATE} . $dst->{TIME};
  }
  else
  { # 特定時間より新しい書き込みがある木の根を取得
    @roots = root_times($datetime);
    $dst = $datetime;
  }
  my @trees;
  foreach my $root (@roots)
  { # 根の子を集めて最新の子の時間をソートの種として併記
    my @tree = make_tree($root);
    push(@trees, [\@tree, newest_datetime([\@tree])]);
  }
  # 最新順にソート
  @trees = sort {$$b[1] <=> $$a[1]} @trees;
  # 出力しないページに属する根は削除
  for(my $i = 0; $i < $skiproots; $i++)
  {
    shift(@trees);
  }
  print_tree_articles($_, $dst, $datetime) foreach(@trees);
}

# 新しい子のある根を新しい順に指定個得る
sub root_counts
{
  my $count = shift;
  my $date = $globaldate;
  my @dst;
  while($date > 20130101)
  {
    if(-e logfilename($date))
    {
      my @log = read_log($date);
      foreach my $line (reverse(@log))
      {
        my $beforesize = scalar(@dst);
        my $root = get_root(decode_article($line));
        unique_push(\@dst, $root);
        if(scalar(@dst) != $beforesize)
        {
          return @dst if --$count == 0;
        }
      }
    }
    $date = yesterday($date);
  }
  return @dst;
}

# 指定時間より新しい子のある根をすべて得る
sub root_times
{
  my $datetime = shift;
  my $date = $globaldate;
  my @dst;
  while($date > 20130101)
  {
    if(-e logfilename($date))
    {
      my @log = read_log($date);
      foreach my $line (reverse(@log))
      {
        my %article = decode_article($line);
        return @dst if ($article{DATE} . $article{TIME}) < $datetime;
        unique_push(\@dst, get_root(%article));
      }
    }
    $date = yesterday($date);
  }
  return @dst;
}

# 子から根を得る
sub get_root
{
  my %article = @_;
  while($article{PRNT} ne undef)
  {
    %article = read_article($article{PRNT});
  }
  return \%article;
}

# 配列に同じIDがない場合だけpushする
sub unique_push
{
  my ($dst, $data) = @_;
  foreach(@$dst)
  {
    return if $_->{IDNT} eq $data->{IDNT};
  }
  push(@$dst, $data);
}

# 根から木を作る
sub make_tree
{
  my $root = shift;
  my @dst;
  make_tree_recur($root, \@dst);
  return @dst;
}

# 根から再帰的に木を作るためのヘルパ
sub make_tree_recur
{
  my ($base, $dst) = @_;
  push(@$dst, $base);
  foreach(split(/:/, $base->{CHLD}))
  {
    my %article = read_article($_);
    make_tree_recur(\%article, $dst);
  }
}

# キー/値のうち値があるときだけペアにして返す
sub escparam
{
  my ($param, $data) = @_;
  return $data eq "" ? "" : $param . '=' . $data;
}

# 書き込み辞書から ID を探す
sub find_article
{
  my ($id, $dic) = @_;
  foreach my $index (@{$dic})
  {
    return $index if $index->{IDNT} eq $id;
  }
}

# 木の最新書き込みの日時を得る
sub newest_datetime
{
  my $tree = shift;
  my $datetime = 0;
  my $wday = 0;
  foreach my $article (@{$$tree[0]})
  {
    my $articledatetime = $article->{DATE} . $article->{TIME};
    my $articlewday = $article->{WDAY};
    if($datetime < $articledatetime)
    {
      $datetime = $articledatetime;
      $wday = $articlewday;
    }
  }
  return ($datetime, $wday);
}

# 木にNGワードがあれば真を返す
sub is_ngtree
{
  my $tree = shift;
  foreach my $article (@{$$tree[0]})
  {
    return 1 if has_ngwords($article->{USNM});
    return 1 if has_ngwords($article->{TITL});
    return 1 if has_ngwords($article->{TEXT});
  }
  return 0;
}

# 日時を文字列で取得
sub get_datetime_text
{
  my ($datetime, $wday) = @_;
  my $dst;
  my $date = substr($datetime, 0, 8);
  my $time = substr($datetime, 8);
  my $year = substr($date, 0, 4);
  my $month = substr($date, 4, 2);
  my $day = substr($date, 6, 2);
  my $hour = substr($time, 0, 2);
  my $minute = substr($time, 2, 2);
  my $second = substr($time, 4, 2);
  $dst .= sprintf("%04d/%02d/%02d", $year, $month, $day);
  $wday = ("日", "月", "火", "水", "木", "金", "土")[$wday];
  $dst .= sprintf("($wday)");
  $dst .= sprintf("%02d時%02d分%02d秒", $hour, $minute, $second);
  return $dst;
}

# 日時を HTML 出力
sub print_datetime
{
  my ($datetime, $wday) = @_;
  printfl('<div class="datetime">');
  printfl(get_datetime_text($datetime, $wday));
  printfl('<span class="vanishtree"></span>');
  printfl('</div>');
}

# 木を一つ HTML 出力
sub print_tree_articles
{
  my ($tree, $datetime, $reloadtime) = @_;
  return if is_ngtree($tree);
  if(arg('newerdisp') eq '')
  {
    printfl("<div class=\"vanishpart ngpart\" id=\"$$tree[0][0]->{IDNT}\">");
    printfl('<hr>') if !$exp;
    print_datetime(newest_datetime($tree)) if !$exp;
    printfl('<span class="ngexp vanishexp"></span>');
    printfl('<nobr>') if $smartphone;
    printfl("<div class=\"article\">");
  }
  my $depth = 0;        # インデントレベル
  my @itbl;             # 書き込みをつなぐ罫線を保持
  $depth++ if $exp;
  push(@itbl, '<span class="ruler">└</span>') if $exp;
  print_tree_article_recur($$tree[0][0], $$tree[0], $depth, \@itbl, $reloadtime);
  if(arg('newerdisp') eq '')
  {
    printfl("</div>");
    printfl('</nobr>') if $smartphone;
    printfl('</div>');
  }
}

# 有効な子だけを得る
# 荒らしで子IDだけ放り込むのが過去あった
sub correct_true_children
{
  my ($children, $dic) = @_;
  my @dst;
  foreach my $item (@{$dic})
  {
    foreach my $child (@{$children})
    {
      push(@dst, $child) if $item->{IDNT} eq $child;
    }
  }
  return @dst;
}

# 木を一つ HTML 出力、再帰用ヘルパ
sub print_tree_article_recur
{
  my ($refarticle, $dic, $depth, $itbl, $reloadtime) = @_;
  my %article = %$refarticle;
  my @children;
  @children = split(/:/, $article{CHLD}) if $article{CHLD} ne undef;
  @children = correct_true_children(\@children, $dic);
  my $sibs = scalar(@children);   # 同じ深さの子の数
  my $hot;
  $hot = $class_hot if $reloadtime != 0 && ($article{DATE} . $article{TIME}) > $reloadtime;
  print_tree_article(\%article, $itbl, $sibs, $hot);
  if($article{CHLD} ne undef)
  {
    my $last = pop(@children);
    foreach my $child (@children)
    {
      $$itbl[$depth] = '<span class="ruler">├</span>';
      if($depth > 0)
      {
        $$itbl[$depth - 1] = '<span class="ruler">│</span>' if $$itbl[$depth - 1] eq '<span class="ruler">├</span>';
        $$itbl[$depth - 1] = '&nbsp;&nbsp;' if $$itbl[$depth - 1] eq '<span class="ruler">└</span>';
      }
      print_tree_article_recur(find_article($child, $dic), $dic, $depth + 1, $itbl, $reloadtime);
    }
    $$itbl[$depth] = '<span class="ruler">└</span>';
    if($depth > 0)
    {
      $$itbl[$depth - 1] = '<span class="ruler">│</span>' if $$itbl[$depth - 1] eq '<span class="ruler">├</span>';
      $$itbl[$depth - 1] = '&nbsp;&nbsp;' if $$itbl[$depth - 1] eq '<span class="ruler">└</span>';
    }
    print_tree_article_recur(find_article($last, $dic), $dic, $depth + 1, $itbl, $reloadtime);
    delete($$itbl[$depth]);
  }
}

# 書き込みを一つ HTML 出力
sub print_tree_article
{
  my ($refarticle, $itbl, $sibs, $hot) = @_;
  my %article = %$refarticle;
  $newercount++ if $hot ne '';
  return if arg('newerdisp') ne '';
  my @param;
  pushnb(\@param, escparam('date', $article{DATE}));
  pushnb(\@param, escparam('parent', $article{IDNT}));
  pushnb(\@param, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@param, escparam('mail', arg('mail')));
  pushnb(\@param, escparam('admin', $argadmin));
  pushnb(\@param, escparam('zoom', $argzoom));
  pushnb(\@param, escparam('trad', $argtrad));
  pushnb(\@param, escparam('exp', $argexp));
  pushnb(\@param, escparam('tree', $argtree));
  pushnb(\@param, escparam('autoreload', $argautoreload));
  my $linkparam = join('&', @param);
  my $target = $argtarget;
  printfl($_) foreach(@$itbl);
  if($article{NRES} eq undef)
  {
    printfl("<a href=\"$configs{cginame}?mode=res&$linkparam\"");
    printfl(" target=\"_blank\"") if $target eq '_blank';
    printfl(' class="res"');
    printfl(" style=\"$configs{hotbuttoncolor}\"") if ($hot ne "") && $exp;
    printfl(" title=\"$configs{resclick}\"");
    printfl('>■</a>');
  }
  else
  {
    printfl('■');
  }
  printfl("<span class=\"banmsg\" name=\"$article{IPID}\" style=\"display:none\"><i class='unban'></i><br></span>");
  my $text = uri_unescape($article{TEXT});
  my $infospacing = get_maxwidth($text);
  my $url = uri_unescape($article{URLS});
  $text .= "\n\n$url\n" if $url ne "";
  $text = make_link($text);
  $text =~ s/blanktemp/ target="_blank"/g if $target eq '_blank';
  $text =~ s/blanktemp//g;
  my $infoline = make_infoline($refarticle);
  $text = $infoline . $text if !$exp || $arginfo eq 'true';
  $text = make_replaces($text);
  $text = tagstrike($text) if $nazo; # なぞ化計画
  $text = "<i>$configs{deleted}</i>\n" if $article{DELE} ne undef;
  my $noneed = $text =~ /\.(jpg|png|gif)/;
  my $datetext = get_datetime_text($article{DATE} . $article{TIME}, $article{WDAY});
  printfl("<span title=\"$datetext\">") if !$noneed && !$exp;
  my $taggedinfoline = $infoline;
# $infoline =~ s/<("[^"]*"|'[^']*'|[^'">])*>//g;
# printfl("<span title=\"$infoline\">") if !$noneed && $exp && $arginfo eq 'false';
  my @lines = split(/\n/, $text);
  my $top = shift(@lines);
  printfl("<span class=\"$hot\">") if $hot ne "";
  $top =~ s/[\n|\r|]$//;
  printfl("<span class=\"banip\" name=\"$article{IPID}\">");
  printfl("<span class=\"warata\" name=\"$article{WAID}\">");
  printfl("<span class=\"waratalist\" name=\"$article{WALS}\"></span>");
  printfl("<span class=\"identify\" name=\"$article{IDNT}\"></span>");
  printfl("<span class=\"line\">$top</span>") if $top ne "";
  if($article{DELE} eq undef)
  {
    printfl('&nbsp;') foreach(0..($infospacing - get_linewidth($top)));
    printfl("<span class=\"infoline\">─ $taggedinfoline</span>") if !$noneed && $exp && $arginfo eq 'false' && $infoline ne '';
  }
  printfl('<span class="waratamark"></span>');
  printfl('<br>');
  my $sized = @$itbl;
  my $save = $$itbl[$sized - 1];
  my $patch = $save eq '<span class="ruler">└</span>' ? '&nbsp;&nbsp;' : '<span class="ruler">│</span>';
  my $patch2 = $sibs > 0 ? '<span class="ruler">│</span>' : '&nbsp;&nbsp;';
  $$itbl[$sized - 1] = $patch if $sized > 0;
  push(@lines, "");
  foreach my $line (@lines)
  {
    printfl($_) foreach(@$itbl);
    printfl($patch2);
    my $indent = $sized + 1;
#   $line =~ s/imgindentem/${indent}em;/g;
    $line =~ s/[\n|\r|]$//;
    my $smindent;
    $smindent = '&nbsp;&nbsp;&nbsp;&nbsp;' if $iphone;
    printfl("<span class=\"line\">$smindent$line</span>") if $line ne "";
    printfl('<br>');
  }
  printfl('</span>');
  printfl("<span class=\"banmsg\" name=\"$article{IPID}\" style=\"display:none\">");
  printfl($_) foreach(@$itbl);
  printfl($patch2);
  printfl('<br>');
  printfl('</span>');
  printfl('</span>');
  printfl('</span>');
  $$itbl[$sized - 1] = $save if $sized > 0;
  printfl('</span>') if $hot ne "";
  printfl('</span>') if !$noneed && !$exp;
}

# 単語を外部ファイルの指定通りに置換する
sub make_replaces
{
  my $text = shift;
  foreach(@replaces)
  {
    my ($src, $dst) = split(/,/, $_);
    $text =~ s/$src/$dst/g;
  }
  return $text;
}

# リンク形式で書かれたテキストをタグ化する
sub make_link
{
  my $text = shift;
  $text =~ s/(http|https):\/\/.*\.youtube\.com\/watch\?v=(.*)/<a href=\"movie:\/\/www\.youtube\.com\/watch\?v=$2\"blanktemp>movie:\/\/www\.youtube\.com\/watch\?v=$2<\/a>\n<iframe width="400" height="225" src="movie:\/\/www.youtube.com\/embed\/$2" frameborder="0" allowfullscreen><\/iframe>/g;
  # $text =~ s/(http|https):\/\/(.*\.(gif|jpg|png))/grph:[$2]/g;
  $text = make_http_link($text);
  $text =~ s/movie:(\/\/www\.youtube\.)/http:$1/g;
  $text =~ s/&/&amp;/g;
  $text =~ s/</&lt;/g;
  $text =~ s/>/&gt;/g;
  $text =~ s/&lt;a (.*?)&gt;/<a $1>/g;
  $text =~ s/&lt;\/a&gt;/<\/a>/g;
  $text =~ s/&lt;iframe (.*?)&gt;/<iframe $1>/g;
  $text =~ s/&lt;\/iframe&gt;/<\/iframe>/g;
  $text =~ s/&amp;nbsp;/&nbsp;/g;
  # $text =~ s/grph:\[(.*)\]/<table border=\"0\" style=\"margin-left:imgindentem\"><tr><td><a class=\"zoom\" href=\"http:\/\/$1\"><img src=\"http:\/\/$1\"><br>http:\/\/$1<\/a><\/td><\/tr><\/table>/g;
  return $text; 
}

# http/https をタグ化する
sub make_http_link
{
  my $text = shift;
  $text =~ s/([^"]|^)((http|https):\/\/[a-zA-Z0-9!_@~=&:#\.\/\?\-ぁ-んァ-ヶ亜-腕]*)/$1<a href=\"$2\"blanktemp>$2<\/a>/g;
  return $text;
}

# キー/値の値が空でない場合だけpushする
sub pushnb
{
  my ($array, $param) = @_;
  push(@$array, $param) if $param ne "";
}

# 書き込みの情報欄を組み立てる
sub make_infoline
{
  my $refarticle = shift;
  my %article = %$refarticle;
  my @dst;
  my $name = $article{USNM};
  if($name ne "")
  {
    push(@dst, "$configs{bcwriter}:" . make_trip(sanitize($name)));
#   if($name =~ /$adminname/)
#   {
#     my $info = $article{HOST};
#     $info = $article{ADDR} if $info eq "";
#     push(@dst, '<i>' . $info . '</i>');
#   }
  }
  my $title = $article{TITL};
  if($title ne "")
  {
    push(@dst, "$configs{bctitle}:" . sanitize($title));
  }
  my $mail = $article{MAIL};
  if($mail ne "")
  {
    push(@dst, "$configs{bcmail}:" . sanitize($mail));
  }
  if($article{DISP} ne undef || uri_unescape($cgi->param('admin')) eq $pass)
  {
    my $info = $article{HOST};
    $info = $article{ADDR} if $info eq "";
    push(@dst, '<i>' . $info . '</i>');
  }
  if($argadmin eq $pass)
  {
    my @params;
    pushnb(\@params, escparam('name', delete_trip(arg('name'))));
    pushnb(\@params, escparam('admin', $argadmin));
    pushnb(\@params, escparam('zoom', $argzoom));
    pushnb(\@params, escparam('trad', $argtrad));
    pushnb(\@params, escparam('exp', $argexp));
    pushnb(\@params, escparam('tree', $argtree));
    pushnb(\@params, escparam('autoreload', $argautoreload));
    pushnb(\@params, escparam('ident', $article{IDNT}));
    my $param = join('&', @params);
    push(@dst, "<a href=\"$configs{cginame}?mode=display&$param\">IP表示</a>");
    push(@dst, "<a href=\"$configs{cginame}?mode=delete&$param\">削除</a>");
  }
  my $line;
  if(@dst)
  {
    $line = '<span class="infoline">' . join(' ', @dst) . "</span>\n";
  }
  return $line;
}

# 文字をエスケープする
sub sanitize
{
  my $text = shift;
  $text =~ s/&/&amp;/g;
  $text =~ s/</&lt;/g;
  $text =~ s/>/&gt;/g;
  return $text;
}

# レス画面メイン
sub res
{
  print_content_type();
  print_header(0);
  $trad ? print_flatoriginarticle() : print_originarticle();
  $trad ? print_flatresforms() : print_resforms();
  print_footer();
  print_closer();
  exit();
}

# 指定葉から指定数さかのぼった木を組み立てる
# 兄弟葉は切り捨てる
sub collect_response
{
  my ($base, $depth) = @_;
  my $tempname = tmpnam();
  my $identifier = basename($tempname);
  my %article;
  $article{IDNT} = $globaldate . $identifier;
  $base->{CHLD} = $article{IDNT};
  $article{PRNT} = $base->{IDNT};
  $article{TEXT} = $configs{reshere};
  $article{NRES} = 'TRUE';
  my @dst;
  push(@dst, \%article);
  foreach(1..$depth)
  {
    push(@dst, $base);
    last if $base->{PRNT} eq undef;
    my %article = read_article($base->{PRNT});
    $article{CHLD} = $base->{IDNT};
    $base = \%article;
  }
  return ($base, @dst);
}

# いわゆるレス元のツリーをレス画面に HTML 出力
sub print_originarticle
{
  my $id = uri_unescape($cgi->param('parent'));
  my %article = read_article($id);
  my @tree = collect_response(\%article, 2);
  my $dst = @tree[scalar(@tree) - 1];
  $dst = $dst->{DATE} . $dst->{TIME};
  printfl('<br>');
  my $reloadtime = ($article{DATE} . $article{TIME}) - 1;
  print_tree_articles([\@tree, $dst], $reloadtime);
}

# レス元の旧型式書き込みをレス画面に HTML 出力
sub print_flatoriginarticle
{
  my $id = uri_unescape($cgi->param('parent'));
  my %article = read_article($id);
  printfl(get_flat_article(\%article));
  printfl('<hr>');
}

# レス元の入力フォームにテキストを入れて HTML 出力
sub print_flatresforms
{
  my $id = uri_unescape($cgi->param('parent'));
  my %article = read_article($id);
  my $arrows = make_allowed_families(\%article, $trad_res_depth);
  $arrows =~ s/  /&nbsp;&nbsp;/g;
  print_resforms($arrows);
}

# レス元の入力フォームを HTML 出力
sub print_resforms
{
  my $defaulttext = shift;
  my $name = arg('name');
  $name = $cookie{NAME} if $cookie{NAME} ne '';
  my $mail = arg('mail');
  my $parent = arg('parent');
  my $articles = $argarticles;
  my $datetime = arg('datetime');
  $datetime = $globaldate . $globaltime if $datetime eq "";
  printfl(flattize(<<EOT));
<form method="post" action="$configs{cginame}">
<table border="0" cellpadding="0" cellspacing="0">
<tr><td>$configs{bcwriter}</td><td><input type="text" size="15" name="name" value="$name"></td></tr>
<tr><td>$configs{bcmail}</td><td><input type="text" size="25" name="mail" value="$mail"></td></tr>
<tr><td>$configs{bctitle}</td><td><input type="text" size="25" name="title">
<!--
&nbsp;&nbsp;<input type="submit" name="mode" value="$configs{postbutton}">
&nbsp;&nbsp;<input type="submit" name="mode" accesskey="r" value="$configs{reloadbutton}">
-->
&nbsp;&nbsp;<input id="submitflip" type="submit" name="mode" accesskey="r" value="$configs{postreloadbutton}">
<!-- &nbsp;&nbsp;<input type="reset" value="$configs{bcreset}"> --> </td></tr>
EOT
  print("<tr><td>$configs{bccontent}</td><td><textarea id=\"msgflip\" rows=\"5\" cols=\"50\" name=\"text\" wrap=\"off\" placeholder=\"$configs{placeholder}\">$defaulttext</textarea></td></tr>");
  printfl(flattize(<<EOT));
<!--
<tr><td>$configs{bclink}</td><td><input type="text" size="25" name="url">
&nbsp;&nbsp;<input type="submit" name="reload" accesskey="y" value="$configs{zeroreload}">
&nbsp;&nbsp;<input type="submit" name="newer" value="$configs{newerreload}"></td></tr>
-->
</table>
EOT
  print_hidden('parent', $parent);
  print_hidden('datetime', $datetime);
  print_hidden_simple('admin');
  print_hidden_simple('zoom');
  print_hidden_simple('trad');
  print_hidden_simple('exp');
  print_hidden_simple('tree');
  print_hidden_simple('autoreload');
  printfl('</form>');
}

# disp モード、ログに表示する旨マークする
sub disp
{
  my $id = arg('ident');
  my %article = read_article($id);
  $article{DISP} = 'TRUE';
  write_article($id, %article);
}

# del モード、ログに削除マークをつける
sub del
{
  my $id = uri_unescape($cgi->param('ident'));
  my %article = read_article($id);
  $article{DELE} = 'TRUE';
  write_article($id, %article);
}

# amend モード、ログに取り消しマークをつける
sub amend
{
  my $id = uri_unescape($cgi->param('ident'));
  my %article = read_article($id);
  $article{AMEN} = 'TRUE';
  write_article($id, %article);
}

# imode板メイン
sub imode_main
{
  print_content_type();
  print(flattize(<<EOT));
<html>
<head>
<title>$configs{imodetitle}</title>
<link rel="stylesheet" href="bbs.css">
<link rel="stylesheet" href="$configs{cssfilename}">
</head>
<body bgcolor="$nowbgcolor">
EOT
  my $mode = arg('mode');
  my $name = arg('name');
  $name = $cookie{NAME} if $cookie{NAME} ne '';
  $name =~ s/"/&quot;/g;
  my $mail = arg('mail');
  my $pages = arg('pages');
  $pages = 2 if $pages eq undef;
  my $nowdatetime = $globaldate . $globaltime;
  if($mode eq 'res')
  {
    my $parent = uri_unescape($cgi->param('parent'));
    my %article = read_article($parent);
    print(imode_print(\%article));
    my $articles = uri_unescape($cgi->param('articles'));
    $articles = $cookie{ARTICLES} if $cookie{ARTICLES} ne '';
    my $datetime = uri_unescape($cgi->param('datetime'));
    $datetime = $nowdatetime if $datetime eq "";
    print(flattize(<<EOT));
<form method="post" action="$configs{cginame}">
<textarea rows="4" cols="14" name="text"></textarea><br>
<input type="submit" name="post" value="投:9" accesskey="9"><br>
名<input type="8" type="text" name="name" value="$name"><br>
信<input type="8" type="text" name="mail" value="$mail"><br>
題<input type="8" type="text" name="title">
<input type="hidden" name="i" value="1">
<input type="hidden" name="mode" value="post">
<input type="hidden" name="parent" value="$parent">
<input type="hidden" name="articles" value="$articles">
<input type="hidden" name="datetime" value="$datetime">
</form>
</body>
</html>
EOT
    exit();
  }
  elsif($mode eq 'post')
  {
    post();
  }
  my $datetime;
  my $contents;
  if(uri_unescape($cgi->param('wri')) ne undef)
  {
    my $datetime = uri_unescape($cgi->param('datetime'));
    $datetime = $nowdatetime if $datetime eq "";
    print(flattize(<<EOT));
<form method="post" action="$configs{cginame}">
<textarea rows="4" cols="14" name="text"></textarea><br>
<input type="submit" name="post" value="投:9" accesskey="9"><br>
名<input size="8" type="text" name="name" value="$name"><br>
信<input size="8" type="text" name="mail" value="$mail"><br>
題<input size="8" type="text" name="title">
<input type="hidden" name="i" value="1">
<input type="hidden" name="url" value="">
<input type="hidden" name="mode" value="post">
<input type="hidden" name="datetime" value="$datetime">
</form>
</body>
</html>
EOT
    exit();
  }
  elsif(uri_unescape($cgi->param('rel')) ne undef)
  {
    ($datetime, $contents) = make_contents(undef, 1);
    $pages = 2;
  }
  elsif(uri_unescape($cgi->param('rel0')) ne undef)
  {
    ($datetime, $contents) = make_contents(0);
  }
  elsif(uri_unescape($cgi->param('nex')) ne undef)
  {
    ($datetime, $contents) = make_contents();
    $pages++;
  }
  else
  {
    ($datetime, $contents) = make_contents();
  }
  $datetime = $nowdatetime;
  $contents = '<br>' . get_counter() . '<br>' . $contents;
  print(flattize(<<EOT));
<form method="post" action="$configs{cginame}">
<a name="top"><a href="#bottom" accesskey="8">▼:8</a></a>
<input type="submit" name="rel0" value="未:0" accesskey="0">
<input type="submit" name="rel" value="Ｒ:7" accesskey="7">
<input type="submit" name="wri" value="投:9" accesskey="9">
EOT
  print($contents);
  print(flattize(<<EOT));
<input type="submit" name="nex" value="＞:5" accesskey="5">
<input type="hidden" name="i" value="1">
<input type="hidden" name="name" value="$name">
<input type="hidden" name="mail" value="$mail">
<input type="hidden" name="datetime" value="$datetime">
<input type="hidden" name="pages" value="$pages">
<a name="bottom"><a href="#top" accesskey="2">▲:2</a></a>
</form>
</body>
</html>
EOT
  exit();
}

# imode ページを組み立てる
sub make_contents
{
  my ($givencount, $givenpages) = @_;
  my $count = $argarticles;
  $count = $default_imode_articles if $count eq undef;
  $count = $givencount if $givencount ne undef;
  my $pages = arg('pages');
  $pages = 1 if $pages eq undef;
  $pages = $givenpages if $givenpages ne undef;
  my $first = ($pages * $count) - ($count - 1);
  my $skip = ($pages - 1) * $count;
  $count = $count * $pages;
  my $datetime = arg('datetime');
  $datetime = 0 if $datetime eq "";
  $datetime = rewind_minutes($globaldate . $globaltime, $argrewind) if $datetime == 0 && $argrewind ne "";
  my @arts;
  my $dst;
  if($count > 0)
  {
    @arts = collect_counts($count);
    $dst = $arts[scalar(@arts) - 1];
    $dst = $dst->{DATE} . $dst->{TIME};
  }
  else
  {
    @arts = collect_times($datetime);
    $dst = $datetime;
  }
  my $c;
  foreach my $article (@arts)
  {
    next if --$skip >= 0;
    $c .= imode_print($article);
  }
  my $collects = scalar(@arts);
  $c .= '<br>';
  $c .= $first . '-' if $collects ne 0;
  $c .= $collects;
  $c .= '件';
  return ($dst, $c);
}

# imode 書き込みの表示
sub imode_print
{
  my $article = shift;
  my $c;
  $c .= '<pre>';
  my @param;
  pushnb(\@param, escparam('date', $article->{DATE}));
  pushnb(\@param, escparam('parent', $article->{IDNT}));
  pushnb(\@param, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@param, escparam('mail', $cgi->param('mail')));
  my $articles = uri_unescape($cgi->param('articles'));
  $articles = $cookie{ARTICLES} if $cookie{ARTICLES} ne '';
  $articles = $default_imode_articles if $articles eq undef;
  my $lineparam = join('&', @param);
  $c .= "<a href=\"$configs{cginame}?i=1&mode=res&$lineparam\">■</a>";
  my $date = $article->{DATE};
  my $time = $article->{TIME};
  my $month = substr($date, 4, 2);
  my $day = substr($date, 6, 2);
  my $hour = substr($time, 0, 2);
  my $minute = substr($time, 2, 2);
  my $second = substr($time, 4, 2);
  $c .= sprintf('%02d/%02d ', $month, $day);
  $c .= sprintf('%02d:%02d:%02d', $hour, $minute, $second);
  $c .= "<br>";
  my $user = make_trip(sanitize($article->{USNM}));
  my $mail = sanitize($article->{MAIL});
  my $infoline = $user;
  $infoline = '<a href="mailto:' . $mail . '">' . $infoline . '</a>' if $mail ne "";
  $infoline = 'name:' . $infoline if $infoline ne "";
  $c .= $infoline;
  if($article->{DISP} ne undef) # if($infoline =~ /$adminname/ || $article->{DISP} ne undef)
  {
    my $host = $article->{HOST};
    $host = $article->{ADDR} if $host eq "";
    $c .= " <i>$host</i>";
  }
  $c .= "<br>" if $infoline ne "";
  my $arrow = '&gt; ';
  my @lines = split(/\n/, sanitize($article->{TEXT}));
  my $added = 0;
  my $depth = 1;
  foreach(1..$depth)
  {
    my $parent = $article->{PRNT};
    last if $parent eq "";
    my %parentarticle = read_article($parent);
    unshift(@lines, ' ') if $added == 0;
    my @res;
    foreach my $line (reverse(split(/\n/, sanitize($parentarticle{TEXT}))))
    {
      unshift(@res, $arrow . $line);
    }
    @res = split(/\n/, tagstrike(join("\n", @res))) if $nazo;
    unshift(@lines, @res) if $article->{QUOT} eq 'ERASED';
    $arrow .= '&gt; ';
    $article = \%parentarticle;
    $added++;
  }
  $c .= join("\n", @lines);
  $c .= '</pre>';
  $c = tagstrike($c) if $nazo;
  return $c;
}

# 新しい順に書き込みを指定個取得
sub collect_counts
{
  my $count = shift;
  my $date = $globaldate;
  my @dst;
  while($date > 20130101)
  {
    if(-e logfilename($date))
    {
      my @log = read_log($date);
      foreach my $line (reverse(@log))
      {
        my %article = decode_article($line);
	if($article{DELE} eq '' && $article{AMEN} eq '')
	{
	  push(@dst, \%article);
	  return @dst if --$count == 0;
	}
      }
    }
    $date = yesterday($date);
  }
  return @dst;
}

# 指定時間より新しい書き込みをすべて取得
sub collect_times
{
  my $datetime = shift;
  my $date = $globaldate;
  my @dst;
  while($date > 20130101)
  {
    if(-e logfilename($date))
    {
      my @log = read_log($date);
      foreach my $line (reverse(@log))
      {
        my %article = decode_article($line);
        return @dst if ($article{DATE} . $article{TIME}) < $datetime;
	if($article{DELE} eq '' && $article{AMEN} eq '')
	{
	  unique_push(\@dst, \%article);
	}
      }
    }
    $date = yesterday($date);
  }
  return @dst;
}

# 旧型式の書き込みの表示
sub print_flat
{
  my $count = get_articles();
  my $pages = get_pages();
  my $skip = $count * ($pages - 1);
  $count = $count * $pages;
  my $datetime = arg('datetime');
  $datetime = $cookie{LASTRELOAD} if $cookie{LASTRELOAD} ne '';
  $datetime = 0 if $datetime eq "";
  $datetime = rewind_minutes($globaldate . $globaltime, $argrewind) if $datetime == 0 && $argrewind ne "";
  my @articles;
  if($count > 0)
  {
    @articles = collect_counts($count);
  }
  else
  {
    @articles = collect_times($datetime);
  }
  foreach my $article (@articles)
  {
    next if --$skip >= 0;
    my $content = get_flat_article($article);
    my $c;
    $c .= '<nobr>' if $smartphone;
    $c .= '<div class="tradarticle">';
    $c .= $content;
    $c .= '</div>';
    $c .= '</nobr>' if $smartphone;
    $c .= '<hr>';
    printfl("<div class=\"vanishpart ngpart\" id=\"$article->{IDNT}\">");
    print flattize($c) if $content ne '<!hasng>';
    printfl('</div>');
  }
}

# 旧型式の書き込みの HTML 形式の取得
sub get_flat_article
{
  my $article = shift;
  my $hasng = 0;
  $hasng = 1 if $article->{DELE} ne undef;
  $hasng = 1 if $article->{AMEN} ne undef;
  my $c;
  my $i;
  $i .= "<span class=\"banmsg\" name=\"$article->{IPID}\" style=\"display:none\"><blockquote><i class='unban'></i></blockquote></span>";
  $i .= "<div class=\"banip\" name=\"$article->{IPID}\">";
  $i .= "<div class=\"warata\" name=\"$article->{WAID}\">";
  $i .= "<span class=\"waratalist\" name=\"$article->{WALS}\"></span>";
  $i .= "<span class=\"identify\" name=\"$article->{IDNT}\"></span>";
  $i .= '<font size="-1" face="MS PGothic">';
  if($article->{TITL} ne undef)
  {
    $i .= '<font size="+1">';
    $i .= '<b>' . $article->{TITL} . '</b>';
    $i .= '</font>';
  }
  elsif($article->{PRNT} ne undef)
  {
    $i .= '<font size="+1">';
    my %parent = read_article($article->{PRNT});
    my $parentname = $parent{USNM};
    $hasng = 1 if has_ngwords($parentname);
    $parentname = '&nbsp;&nbsp;' if $parentname eq undef;
    $i .= '<b>' . '＞' . delete_trip($parentname) . '</b>';
    $i .= '</font>';
  }
  else
  {
    $i .= '&nbsp;&nbsp;';
  }
  $i .= '&nbsp;&nbsp;';
  $i .= '<font size="+0">' . $configs{traduser};
  $hasng = 1 if has_ngwords($article->{USNM});
  if($article->{USNM} ne undef)
  {
    $i .= '<b>' . make_trip($article->{USNM}) . '</b>';
  }
  else
  {
    $i .= '&nbsp;&nbsp;';
  }
  $i .= '</font>';
  $i .= '&nbsp;&nbsp;';
  $i .= '<font size="-1">';
  $i .= $configs{traddate};
  $i .= get_datetime_text($article->{DATE} . $article->{TIME}, $article->{WDAY});
  $i .= '</font>';
  $i .= '&nbsp;&nbsp;';
  my @param;
  pushnb(\@param, escparam('date', $article->{DATE}));
  pushnb(\@param, escparam('parent', $article->{IDNT}));
  pushnb(\@param, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
  pushnb(\@param, escparam('mail', arg('mail')));
  pushnb(\@param, escparam('admin', $argadmin));
  pushnb(\@param, escparam('zoom', $argzoom));
  pushnb(\@param, escparam('trad', $argtrad));
  pushnb(\@param, escparam('exp', $argexp));
  pushnb(\@param, escparam('tree', $argtree));
  pushnb(\@param, escparam('autoreload', $argautoreload));
  my $linkparam = join('&', @param);
  my $target = $argtarget;
  $i .= '<span class="tradres">';
  $i .= "<a href=\"$configs{cginame}?mode=res&$linkparam\"";
  $i .= 'target="_blank"' if $target ne '';
  $i .= ' class="res"';
  $i .= " title=\"$configs{resclick}\"";
  $i .= ">$configs{tradresbutton}</a>";
  $i .= '</span>';
  $i .= '<span class="vanishtrad"></span>';
  $i .= '<span class="banlink"></span>';
  if($nazo && $configs{tradamendbutton} ne '')
  {
    if($article->{HOST} ne "" && $article->{HOST} eq $globalhost)
    {
      if(seconds($globaldate . $globaltime) - seconds($article->{DATE} . $article->{TIME}) < 24 * 60 * 60) # 一日
      {
	$i .= '&nbsp;' foreach(1..5);
	my @p;
	pushnb(\@p, escparam('date', $article->{DATE}));
	pushnb(\@p, escparam('parent', $article->{IDNT}));
	pushnb(\@p, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
	pushnb(\@p, escparam('mail', arg('mail')));
	pushnb(\@p, escparam('admin', $argadmin));
	pushnb(\@p, escparam('zoom', $argzoom));
	pushnb(\@p, escparam('trad', $argtrad));
	pushnb(\@p, escparam('exp', $argexp));
	pushnb(\@p, escparam('tree', $argtree));
	pushnb(\@p, escparam('autoreload', $argautoreload));
	pushnb(\@p, escparam('ident', $article->{IDNT}));
	my $lp = join('&', @p);
	$i .= "<a href=\"$configs{cginame}?mode=amend&$lp\"";
	$i .= 'target="_blank"' if $target ne '';
	$i .= ' class="resamend"';
	$i .= '>';
	$i .= "$configs{tradamendbutton}";
	$i .= '</a>';
      }
    }
  }
  if($argadmin eq $pass)
  {
    my @params;
    pushnb(\@params, escparam('name', delete_trip(arg('name'))));
    pushnb(\@params, escparam('admin', $argadmin));
    pushnb(\@params, escparam('zoom', $argzoom));
    pushnb(\@params, escparam('trad', $argtrad));
    pushnb(\@params, escparam('exp', $argexp));
    pushnb(\@params, escparam('tree', $argtree));
    pushnb(\@params, escparam('autoreload', $argautoreload));
    pushnb(\@params, escparam('ident', $article->{IDNT}));
    my $param = join('&', @params);
    $i .= " <a href=\"$configs{cginame}?mode=display&$param\">IP表示</a>";
    $i .= " <a href=\"$configs{cginame}?mode=delete&$param\">削除</a>";
  }
  if($article->{DISP} ne undef)
  {
    $i .= '<i>' . $article->{HOST} . '</i>';
  }
  $i .= '<span class="waratamark"></span>';
  $i .= '</font>';
  $i .= '<font size="-1">';
  $i .= '<blockquote>';
  $i .= '<div class="tradcontent">';
  my $content = make_flat_article_text($article);
  $i .= $content;
  $hasng = 1 if $content eq '<!hasng>';
  $i .= '</div>';
  $i .= '</blockquote>';
  $i .= '</font>';
  $i .= '</div>';
  $i .= '</div>';
  $c .= $i;
  $c = '<!hasng>' if $hasng;
  return $c;
}

# 旧型式のレス画面における引用部分の組み立て
# 自分自身も入る
sub make_allowed_families
{
  my ($article, $maxdepth) = @_;
  $article->{PRNT} = $article->{IDNT};
  return make_allowed_parents($article, $maxdepth);
}

# 旧型式の引用部分の組み立て
sub make_allowed_parents
{
  my ($article, $maxdepth, $force_build) = @_;
  my $dst;
  if($article->{QUOT} ne 'ERASED' && !$force_build)
  {
    return $dst if $article->{PRNT} eq undef;
    my %parent = read_article($article->{PRNT});
    my @lines = split(/\n/, sanitize($parent{TEXT}));
    $lines[scalar(@lines) - 1] .= "" if scalar(@lines) > 0;
    push(@lines, $parent{URLS} . "") if $parent{URLS} ne undef;
    my $firstline = scalar(@lines) - 1;
    $lines[$_] = '&gt; ' . $lines[$_] foreach(0..scalar(@lines) - 1);
    for(my $line = 0; $line < scalar(@lines) - 1; ++$line)
    {
      if($lines[$line] !~ /^&gt; > /)
      {
        $firstline = $line;
        last;
      }
    }
    if($firstline != scalar(@lines) - 1 && $lines[$firstline] =~ /^&gt; $/)
    {
      splice(@lines, $firstline, 1);
    }
    my $arrow;
    $arrow .= '&gt; ' foreach(0..$maxdepth);
    @lines = map { $_ =~ s/^${arrow}.*$//g; $_ } @lines;
    $dst = join("\n", @lines) . "\n";
  }
  else
  {
    my $depth = 0;
    my $arrow = '&gt; ';
    while($article->{PRNT} ne undef && ++$depth < $maxdepth)
    {
      my %parent = read_article($article->{PRNT});
      my @lines = split(/\n/, sanitize($parent{TEXT}));
      $lines[scalar(@lines) - 1] .= "" if scalar(@lines) > 0;
      push(@lines, $parent{URLS} . "") if $parent{URLS} ne undef;
      $lines[$_] = $arrow . $lines[$_] foreach(0..scalar(@lines) - 1);
      $dst = join("\n", @lines) . "\n" . $dst;
      $arrow .= '&gt; ';
      $article = \%parent;
    }
  }
  return $dst;
}

# 旧型式書き込みの組み立て
sub make_flat_article_text
{
  my $article = shift;
  my $text = $article->{TEXT};
  my $url = $article->{URLS};
  my $target = $argtarget;
  $text .= "\n\n$url\n" if $url ne undef;
  $text = make_link($text);
  $text =~ s/blanktemp/ target="_blank"/g if $target eq '_blank';
  $text =~ s/blanktemp//g;
  $text = make_replaces($text);
  $text = tagstrike($text) if $nazo;
  $text =~ s/\n/<br>/g if $text !~ /svg/;
  $text =~ s/(\r|\n)//g;
  $text =~ s/  /&nbsp;&nbsp;/g;
  $text =~ s/> (.)/>&nbsp;$1/g;
  my $refs = make_allowed_parents($article, $trad_res_depth);
  $refs .= '<br>' if $article->{NOSP} eq undef;
  $refs .= '<br>' if $article->{IMOD} ne undef;
  $refs = make_http_link($refs);
  $refs =~ s/blanktemp/ target="_blank"/g if $target eq '_blank';
  $refs =~ s/blanktemp//g;
  $refs = make_replaces($refs);
  $refs = reflevel_tagstrike($refs, $trad_res_depth) if $nazo;
  $refs =~ s/\n/<br>/g;
  $refs =~ s/(\r|\n)//g;
  $refs =~ s/  /&nbsp;&nbsp;/g;
  $refs = "" if $article->{QUOT} ne 'ERASED';
  my $hasng = 0;
  $hasng = 1 if has_ngwords($text);
  $hasng = 1 if has_ngwords($refs);
  if($article->{PRNT} ne "")
  {
    $text = $refs . (!$smartphone ? '<font size="-1">' : '') . $text;
    $text .= '<br><br>';
    my %parent = read_article($article->{PRNT});
    $article = \%parent;
    my @param;
    pushnb(\@param, escparam('date', $article->{DATE}));
    pushnb(\@param, escparam('parent', $article->{IDNT}));
    pushnb(\@param, escparam('name', uri_escape(delete_trip($cgi->param('name')))));
    pushnb(\@param, escparam('mail', arg('mail')));
    pushnb(\@param, escparam('admin', $argadmin));
    pushnb(\@param, escparam('zoom', $argzoom));
    pushnb(\@param, escparam('trad', $argtrad));
    pushnb(\@param, escparam('exp', $argexp));
    pushnb(\@param, escparam('tree', $argtree));
    pushnb(\@param, escparam('autoreload', $argautoreload));
    my $linkparam = join('&', @param);
    $text .= "<a href=\"$configs{cginame}?mode=res&$linkparam\">";
    $text .= $configs{tradres} . get_datetime_text($article->{DATE} . $article->{TIME}, $article->{WDAY});
    $text .= '</a>' . (!$smartphone ? '</font>' : '');
    $text .= '<br><br>';
  }
  else
  {
    $text .= '<br><br>';
  }
  $text = "<!hasng>" if $hasng;

  return $text;
}

# 参照部分限定で tagstrike をかける
sub reflevel_tagstrike
{
  my ($text, $maxdepth) = @_;
  my @lines = split(/\n/, $text);
  my @res;
  my @body = @lines;
  foreach(0..scalar(@lines))
  {
    last if $lines[$_] !~ /^&gt; /;
    push(@res, $lines[$_]);
    splice(@body, 0, 1);
  }
  my $depths;
  my @cutted = split(/\n/, tagstrike(join("\n", @res)));
  foreach(1..$maxdepth)
  {
    my $arrow;
    $arrow .= '&gt; ' foreach($_..$maxdepth);
    my @stack;
    foreach(0..scalar(@res))
    {
      last if $res[$_] !~ /^$arrow/;
      push(@stack, $res[$_]);
      splice(@cutted, 0, 1);
    }
    my $depth = join("\n", @stack);
    $depth .= "\n" if $depth ne "";
    $depths .= $depth;
    @res = @cutted;
  }
  my $bodystrike = join("\n", @body);
  return $depths . $bodystrike;
}

# 表示時のタグコントロール
sub tagstrike
{
  my $text = shift;

  # 完全禁止タグ群を制御
  $text =~ s/&lt;(.*?)&gt;/<$1>/g;
  $text =~ s/&lt;\/(.*?)(&gt;|>)/<\/$1>/g;
# $text =~ s/<(.*?) class(.*?)>/<$1 class_$2>/ig;
  $text =~ s/<(.*?) name(.*?)>/<$1 name_$2>/ig;
  $text =~ s/<(.*?) action(.*?)>/<$1 action_$2>/ig;
  $text =~ s/<xmp +.*?>//ig;
  $text =~ s/<plaintext +.*?>//ig;
  $text =~ s/<body +.*?>//ig;
  $text =~ s/<html +.*?>//ig;
  $text =~ s/<script +.*?>//ig;

  # pre は完全につぶす
  $text =~ s/<\/?pre>//ig;

  $text = make_style($text);
  $text = make_styletag($text);
  my @tags = $text =~ /<\/?.*?>/g;
  my %check;
  foreach(@tags) # タグの開き閉じの対応をカウント
  {
    if($_ !~ /^<\//)
    {
      $_ =~ s/^<(.*)>$/$1/;
      $_ =~ s/^(.*?) .*$/$1/;
      $check{lc($_)}++;
    }
    else
    {
      $_ =~ s/^<\/(.*)>$/$1/;
      $_ =~ s/^(.*?) .*$/$1/;
      --$check{lc($_)};
    }
  }
  my $minus;
  foreach(keys %check) # 閉じが勝っていたら同じタグは全部無効化
  {
    if($check{$_} < 0)
    {
      $text =~ s/<( *?$_.*?)>/&lt;$1&gt;/g;
      $text =~ s/<( *?(\/?)$_.*?)>/&lt;$1&gt;/g;
    }
  }
  my @closer;
  foreach(keys %check) # 開きが勝っていたら書き込み末尾で閉じる
  {
    for(my $i = 0; $i < $check{$_}; $i++)
    {
      push(@closer, '</' . $_ . '>');
    }
  }
  $text .= join('', @closer);
  $text =~ s/<\/br>//ig;

  # アンパサンド化された < と > を元に戻す
  $text =~ s/&amp;lt;/&lt;/g;
  $text =~ s/&amp;gt;/&gt;/g;

  return $text;
}

# タグの style= を適正化する
sub make_style
{
  my $text = shift;
  my @tags = $text =~ /<.*?>/g;
  foreach(@tags)
  {
    my $t = $_;
    $t =~ s/^<(.*)>$/$1/;
    my @styles_si = $t =~ /style='(.*?);*'/ig;
    $t =~ s/'$_;*'// foreach(@styles_si);
    my @styles_do = $t =~ /style="(.*?);*"/ig;
    $t =~ s/"$_;*"// foreach(@styles_do);
    my @styles_ba = $t =~ /style=(.*)/ig;
    foreach((@styles_si, @styles_do, @styles_ba))
    {
      my @styles = split(/;/);
      foreach(@styles)
      {
	if($_ =~ /font-size.*?:/i)
	{
	  my $p = $_;
	  $p =~ s/font-size.*?: *(.*)/$1/i;
	  $p =~ /([\d]*)(.*)$/;
	  next if $2 =~ /;/ && $1 <= 10;
	  next if $1 <= 100 && $2 =~ /pt/i;
	  next if $1 <= 20 && $2 =~ /em/i;
	  next if $1 <= 200 && $2 =~ /px/i;
	}
	next if $_ =~ /color.*?:/i;
	next if $_ =~ /text-shadow.*?:/i;
	next if $_ =~ /font-weight.*?:/i;
	next if $_ =~ /opacity.*?:/i;

	$text =~ s/$_//;
      }
    }
  }
  return $text;
}

# <style> を適正化する
sub make_styletag
{
  my $text = shift;
  my @styles = $text =~ /<style>(.*?)<\/style>/ig;
  foreach(@styles)
  {
    my @p = $_ =~ /{(.*?)}/g;
    foreach(@p)
    {
      if($_ =~ /font-size.*?:/i)
      {
	my $p = $_;
	$p =~ s/font-size.*?: *(.*)/$1/i;
	$p =~ /([\d]*)(.*)$/;
	next if $2 =~ /;/ && $1 <= 10;
	next if $1 <= 100 && $2 =~ /pt/i;
	next if $1 <= 20 && $2 =~ /em/i;
	next if $1 <= 200 && $2 =~ /px/i;
      }
      next if $_ =~ /color.*?:/i;
      next if $_ =~ /transition-.*?:/i;
      next if $_ =~ /text-shadow.*?:/i;
      next if $_ =~ /font-weight.*?:/i;
      next if $_ =~ /opacity.*?:/i;
      $text =~ s/$_//;
    }
  }
  return $text;
}

# 板の設定画面
sub config
{
  print_content_type();
  print_header(0);
  my $name = arg('name');
  $name = $cookie{NAME} if $cookie{NAME} ne '';
  my $articles = get_articles();
  $articles = '' if $articles == $default_articles;
  my $defarticles = sprintf("$configs{defarticles}", $default_articles);
  my $nosharpbgcolor = substr($nowbgcolor, 1);
  my ($tradc, $treec, $expc);
  $tradc = 'checked' if $argtrad;
  $treec = 'checked' if $argtree;
  $expc = 'checked' if $argexp;
  printfl(flattize(<<EOT));
<form method="get" action="$configs{cginame}">
$configs{defwriter} <input type="text" size="20" name="name" value="$name"><br>
$defarticles <input type="text" size="4" name="articles" value="$articles"><br>
$configs{bgword} <input type="text" size="40" name="bgcolor" value="$nosharpbgcolor"><br>
$configs{deftarget} <input type="checkbox" name="target" value="checked"><br>
$configs{defdisplay}
 <input type="radio" name="display" value="trad" $tradc>$configs{defdisplaytrad}
 <input type="radio" name="display" value="tree" $treec>$configs{defdisplaytree}
 <input type="radio" name="display" value="exp" $expc>$configs{defdisplayexp}
<br>
<br>
<span class="notice">$configs{bcconfig}</span><br>
<br>
<input type="submit" name="mode" value="$configs{configchange}">
<input type="reset" value="$configs{bcreset}"><br>
EOT
  print_hidden('zoom' => $cgi->param('zoom'));
  printfl('</form>');
  print_footer();
  print_closer();
  exit();
}

# 板にパラメータを渡すためのリロード
sub configed
{
  my @dst;
  pushnb(\@dst, escparam('zoom', $argzoom));
# pushnb(\@dst, escparam('trad', $argtrad));
# pushnb(\@dst, escparam('exp', $argexp));
# pushnb(\@dst, escparam('tree', $argtree));
  my $params = join('&', @dst);
  print("Content-type: text/html; charset=UTF-8\n");
  print_cookie('NAME' => arg('name'), 'TARGET' => arg('target'), 'ARTICLES' => arg('articles'), 'BGCOLOR' => arg('bgcolor'));
  print_cookie('DISPLAY' => arg('display'));
  print("\n");
  printfl("<html><head><meta charset=\"UTF-8\">");
  printfl("<meta http-equiv=\"refresh\" content=\"0; url=$ENV{'SCRIPT_NAME'}?$params\">");
  printfl("</head><body>");
  printfl("</body></html>");
  exit();
}

# NGワードにヒットしたら真を返す
sub has_ngwords
{
  return 0; # javascript に委譲した
  my $content = shift;
  my $ng = $cookie{NG};
  return 0 if $ng eq undef;
  return $content =~ /$ng/;
}

# 点取り占いを取得
sub make_tentori
{
  my $dst;
  my $score = int(rand(10));
  open(IN, "<$configs{tentoridirname}tentori${score}.txt");
  my @lines = <IN>;
  close(IN);
  $_ =~ s/\x0d?\x0a?$//g foreach(@lines);
  $score = 10 if $score == 0;
  my @mark = ('×', '▲', '▲', '△', '△', '●', '●', '○', '○', '◎', '◎');
  my $line = $lines[int(rand(scalar(@lines) - 1))];
  $dst = '<span class="tentori">';
  $dst .= "$line $mark[$score]$score点";
  $dst .= '</span>';
  return $dst;
}

# トリップ情報を作成
sub make_trip
{
  my $name = shift;
  my @p = split(/#/, $name, 2);
  if(scalar(@p) == 2)
  {
    my $sj = $p[1];
    $sj =~ s/&quot;/"/g;
    from_to($sj, 'UTF-8', 'Shift_JIS');
    my $salt = substr($sj, , 1) . 'H';
    $salt =~ tr/\x3A-\x40\x5B-\x60\x00-\x2D\x7B-\xFF/A-Ga-f./;
    $name = $p[0] . ' <span class="trip">◆' . substr(crypt($sj, $salt), -10) . '</span>';
  }
  return $name;
}

# トリップ情報を削除
sub delete_trip
{
  my $name = shift;
  my @p = split(/#/, $name);
  return $p[0];
}

# クッキーを書き出す
sub print_cookie
{
  my %values = (@_);
  $values{$_} = uri_escape($values{$_}) foreach(keys(%values));
  foreach(sort(keys(%values)))
  {
    print("Set-Cookie: $_=$values{$_}; expires=Tue, 1-Jan-2030 00:00:00 GMT;\n");
  }
}

# クッキーを読み込む
sub read_cookie
{
  my %dst;
  foreach(split(/; */, $ENV{'HTTP_COOKIE'}))
  {
    my ($key, $value) = split(/=/);
    $value = uri_unescape($value);
    $dst{$key} = $value if $value ne "";
  }
  return %dst;
}

# content-type 以外の表示文字列はすべてこの関数を通す
sub printfl
{
  my $s = shift;
  print(flattize($s));
}

# 攻撃なら非ゼロを返す
sub is_attack
{
  my @list = read_textfile($configs{attacksfilename});
  chomp(@list);
  my $address = $ENV{'REMOTE_ADDR'};
  my @addr = split(/\./, $address);
  my $ip = pack("C4", $addr[0], $addr[1], $addr[2], $addr[3]);
  my $host = gethostbyaddr($ip, 2);
  my $flag = 0;
  $flag += ($host =~ /$_/) foreach(@list);
  return $flag;
}

# URL に含まれる IDNT が該当すれば非ゼロを返す
sub is_ngident
{
  if (!(-e $configs{ngidentfilename})) {
    return 0;
  }
  my @list = read_textfile($configs{ngidentfilename});
  chomp(@list);
  my $flag = 0;
  $flag += (arg('parent') =~ /$_/) foreach(@list);
  return $flag;
}

# Error 404 でページ出力を終了する
sub goto404
{
  print "Status: 404 Not Found\n";
  print "Content-type: text/html\n\n";
  exit();
}

# アドレスからIDを作成する
sub make_ipid
{
  my $sj = shift;
  from_to($sj, 'UTF-8', 'Shift_JIS');
  my $salt = substr($sj, , 1) . 'H';
  $salt =~ tr/\x3A-\x40\x5B-\x60\x00-\x2D\x7B-\xFF/A-Ga-f./;
  return substr(crypt($sj, $salt), -10);
}

# 文字列の半角幅を計算する
sub get_linewidth
{
  my $line = shift;
  my $c = unijp($line)->sjis;
  $c =~ s/&#[0-9a-fA-F]+;/  /g;
  return length($c);
}

# 文章の最大半角幅を計算する
sub get_maxwidth
{
  my $text = shift;
  my @lines = split(/\n/, $text);
  my $maxchar = 0;
  foreach(@lines)
  {
    my $l = get_linewidth($_);
    $maxchar = max($maxchar, $l);
  }
  return $maxchar;
}

# アドレスからワラタIDを作成する
sub make_waid
{
  my $sj = shift;
  from_to($sj, 'UTF-8', 'Shift_JIS');
  my $salt = substr($sj, , 1) . 'H';
  $salt =~ tr/\x3A-\x40\x5B-\x60\x00-\x2D\x7B-\xFF/A-Ga-f./;
  return substr(crypt($sj, $salt), -10);
}

# 転送されてくるキャンバスを書き込んでそのファイル名を返す
sub write_canvas
{
    my $canvas = $cgi->param('canvas');
    my $upfilename = '' . time() . '.png';
    open(OUT, ">$configs{imgdir}/$upfilename");
    print OUT MIME::Base64::decode($canvas);
    close(OUT);
    return "$configs{imgdir}/$upfilename";
}

# vim: set tabstop=8 softtabstop=2 shiftwidth=2 :
