--TEST--
SPL: SplFileObject realpath and include_path
--FILE--
<?php

set_include_path('ext');

chdir(dirname(dirname(__FILE__))); // ext/spl


$fo = new SplFileObject('spl'.DIRECTORY_SEPARATOR.'fileobject_004.phpt', 'r', true);

var_dump($fo->getPath());
var_dump($fo->getFilename());
var_dump($fo->getRealPath());
?>
==DONE==
--EXPECTF--
string(%d) "spl"
string(19) "fileobject_004.phpt"
string(%d) "%sext/spl/fileobject_004.phpt"
==DONE==
