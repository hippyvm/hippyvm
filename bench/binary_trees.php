<?php
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

function binary_trees($n) {
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

$all = array();
for ($i = 0; $i < 10; $i++) {
  $start = microtime(true);
  binary_trees(13);
  $all[] = microtime(true) - $start;
}
foreach ($all as $t) {
  echo $t, "\n";
}
?>