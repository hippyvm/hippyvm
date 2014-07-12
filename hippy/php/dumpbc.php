<?php
apc_compile_file($argv[1]);
echo apc_bin_dumpfile(array($argv[1]), null, $argv[2]);
?>

