<?
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
        for($i=0; $i<$n; $i++) {
          $perm[$i] = $perm1[$i];
        }
        $flipsCount = 0;

         while ( !(($k=$perm[0]) == 0) ) {
            $k2 = ($k+1) >> 1;
            for($i=0; $i<$k2; $i++) {
               $temp = $perm[$i];
               $perm[$i] = $perm[$k-$i];
               $perm[$k-$i] = $temp;
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

function fannkuch($n) {
  printf("Pfannkuchen(%d) = %d\n", $n, Fannkuch_run($n));
}

$all = array();
for ($i = 0; $i < 3; $i++) {
  $start = microtime(true);
  fannkuch(10);
  $all[] = microtime(true) - $start;
}
foreach ($all as $t) {
  echo $t, "\n";
}

?>