<?php
/**
 * Copied and re-formatted from The Great Computer Language Shootout:
 *
 *   http://shootout.alioth.debian.org
 */

//date_default_timezone_set("UTC");

///////////////////////////////////////////////////////////////////////////////
// tests

function simple($n = 1000000) {
  $a = 0;
  for ($i = 0; $i < $n; $i++)
    $a++;

  $thisisanotherlongname = 0;
  for ($thisisalongname = 0; $thisisalongname < $n; $thisisalongname++)
    $thisisanotherlongname++;
}

function simplecall($n = 1000000) {
  for ($i = 0; $i < $n; $i++)
    strlen("hallo");
}

function hallo($a) {
}

function simpleucall($n = 1000000) {
  for ($i = 0; $i < $n; $i++)
    hallo("hallo");
}

function simpleudcall($n = 1000000) {
  for ($i = 0; $i < $n; $i++)
    hallo2("hallo");
}
function hallo2($a) {
}

function mandel() {
  $w1=50;
  $h1=150;
  $recen=-.45;
  $imcen=0.0;
  $r=0.7;
  $s=0;  $rec=0;  $imc=0;  $re=0;  $im=0;  $re2=0;  $im2=0;
  $x=0;  $y=0;  $w2=0;  $h2=0;  $color=0;
  $s=2*$r/$w1;
  $w2=40;
  $h2=12;
  for ($y=0 ; $y<=$w1; $y=$y+1) {
    $imc=$s*($y-$h2)+$imcen;
    for ($x=0 ; $x<=$h1; $x=$x+1) {
      $rec=$s*($x-$w2)+$recen;
      $re=$rec;
      $im=$imc;
      $color=1000;
      $re2=$re*$re;
      $im2=$im*$im;
      while( ((($re2+$im2)<1000000) && $color>0)) {
        $im=$re*$im*2+$imc;
        $re=$re2-$im2+$rec;
        $re2=$re*$re;
        $im2=$im*$im;
        $color=$color-1;
      }
      if ( $color==0 ) {
        print "_";
      } else {
        print "#";
      }
    }
    print "<br>";
    //flush();
  }
}

/*function mandel2() {
  $b = " .:,;!/>)|&IH%*#";
  //float r, i, z, Z, t, c, C;
  for ($y=30; printf("\n"), $C = $y*0.1 - 1.5, $y--;){
    for ($x=0; $c = $x*0.04 - 2, $z=0, $Z=0, $x++ < 75;){
      for ($r=$c, $i=$C, $k=0; $t = $z*$z - $Z*$Z + $r, $Z = 2*$z*$Z + $i, $z=$t, $k<5000; $k++)
        if ($z*$z + $Z*$Z > 500000) break;
      echo $b[$k%16];
    }
  }
  }*/

function Ack($m, $n){
  if($m == 0) return $n+1;
  if($n == 0) return Ack($m-1, 1);
  return Ack($m - 1, Ack($m, ($n - 1)));
}

function ackermann($n = 7) {
  $r = Ack(3,$n);
  print "Ack(3,$n): $r\n";
}

function ary($n = 50000) {
  $X = array();
  $Y = array();
  for ($i=0; $i<$n; $i++) {
    $X[$i] = $i;
  }
  for ($i=$n-1; $i>=0; $i--) {
    $Y[$i] = $X[$i];
  }
  $last = $n-1;
  print "$Y[$last]\n";
}

function ary2($n = 50000) {
  $X = array();
  $Y = array();
  for ($i=0; $i<$n;$i) {
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;

    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
    $X[$i] = $i; ++$i;
  }
  for ($i=$n-1; $i>=0;$i) {
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;

    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
    $Y[$i] = $X[$i]; --$i;
  }
  $last = $n-1;
  print "$Y[$last]\n";
}

function ary3($n = 2000) {
  $X = array();
  $Y = array();
  for ($i=0; $i<$n; $i++) {
    $X[$i] = $i + 1;
    $Y[$i] = 0;
  }
  for ($k=0; $k<1000; $k++) {
    for ($i=$n-1; $i>=0; $i--) {
      $Y[$i] += $X[$i];
    }
  }
  $last = $n-1;
  print "$Y[0] $Y[$last]\n";
}

function fibo_r($n){
    return(($n < 2) ? 1 : fibo_r($n - 2) + fibo_r($n - 1));
}

function fibo($n = 30) {
  $r = fibo_r($n);
  print "$r\n";
}

/*function hash1($n = 50000) {
  for ($i = 1; $i <= $n; $i++) {
    $X[dechex($i)] = $i;
  }
  $c = 0;
  for ($i = $n; $i > 0; $i--) {
    if ($X[dechex($i)]) { $c++; }
  }
  print "$c\n";
  }*/

function hash2($n = 500) {
  $hash1 = array();
  $hash2 = array();
  for ($i = 0; $i < $n; $i++) {
    $hash1["foo_$i"] = $i;
    $hash2["foo_$i"] = 0;
  }
  for ($i = $n; $i > 0; $i--) {
    foreach($hash1 as $key => $value) $hash2[$key] += $value;
  }
  $first = "foo_0";
  $last  = "foo_".($n-1);
  print "$hash1[$first] $hash1[$last] $hash2[$first] $hash2[$last]\n";
}

function heapsort_r($n, &$ra) {
    $l = ($n >> 1) + 1;
    $ir = $n;

    while (1) {
	if ($l > 1) {
	    $rra = $ra[--$l];
	} else {
	    $rra = $ra[$ir];
	    $ra[$ir] = $ra[1];
	    if (--$ir == 1) {
		$ra[1] = $rra;
		return;
	    }
	}
	$i = $l;
	$j = $l << 1;
	while ($j <= $ir) {
	    if (($j < $ir) && ($ra[$j] < $ra[$j+1])) {
		$j++;
	    }
	    if ($rra < $ra[$j]) {
		$ra[$i] = $ra[$j];
		$j += ($i = $j);
	    } else {
		$j = $ir + 1;
	    }
	}
	$ra[$i] = $rra;
    }
}

function heapsort($N = 20000) {
  global $LAST;

  $ary = array(0);
  for ($i=1; $i<=$N; $i++) {
    $ary[$i] = gen_random(1);
  }
  heapsort_r($N, $ary);
  echo $ary[$N];
  //printf("%.10f\n", $ary[$N]);
}

function mkmatrix ($rows, $cols) {
    $count = 1;
    $mx = array();
    for ($i=0; $i<$rows; $i++) {
	for ($j=0; $j<$cols; $j++) {
	    $mx[$i][$j] = $count++;
	}
    }
    return($mx);
}

function mmult ($rows, $cols, $m1, $m2) {
    $m3 = array();
    for ($i=0; $i<$rows; $i++) {
	for ($j=0; $j<$cols; $j++) {
	    $x = 0;
	    for ($k=0; $k<$cols; $k++) {
		$x += $m1[$i][$k] * $m2[$k][$j];
	    }
	    $m3[$i][$j] = $x;
	}
    }
    return($m3);
}

function matrix($n = 20) {
  $SIZE = 30;
  $m1 = mkmatrix($SIZE, $SIZE);
  $m2 = mkmatrix($SIZE, $SIZE);
  while ($n--) {
    $mm = mmult($SIZE, $SIZE, $m1, $m2);
  }
  print "{$mm[0][0]} {$mm[2][3]} {$mm[3][2]} {$mm[4][4]}\n";
}

function nestedloop($n = 12) {
  $x = 0;
  for ($a=0; $a<$n; $a++)
    for ($b=0; $b<$n; $b++)
      for ($c=0; $c<$n; $c++)
        for ($d=0; $d<$n; $d++)
          for ($e=0; $e<$n; $e++)
            for ($f=0; $f<$n; $f++)
             $x++;
  print "$x\n";
}

function sieve($n = 30) {
  $count = 0;
  while ($n-- > 0) {
    $count = 0;
    $flags = range (0,8192);
    for ($i=2; $i<8193; $i++) {
      if ($flags[$i] > 0) {
        for ($k=$i+$i; $k <= 8192; $k+=$i) {
          $flags[$k] = 0;
        }
        $count++;
      }
    }
  }
  print "Count: $count\n";
}

function strcat($n = 200000) {
  $str = "";
  while ($n-- > 0) {
    $str .= "hello\n";
  }
  $len = strlen($str);
  print "$len\n";
}

function bottomUpTree($item, $depth)
{
   if($depth)
   {
      --$depth;
      $newItem = $item<<1;
      return array(
         bottomUpTree($newItem - 1, $depth),
         bottomUpTree($newItem, $depth),
         $item
      );
   }
   return array(NULL, NULL, $item);
}

function itemCheck($treeNode)
{
   $check = 0;
   do
   {
      $check += $treeNode[2];
      if(NULL == $treeNode[0])
      {
         return $check;
      }
      $check -= itemCheck($treeNode[1]);
      $treeNode = $treeNode[0];
   }
   while(TRUE);
}

function binary_trees($n = 12) {
  $minDepth = 4;
  $maxDepth = max($minDepth + 2, $n);
  $stretchDepth = $maxDepth + 1;

  $stretchTree = bottomUpTree(0, $stretchDepth);
  printf("stretch tree of depth %d\t check: %d\n",
  $stretchDepth, itemCheck($stretchTree));
  unset($stretchTree);

  $longLivedTree = bottomUpTree(0, $maxDepth);

  $iterations = 1 << ($maxDepth);
  do
  {
     $check = 0;
     for($i = 1; $i <= $iterations; ++$i)
     {
        $t = bottomUpTree($i, $minDepth);
        $check += itemCheck($t);
        unset($t);
        $t = bottomUpTree(-$i, $minDepth);
        $check += itemCheck($t);
        unset($t);
     }

     printf("%d\t trees of depth %d\t check: %d\n",
            $iterations<<1, $minDepth, $check);

     $minDepth += 2;
     $iterations >>= 2;
  }
  while($minDepth <= $maxDepth);

  printf("long lived tree of depth %d\t check: %d\n",
  $maxDepth, itemCheck($longLivedTree));
}


function Fannkuch_run($n){
   $check = 0;
   $perm = array();
   $perm1 = array();
   $count = array();
   $maxPerm = array();
   $maxFlipsCount = 0;
   $m = $n - 1;

   for ($i=0; $i<$n; $i++) $perm1[$i] = $i;
   $r = $n;

   while (TRUE) {
      // write-out the first 30 permutations
      if ($check < 30){
        for($i=0; $i<$n; $i++) echo $perm1[$i]+1;
        echo "\n";
        $check++;
      }

      while ($r != 1){ $count[$r-1] = $r; $r--; }
      if (! ($perm1[0]==0 || $perm1[$m] == $m)){
         for($i=0; $i<$n; $i++) $perm[$i] = $perm1[$i];
         $flipsCount = 0;

         while ( !(($k=$perm[0]) == 0) ) {
            $k2 = ($k+1) >> 1;
            for($i=0; $i<$k2; $i++) {
               $temp = $perm[$i]; $perm[$i] = $perm[$k-$i]; $perm[$k-$i] = $temp;
            }
            $flipsCount++;
         }

         if ($flipsCount > $maxFlipsCount) {
            $maxFlipsCount = $flipsCount;
            for($i=0; $i<$n; $i++) $maxPerm[$i] = $perm1[$i];
         }
      }

      while (TRUE) {
         if ($r == $n) return $maxFlipsCount;
         $perm0 = $perm1[0];
         $i = 0;
         while ($i < $r) {
            $j = $i + 1;
            $perm1[$i] = $perm1[$j];
            $i = $j;
         }
         $perm1[$r] = $perm0;

         $count[$r] = $count[$r] - 1;
         if ($count[$r] > 0) break;
         $r++;
      }
   }
}

function fannkuch($n = 9) {
  printf("Pfannkuchen(%d) = %d\n", $n, Fannkuch_run($n));
}


/* Weighted selection from alphabet */
function makeCumulative(&$genelist) {
   $count = count($genelist);
   for ($i=1; $i < $count; $i++) {
      $genelist[$i][1] += $genelist[$i-1][1];
   }
}

function selectRandom(&$a) {
   $r = gen_random(1);
   $hi = sizeof($a);

   for ($i = 0; $i < $hi; $i++) {
      if ($r < $a[$i][1]) return $a[$i][0];
   }
   return $a[$hi-1][0];
}

/* Generate and write FASTA format */
define ('LINE_LENGTH', 60);

function makeRandomFasta($id, $desc, &$genelist, $n) {
   print(">$id $desc\n");

   for ($todo = $n; $todo > 0; $todo -= LINE_LENGTH) {
      $pick = '';
      $m = $todo < LINE_LENGTH ? $todo : LINE_LENGTH;
      for ($i=0; $i < $m; $i++) $pick .= selectRandom($genelist);
      $pick .= "\n";
      print( $pick );
   }
}

function makeRepeatFasta($id, $desc, $s, $n) {
   echo ">$id $desc\n";
   $i = 0; $sLength = strlen($s); $lineLength = LINE_LENGTH;
   while ($n > 0) {
      if ($n < $lineLength) $lineLength = $n;
      if ($i + $lineLength < $sLength){
         print(substr($s,$i,$lineLength)); print("\n");
         $i += $lineLength;
      } else {
         print(substr($s,$i));
         $i = $lineLength - ($sLength - $i);
         print(substr($s,0,$i)); print("\n");
      }
      $n -= $lineLength;
   }
}

/* Main -- define alphabets, make 3 fragments */
function fasta($n = 1000) {
  $iub = array(
    array('a', 0.27),
    array('c', 0.12),
    array('g', 0.12),
    array('t', 0.27),

    array('B', 0.02),
    array('D', 0.02),
    array('H', 0.02),
    array('K', 0.02),
    array('M', 0.02),
    array('N', 0.02),
    array('R', 0.02),
    array('S', 0.02),
    array('V', 0.02),
    array('W', 0.02),
    array('Y', 0.02)
  );

  $homosapiens = array(
    array('a', 0.3029549426680),
    array('c', 0.1979883004921),
    array('g', 0.1975473066391),
    array('t', 0.3015094502008)
  );

  $alu =
    'GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG' .
    'GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA' .
    'CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT' .
    'ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA' .
    'GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG' .
    'AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC' .
    'AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA';

  makeCumulative($iub);
  makeCumulative($homosapiens);

  makeRepeatFasta('ONE', 'Homo sapiens alu', $alu, $n*2);
  makeRandomFasta('TWO', 'IUB ambiguity codes', $iub, $n*3);
  makeRandomFasta('THREE', 'Homo sapiens frequency', $homosapiens, $n*5);
}


/*function k_nucleotide() {
  global $in_fp;
  $input_file = "k-nucleotide-input50000.txt";
  $in_fp = fopen($input_file, "r");
  $sequence = read_sequence($in_fp, 'THREE');

  fclose($in_fp);

  // sequence read, let's write some stats
  write_freq($sequence, 1);
  write_freq($sequence, 2);
  write_count($sequence, 'GGT');
  write_count($sequence, 'GGTA');
  write_count($sequence, 'GGTATT');
  write_count($sequence, 'GGTATTTTAATT');
  write_count($sequence, 'GGTATTTTAATTTATAGT');
  }*/

/* functions definitions follow */
/*
function read_sequence($in_fp, $id) {
  $ln_id = strlen($id);
  // reach sequence three
  while(!feof($in_fp)) {
    $line = fgets($in_fp, 255);
    if($line[0] == '>' && substr($line, 1, $ln_id) == $id) {
      break;
    }
  }
  if(feof($in_fp)) {
    // sequence not found
    exit(-1);
  }
  // next, read the content of the sequence
  $sequence = '';
  while(!feof($in_fp)) {
    $line = fgets($in_fp, 100);
    switch($line[0]) {
    case ';':
      // comment, continue
      continue;
    case '>':
      // next sequence starts, this one is finished
      break 2;
    default:
      // append the uppercase sequence fragment,
      // must get rid of the CR/LF or whatever if present
      $sequence .= strtoupper(rtrim($line));
    }
  }
  return $sequence;
}
*/
function write_freq(&$sequence, $key_length) {
    var_dump($key_length);
  $map = generate_frequencies($sequence, $key_length);
  sort_by_freq_and_name($map);
  foreach($map as $key => $val) {
    printf ("%s %.3f\n", $key, $val);
  }
  echo "\n";
}

function write_count(&$sequence, $key) {
  $map = generate_frequencies($sequence, strlen($key), false);
  printf ("%d\t%s\n", (array_key_exists($key, $map))?$map[$key]:0, $key);
}

/**
 * Returns a map (key, count or freq(default))
 */
/*
function generate_frequencies(&$sequence, $key_length, $compute_freq = true) {
  $result = array();
  $total = strlen($sequence) - $key_length + 1;
  $i = $total;
  while(--$i >= 0) {
    // highly inefficient, alas, no real choice
    $key = substr($sequence, $i, $key_length);
    if(!array_key_exists($key,$result)) $result[$key] = 0;
    $result[$key]++;
  }
  if($compute_freq) {
    array_walk($result, 'compute_freq', $total);
  }
  return $result;
  }*/

function compute_freq(&$count_freq, $key, $total) {
  $count_freq = ($count_freq* 100) / $total;
}

function sort_by_freq_and_name(&$map) {
  // since PHP 4.1.0, sorting is not stable => dirty kludge
  array_walk($map, 'append_key');
  uasort($map, 'freq_name_comparator');
  array_walk($map, 'remove_key');
}

function append_key(&$val, $key) {
  $val = array($val, $key);
}

function freq_name_comparator($val1, $val2) {
  $delta = $val2[0] - $val1[0];
  // the comparator must return something close to an int
  $result = ($delta == 0)?strcmp($val1[1],$val2[1]):
    ($delta < 0)?-1:1;
  return $result;
}

function remove_key(&$val, $key) {
  $val = $val[0];
}

function mandelbrot($h = 400) {
  $w = 0;
  $bit_num = 0;
  $byte_acc = 0;
  $i = 0; $iter = 50;
  $x = 0; $y = 0; $limit2 = 4;
  $Zr = 0; $Zi = 0; $Cr = 0; $Ci = 0; $Tr = 0; $Ti = 0;

  $w = $h;

  printf ("P4\n%d %d\n", $w, $h);

  for ($y = 0 ; $y < $h ; ++$y)
  {
  	for ($x = 0 ; $x < $w ; ++$x)
  	{
  		$Zr = 0; $Zi = 0; $Tr = 0; $Ti = 0.0;

  		$Cr = (2.0 * $x / $w - 1.5); $Ci = (2.0 * $y / $h - 1.0);

  		for ($i = 0 ; $i < $iter and ($Tr + $Ti <= $limit2) ; ++$i)
  		{
  			$Zi = 2.0 * $Zr * $Zi + $Ci;
  			$Zr = $Tr - $Ti + $Cr;
  			$Tr = $Zr * $Zr;
  			$Ti = $Zi * $Zi;
  		}

  		$byte_acc = $byte_acc << 1;
  		if ($Tr + $Ti <= $limit2) $byte_acc = $byte_acc | 1;

  		++$bit_num;

  		if ($bit_num == 8)
  		{
  			echo chr ($byte_acc);
  			$byte_acc = 0;
  			$bit_num = 0;
  		}
  		else if ($x == $w - 1)
  		{
  			$byte_acc = $byte_acc << (8 - $w % 8);
  			echo chr ($byte_acc);
  			$byte_acc = 0;
  			$bit_num = 0;
  		}
  	}
  }
}


function regex_dna() {

  $variants = array(
      'agggtaaa|tttaccct',
      '[cgt]gggtaaa|tttaccc[acg]',
      'a[act]ggtaaa|tttacc[agt]t',
      'ag[act]gtaaa|tttac[agt]ct',
      'agg[act]taaa|ttta[agt]cct',
      'aggg[acg]aaa|ttt[cgt]ccct',
      'agggt[cgt]aa|tt[acg]accct',
      'agggta[cgt]a|t[acg]taccct',
      'agggtaa[cgt]|[acg]ttaccct',
  );

  # IUB replacement parallel arrays
  $IUB = array(); $IUBnew = array();
  $IUB[]='/B/';     $IUBnew[]='(c|g|t)';
  $IUB[]='/D/';     $IUBnew[]='(a|g|t)';
  $IUB[]='/H/';     $IUBnew[]='(a|c|t)';
  $IUB[]='/K/';     $IUBnew[]='(g|t)';
  $IUB[]='/M/';     $IUBnew[]='(a|c)';
  $IUB[]='/N/';     $IUBnew[]='(a|c|g|t)';
  $IUB[]='/R/';     $IUBnew[]='(a|g)';
  $IUB[]='/S/';     $IUBnew[]='(c|g)';
  $IUB[]='/V/';     $IUBnew[]='(a|c|g)';
  $IUB[]='/W/';     $IUBnew[]='(a|t)';
  $IUB[]='/Y/';     $IUBnew[]='(c|t)';

  # sequence descriptions start with > and comments start with ;
  #my $stuffToRemove = '^[>;].*$|[\r\n]';
  $stuffToRemove = '^>.*$|\n'; # no comments, *nix-format test file...

  # read in file
  #$contents = file_get_contents('php://stdin');
  $input_file = "regex-dna-input500000.txt";
  $contents = file_get_contents($input_file);
  $initialLength = strlen($contents);

  # remove things
  $contents = preg_replace("/$stuffToRemove/m", '', $contents);
  $codeLength = strlen($contents);

  # do regexp counts
  foreach ($variants as $regex){
      print $regex . ' ' . preg_match_all("/$regex/i", $contents, $discard). "\n";
  }

  # do replacements
  $contents = preg_replace($IUB, $IUBnew, $contents);

  print "\n" .
        $initialLength . "\n" .
        $codeLength . "\n" .
        strlen($contents) . "\n" ;
}

//# print the sequence out, if it exists
/*function print_seq(){
    global $seq; # no time-consuming argument passing for us! :)
    if($seq != ''){
        echo wordwrap( strrev( strtr(strtoupper($seq), SRC, DST) ),
                       LINE_LENGTH, "\n", true ), "\n";
    }
    $seq = '';
    }*/
/*
function reverse_complement() {
  # We'll need some definitions
  define( 'LINE_LENGTH', 60 );
  define( 'SRC', 'CGATMKRYVBHD');
  define( 'DST', 'GCTAKMYRBVDH');
  $str = '';
  $seq = '';

  $input_file = "reverse-complement-input50000.txt";
  $in_fp = fopen($input_file, "r");

  # read in the file, a line at a time
  while( !feof($in_fp) ) {
      $str = trim(fgets($in_fp));
      if( $str[0] == '>' ){
          # if we're on a comment line, print the previous seq and move on
          print_seq();
          echo $str, "\n";
      }else{
          # otherwise, just append to the sequence
          $seq .= $str;
      }
  }
  print_seq();
  }*/

function A($i, $j){
   return 1.0/(($i+$j)*($i+$j+1)/2+$i+1);
}

function Av($n,$v){
   $Av = array();
   for ($i=0; $i<$n; $i++){
      $Av[$i] = 0;
      for ($j=0; $j<$n; $j++) $Av[$i] += A($i,$j)*$v[$j];
   }
   return $Av;
}

function Atv($n,$v){
   $Atv = array();
   for ($i=0; $i<$n; $i++){
      $Atv[$i] = 0;
      for ($j=0; $j<$n; $j++) $Atv[$i] += A($j,$i)*$v[$j];
   }
   return $Atv;
}

function AtAv($n,$v){
   return Atv($n, Av($n,$v));
}

function spectral_norm($n = 200) {
  $u = array_pad(array(), $n, 1);

  for ($i=0; $i<10; $i++){
     $v = AtAv($n,$u);
     $u = AtAv($n,$v);
  }

  $vBv = 0;
  $vv = 0;
  for ($i=0; $i<$n; $i++){
     $vBv += $u[$i]*$v[$i];
     $vv += $v[$i]*$v[$i];
  }
  printf("%0.9f\n", sqrt($vBv/$vv));
}

///////////////////////////////////////////////////////////////////////////////
// harness

define ('IM', 139968);
define ('IA', 3877);
define ('IC', 29573);
$LAST = 42;
function gen_random($n) {
  global $LAST;
  return( ($n * ($LAST = ($LAST * IA + IC) % IM)) / IM );
}

function getmicrotime() {
  $rusage = getrusage();
  $t = ($rusage['ru_utime.tv_sec']*1000*1000 +
        $rusage['ru_utime.tv_usec'] +
        $rusage['ru_stime.tv_sec']*1000*1000 +
        $rusage['ru_stime.tv_usec']);
  return $t / 1000000;
}

function start_test() {
  //if (!getenv('VERIFY')) {
  //  ob_start();
  //}
  return getmicrotime();
}

function end_test($start, $name) {
  global $total;
  $end = getmicrotime();
  //if (!getenv('VERIFY')) {
  //  ob_end_clean();
  //}
  $total += $end-$start;
  $num = $end - $start;//number_format($end-$start,3);
  $pad = str_repeat(" ", 24-strlen($name)-strlen($num));
  //if (!getenv('VERIFY')) {
  //  echo "$name$pad$num\n";
  //  ob_start();
  //}
  return getmicrotime();
}

function total() {
  global $total;
  $pad = str_repeat("-", 24);
  echo $pad."\n";
  $num = $total;//number_format($total,3);
  $pad = str_repeat(" ", 24-strlen("Total")-strlen($num));
  echo "Total".$pad.$num."\n";
}

///////////////////////////////////////////////////////////////////////////////
// main
function main() {
  $tests = array(
                 "simple",
                 "simplecall",
                 "simpleucall",
                 "simpleudcall",
                 "mandel",
                 //"mandel2",
                 "ackermann",
                 "ary",
                 "ary2",
                 "ary3",
                 "fibo",
                 //"hash1",
                 "hash2",
                 "heapsort",
                 //"matrix",
                 "nestedloop",
                 "sieve",
                 "strcat",
                 "binary_trees",
                 "fannkuch",
                 "fasta",
                 // "k_nucleotide",
                 "mandelbrot",
                 "meteor_contest",
                 "n_body",
                 // "regex_dna",
                 // "reverse_complement",
                 "spectral_norm",
                );

  $t0 = $t = start_test();
  foreach ($tests as $test) {
    //    if (!isset($argv[1]) || $argv[1] === $test) {
    $test();
    $t = end_test($t, $test);
    //}
  }

  //if (!getenv('VERIFY')) {
  total();
    //}
}

main();

?>
