--TEST--
parse_ini_string() extended tests
--FILE--
<?php

var_dump(parse_ini_string("a = NORMAL"));
var_dump(parse_ini_string("a = 3 & 5", true, true));
var_dump(parse_ini_string(" a = b\n  b=c", true));
var_dump(parse_ini_string(" [a]", true));

echo "Done\n";
?>
--EXPECTF--	
array(1) {
  [%u|b%"a"]=>
  string(6) "NORMAL"
}
array(1) {
  [%u|b%"a"]=>
  string(5) "3 & 5"
}
array(2) {
  [%u|b%"a"]=>
  string(1) "b"
  [%u|b%"b"]=>
  string(1) "c"
}
array(1) {
  [%u|b%"a"]=>
  array(0) {
  }
}
Done
