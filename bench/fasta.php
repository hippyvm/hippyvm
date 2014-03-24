<?

define ('IM', 139968);
define ('IA', 3877);
define ('IC', 29573);
$LAST = 42;
function gen_random($n) {
  global $LAST;
  return( ($n * ($LAST = ($LAST * IA + IC) % IM)) / IM );
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
      if ($todo < LINE_LENGTH)
        $m = $todo;
      else
        $m = LINE_LENGTH;
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
function fasta($n) {
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

$all = array();
for ($i = 0; $i < 10; $i++) {
  $start = microtime(true);
  fasta(100000);
  $all[] = microtime(true) - $start;
}
foreach ($all as $t) {
  echo $t, "\n";
}
?>
